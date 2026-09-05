# ENRK on Kaspa L1 — Reduced Design Specification

**Date:** September 3, 2026
**Status:** Specification for comparison. No implementation implied.
**Purpose:** Make the L1-native path concrete enough to compare with the Igra EVM
path on mechanisms rather than impressions.

---

## 0. Why this document exists

An earlier assessment concluded Kaspa L1 was closed to ENRK because covenants
cannot read a UTXO without spending it, and therefore could not read a shared
price oracle.

**That conclusion was too broad.** The protocol does not need to read without
spending. It can spend an oracle UTXO published for exactly that purpose, in the
same transaction as the operation that needs the price. KIP-10 introspection reads
other inputs by index, and KIP-20 covenant IDs authenticate their lineage.

Both KIPs shipped with the Toccata hardfork in June 2026.

The L1 path is therefore open, but **reduced**: two mechanisms from the Igra design
do not survive the move, and one sub-problem is genuinely unsolved.

---

## 1. The single decisive advantage

**Collateral never leaves Kaspa L1. There is no bridge and no custodian.**

On Igra, every unit of collateral sits in a custodial vault behind 3-of-5 keys
operated by one organisation, with unnamed signers, no bonding, and — on the KAS
route as documented — private-key reconstruction on each exit. Worst case: total
loss of all collateral.

On L1, the worst case for the equivalent trusted component (the price oracle) is
mispriced liquidations. Bad, bounded, and recoverable.

This is not a difference of degree. It is a difference of category, and it is the
reason this path deserves serious evaluation despite everything in §6.

---

## 2. The oracle — construction and its unsolved tension

### 2.1 Available primitives (both shipped)

From **KIP-10** (introspection, reads any input by index):

```
OpTxInputAmount (0xbe)   amount of input N
OpTxInputSpk    (0xbf)   script public key of input N
OpTxInputCount  (0xb3)   number of inputs
OpTxInputIndex  (0xb9)   index of the input currently being validated
```

From **KIP-20** (covenant lineage):

```
OpInputCovenantId        32-byte covenant_id of input N, or ZERO_HASH
OpAuthOutputCount        number of outputs authorised by a covenant input
OpAuthOutputIdx          index of the k-th authorised output
```

KIP-20 explicitly supports one-to-many: *"A common pattern is a single covenant
input authorizing one or many covenant outputs in the spending transaction."*

### 2.2 The base construction

```
Oracle genesis:  the oracle creates one covenant UTXO.
                 Its covenant_id is frozen into every vault script.

Price round:     the oracle spends it in a one-to-many split, producing N child
                 UTXOs, all carrying the same covenant_id, each encoding the
                 current price in its amount (price x fixed scaling factor).

Consumption:     a liquidator builds a transaction:
                   input 0 = the vault being liquidated
                   input 1 = one oracle price UTXO

                 The vault covenant asserts:
                   OpInputCovenantId(1) == ORACLE_COVENANT_ID   (authenticity)
                   price := OpTxInputAmount(1)                  (the value)

Contention:      each liquidator consumes a different one of the N children.
```

Authenticity comes from lineage, not from a signature check — which matters,
because Kaspa script has no opcode to verify a signature over an arbitrary
message. Only `OP_CHECKSIG` over the transaction exists. Covenant IDs sidestep that
limitation entirely.

The consumed sompi flow to the spender, so the oracle's working capital recirculates
rather than being locked.

### 2.3 The three-way tension, and how it resolves

Three requirements pull against each other:

| Requirement | What it wants |
|---|---|
| **No contention** | Many UTXOs live at once |
| **Freshness** | Stale prices must be unusable |
| **DoS resistance** | Consuming a UTXO must not deplete the feed |

The resolution is a two-branch covenant plus an atomic round transition.

```
Oracle UTXO for round R — two branches:

  USE BRANCH (anyone)
    spendable if:
      (a) the transaction also spends a UTXO of the VAULT covenant lineage
          -> checked with OpInputCovenantId over the other inputs
      (b) an output is created carrying the same covenant_id AND the same amount
          -> checked with OpAuthOutputCount / OpAuthOutputIdx

  SWEEP BRANCH (oracle signature, OP_CHECKSIG)
    spendable freely -> lets the oracle republish at a new price
```

**Contention** — N UTXOs live simultaneously; each consumer takes a different one.

**DoS resistance** — the USE branch forces identical replication, so a spender
must recreate what they consume. The feed cannot be drained. Condition (a)
additionally forces the attacker to touch a real vault, so the feed cannot be
spammed for free either.

**Freshness** — sweep and republish happen in a **single transaction**: round R's
UTXOs are consumed and round R+1's are created atomically. There is no instant at
which both rounds exist, so there is no stale-price window at all.

### 2.4 Why the atomic round transition is free — KIP-9

The obvious objection is cost: a transaction consuming N UTXOs and creating N more
looks expensive. Under Kaspa's storage mass rules it is not.

KIP-9 states directly: *"Compounding several outputs into an equal or smaller
number of outputs of equal value will never incur storage mass. This is true
regardless of the magnitude."*

The storage mass formula is:

```
storage_mass = C · ( Σ(1/o) − |I|²/Σ(v) )⁺        C = 10¹²
```

For N inputs of value `a` and N outputs of value `b`, this reduces to:

```
storage_mass = C · N · (1/b − 1/a)⁺
```

Which gives an asymmetry that shapes the design:

- **a rising price is free** — `b > a` makes the term negative, clamped to zero
- **a falling price costs mass**, proportional to N and to the depth of the fall

The constraint is therefore `N · (1/k − 1) ≤ limit`, where `k` is the per-round
price ratio. Bounding per-round movement tightly buys a large N. This pushes the
design toward **frequent rounds of small amplitude**, which is what a good oracle
should do anyway.

Exact numbers are deliberately omitted: KIP-9 expresses the constant in "dworks"
while the mempool limit (100,000) and block limit (500,000) are in "grams", and
that conversion has not been verified. The structural results are certain; a
specific maximum N is not.

### 2.5 What is still unverified

These are sizing questions, not feasibility questions:

1. **Compute mass.** KIP-9 does not bound input count; *compute* mass does. Every
   input executes a covenant script, so this is the real ceiling on N. Not yet
   established.
2. **Script size limits.** The USE branch must scan inputs for the vault lineage —
   a loop plus comparisons. SilverScript advertises loops and arrays, but its
   script size limits are not established.
3. **Block inclusion.** A several-hundred-input sweep competes for block space. If
   it is delayed, the oracle round is delayed with it.

---

## 3. The vault as a covenant

The natural fit, and cleaner than its EVM equivalent.

```
A vault is a UTXO holding KAS, with a covenant permitting:

  Branch OWNER      spend if signed by the owner AND the continuation output
                    satisfies ICR >= ICR_MINIMUM at the co-spent oracle price

  Branch LIQUIDATE  spend by anyone if ICR < MCR_TRIGGER at the co-spent oracle
                    price, and the outputs satisfy the auction distribution rules
```

Both branches read the price from a co-spent oracle UTXO per §2. `OpTxOutputAmount`
and `OpTxOutputSpk` let the script validate its own continuation outputs, which is
what enforces that a withdrawal cannot leave the vault under-collateralised.

Covenants++ documentation lists vault security as a target use case. Each vault is
an independent UTXO, so vault operations never contend with one another — a
structural advantage over the EVM version, where every vault touches shared
contract storage.

---

## 4. Liquidation

Each auction is local to one vault, which fits the model well.

The Dutch descent is a function of elapsed time. `OpCheckLockTimeVerify` lets the
covenant bound the price against the transaction's lock time, so the
100% → 75% descent over 120 minutes is expressible without any shared state.

The reflexive risk identified in the crash stress test is unchanged: liquidation
throughput remains the binding constraint, and the oracle DoS vector in §2.3 would
attack exactly that mechanism. **On L1 the freeze risk is higher, not lower**, until
§2.3 is resolved.

---

## 5. The kFIAT cap, by conservation instead of by counter

The supply-level cap built in Phase 3 reads a global counter. That is not
expressible on L1. The UTXO idiom replaces it with a conservation law:

```
Minting ENRK emits a proportional quota token as a covenant output.
Minting kFIAT requires consuming quota.

  100 * (kfiat_minted) <= CAP_PERCENT * (enrk_minted + kfiat_minted)

enforced locally at each mint by the quota available in the transaction,
rather than globally by reading total supply.
```

The invariant holds by construction and never needs a global read. This is
strictly more robust than the counter version: it cannot be defeated by spreading
debt across vaults, because quota cannot be conjured.

The mint-time-ceiling caveat documented in `kaspa_tokens.rs` still applies — burning
ENRK still shrinks the denominator, and the cap remains a ceiling at issuance
rather than a permanent guarantee.

---

## 6. What does not survive the move

### 6.1 Recovery Mode — blocked, and it costs nothing

Liquity's Recovery Mode raises collateral requirements automatically when the
**system-wide** collateral ratio falls below a threshold. That requires reading
aggregate state across all vaults. There is no L1 mechanism for it.

**An earlier version of this document called that a genuine loss. It was wrong,
and `recovery_mode_analysis.py` disproves it.**

Modelled over 120 Monte Carlo paths at a −85% crash, Recovery Mode triggered on
47 of 60 days and improved the p95 latent hole by **zero points** — 46% with it,
46% without.

The reason: Recovery Mode accelerates *eligibility* for liquidation, while the
failure is in *execution*. Nothing clears because the auction cannot descend far
enough to meet what liquidators demand. Adding vaults to a queue that is not
moving changes nothing. In Liquity it works because a Stability Pool absorbs
liquidations without needing an auction bidder — the two mechanisms are a pair,
and ENRK's pool cannot buy (§6.2).

**The fix that does work is a static parameter**, available identically on both
layers: moving the Dutch auction floor from 85% to 75% takes the p95 latent hole
from 46% to zero, for +2.4% additional discount in calm markets. Floors of 75%,
70% and 60% give identical results, because a Dutch auction clears at the first
acceptable price — once the floor covers maximum liquidator demand, going deeper
costs nothing and adds nothing.

Raising the MCR, by contrast, buys almost no protection (46% → 44% at MCR 200%)
while costing +5.2% in calm markets. It is the wrong lever.

So the L1 path loses Recovery Mode and loses nothing by it. See
`Recovery-Mode-Analysis` for the full result set.

### 6.2 Stability Pool — uncertain, previously judged too harshly

An earlier note recorded this as impossible. KIP-20 documents a many-to-many
delegation pattern: *"Designate a single 'leader' input responsible for validating
the full N-to-N transition. Other covenant inputs act as 'delegators', validating
only that the leader is correctly selected."*

A pool held as a set of covenant UTXOs under one lineage, with leader-validated
transitions, is not excluded. It is a different programming model, not an
impossibility.

Note this matters less than it appears: the Phase 3 review established that the
Stability Pool **as currently written cannot buy anything** — it only burns ENRK it
already holds, and its ammunition is denominated in the asset it defends. Dropping
it removes a mechanism already shown to be decorative.

---

## 7. Side by side

| | Igra EVM | Kaspa L1 reduced |
|---|---|---|
| Language / model | Solidity, account model | SilverScript, UTXO covenants |
| Prior art | Liquity, battle-tested since 2021 | **None. First of its kind.** |
| Collateral custody | 3-of-5 keys, one org, unnamed signers | **None — never leaves L1** |
| Worst-case failure | Total loss of collateral | Mispriced liquidations |
| Size ceiling | ~6–18M KAS (bridge throughput) | **None** |
| Exit latency | 2–5 min (KAT) to 48–72h (Guardians) | **None — no exit needed** |
| Layer governance | DAO-governed rollup | PoW consensus, hardfork only |
| Price oracle | Mature EVM patterns | **§2.3 unsolved** |
| Recovery Mode | Available (Liquity) | **Blocked** |
| Stability Pool | Available (but shown defective) | Uncertain, via delegation |
| Vault contention | Shared contract storage | **None — independent UTXOs** |
| Audit market | Large, affordable, Solidity | Tiny. Almost nobody audits SilverScript |
| Doctrinal fit | Immutable contract on mutable ground | **Exact** |

---

## 8. Open problems, ranked

The gating problem — oracle freshness — is **resolved** (§2.3, §2.4). What remains:

1. **Audit capacity.** Who can credibly audit a SilverScript covenant system for
   immutable deployment? The language is three months old. This is very likely the
   real blocker, regardless of every technical answer above.
2. **No prior art.** Nobody has shipped a CDP stablecoin on these primitives.
   First-of-its-kind plus never-patchable is the combination that should worry us
   most.
3. **Compute mass ceiling on N** (§2.5). Sizing, not feasibility.
4. **Stability Pool via delegation.** Worth a design attempt, but low priority
   given §6.2.

~~Recovery Mode substitute~~ — **resolved.** The auction floor at 75% is the fix,
it is a static constant, and it works identically on both layers (§6.1).

---

## 9. Where the comparison now stands

The L1 path no longer has a hole in it. Every mechanism it needs rests on a
documented, shipped opcode, and the property that makes the oracle work is quoted
verbatim from KIP-9.

That moves the decision onto its real axis. It is no longer "does L1 work" but:

> Is the absence of a custodian worth deploying unpatchable code on
> three-month-old primitives that almost nobody can audit?

Igra offers proven ground, a large audit market, and Liquity's lineage — at the
price of a 3-of-5 custodian holding all collateral, a hard size ceiling, and an
immutable contract standing on DAO-governed ground.

L1 offers exact doctrinal fit, no custodian and no size ceiling — at the price of
being first, with almost no auditors who have covenant experience.

Note what is *no longer* on that list: Recovery Mode. Its absence was the last
technical argument against L1, and §6.1 disproves it.

Both are defensible. Neither is obvious. The choice is a judgement about which
risk is more survivable, and that judgement belongs to the project owner.

---

## Sources

- [KIP-10 — transaction introspection opcodes](https://github.com/kaspanet/kips/blob/master/kip-0010.md)
- [KIP-17 — covenants](https://github.com/kaspanet/kips/blob/master/kip-0017.md)
- [KIP-20 — covenant IDs, split and delegation patterns](https://github.com/kaspanet/kips/blob/master/kip-0020.md)
- [KIP-16 — ZK opcodes and verifier precompile](https://github.com/kaspanet/kips/blob/master/kip-0016.md)
- [Hail the SilverScript — Kas Magazine](https://kasmagazine.com/article/hail-the-silverscript)
- Internal: `docs/design/EXECUTION_TARGET_ASSESSMENT.md`, `tests/backtesting/stress_test_crash.py`
