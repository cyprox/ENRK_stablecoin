# ENRK on Kaspa L1 — Reduced Design Specification

**Date:** September 3, 2026
**Status:** design specification of the layer decided by the owner on 2026-11-13 (Kaspa L1; Igra not retained). It is a design record, not an implementation. Open items are listed in section 8.
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

KIP-20 shipped with the Toccata hardfork (mainnet activation 2026-06-30); the KIP-10 introspection opcodes were active before it (KIP-17).

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
                 Its covenant_id is held in each vault's own state, fixed at
                 vault creation. It CANNOT be a compile-time constant --
                 measured, see 2.5 Q1c.

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

**A correction to an earlier claim here.** This section previously stated that the
consumed sompi flow to the spender, so the oracle's working capital recirculates.
That contradicts §2.3: the USE branch requires an output carrying the same
covenant_id **and the same amount**, so the spender must recreate what they consume.
The oracle's working capital is therefore **locked, not recirculated**, at
`N x amount_per_UTXO`.

This matters for the variant choice. In variant A the amount encodes the price, so
the locked capital is set by the price scaling factor and cannot be reduced
independently. In variant B the price is a state field, so the amount can sit at the
dust minimum and the locked capital is negligible. See §2.5.

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
spammed for free either (not implemented in either variant as of AUDIT I22).

**Freshness** — the intended design is a single transaction in which round R is consumed and round R+1 created, so no stale sibling remains. As written this does not hold (see the note below); stale-sibling risk is closed only by an all-N completeness guard, shown essential by a negative control on testnet-10 (ECONOMICS-VERIFICATION section 10.2).

> **This property does not hold for the construction as currently written.**
> Measured September 15, 2026: `sweep` in both variants emits exactly two outputs
> (`left`, `right`), and the generated Silverscript requires
> `OpAuthOutputCount(this.activeInputIndex) == 2`. The split is **binary**, so
> reaching N children from one parent takes ⌈log₂ N⌉ successive sweeps and
> therefore several transactions — which is the opposite of atomic. Batching N
> independent sweeps into one transaction is the obvious candidate and has the
> same shape as the validated USE ladder, but it has never been measured and the
> contract does not express it. **The form of the round transition is an open
> design decision.** See [`REMEASUREMENT-2026-09-15.md`](REMEASUREMENT-2026-09-15.md)
> §6.1.

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
while the block limits are compute 500,000, transient 1,000,000 and storage 500,000 (no separate 100,000 standard-mass cap exists after Toccata in rusty-kaspa v2.1.0), and
that conversion has not been verified. The structural results are certain; a
specific maximum N is not.

### 2.5 What was measured, and what remains

On September 6, 2026 the construction was implemented in Argent
(`argent-lang/argent` d08e52d) in two variants and executed through the real Kaspa
mainnet script engine via `argent-runtime` and `MassCalculator`. The sizing
questions below are no longer estimates.

**Re-measured September 15, 2026** on Argent `e76ee07` with the released
Silverscript v1.0.0. Every figure reproduces; the variant B column below has been
corrected for three transcription errors, and the ceilings are now the true
maxima rather than ladder rungs. Method, corrections and the defect found in the
published harness are in
[`REMEASUREMENT-2026-09-15.md`](REMEASUREMENT-2026-09-15.md).

**Variant A** encodes the price in the UTXO amount. **Variant B** carries it as a
typed state field. Both compiled on the first attempt.

| | Variant A | Variant B |
|---|---|---|
| Ceiling on N per round | **642** | **532** |
| Binding constraint | transient mass | transient mass |
| Compute mass per input | 759 | 839 |
| Transient mass per input | 1,556 | 1,876 |
| Signature script | 248 B | 328 B |
| Total script size | 1,046 B | 1,206 B |

1. **Compute mass — answered, and it is not the ceiling.** The binding constraint
   is *transient* mass, not compute mass. Toccata block limits: compute 500,000,
   transient 1,000,000, storage 500,000.
2. **Script size — answered, and it is a non-issue.** 1,046 B and 1,206 B against a
   1 MB limit, or 0.1%. Vault 805 B / 886 B, oracle 241 B / 320 B.
3. **Block inclusion — answered on testnet-10, not on mainnet.** (These ceilings are for N independent USE spends in one transaction. Republication at a changed price was executed on testnet-10 up to N = 46 for the contract form tested (ECONOMICS-VERIFICATION section 10.2). Inclusion of an N = 640 round, 97.5% of the compute limit, was executed on testnet-10 on a lightly loaded network; mainnet contention is untested.) A round at N=640 consumes 996,216 transient
   mass, or 99.6% of one block's budget. At Kaspa's 10 BPS that is ~100 ms per
   round, and ~10 ms at the planned 100 BPS, which is acceptable for real-time
   liquidation. But behaviour under contention, and post-Toccata fees, require
   Testnet-10. **The oracle monopolises one block per round, so the cadence model
   is N x block_time.**

### 2.5.1 Q1c — the constraint the measurement surfaced

A question nobody had asked was answered by the compiler refusing to build:
**`covenant_id` cannot be a compile-time constant.** `probe_const_covid.ag` is
rejected. Re-verified under Silverscript v1.0.0 on September 15, 2026, where the
compiler states the constraint itself:

```
argentc: entry `Probe::touch` observe `oracle` covenant id source must be
a `self.<field>` state field or entry argument of type `cov_id`
```

The consequence is structural, not cosmetic. §2.2 above previously assumed the
oracle's `covenant_id` could be frozen into every vault script at compile time,
which is what made authenticity free. It cannot. The vault must carry the oracle
identity in its own state, fixed at vault creation — and **what guarantees a vault
is created against the right oracle is not specified anywhere in this document.**

For immutable code this is a security question. It is open.

### 2.5.2 The KIP-9 asymmetry, quantified

§2.4 derived the asymmetry structurally. It has now been measured, and it separates
the two variants sharply.

| Price ratio per round | Variant A storage mass | Variant B |
|---|---|---|
| constant | 0 | 0 |
| k = 0.99 (−1%) | 101 units/unit | 0 |
| k = 0.90 (−10%) | 1,111 units/unit | 0 |
| k = 0.50 (−50%) | 10,000 units/unit | 0 |

At N=640 a −10% round costs variant A **711,040 storage units**, which exceeds the
500,000 per-block limit by 42%. Variant B incurs zero storage mass under any price
movement, because its amounts do not change when the price does. Caution (AUDIT I19, section 13.3b): this table describes a value-changing N-to-N round that no entry can produce; price changes happen only through the 1-to-2 sweep. The real storage cost is in genesis (about 4 x N x 10^12 / value) and in sweep. 'Zero at any price' for variant B is unproven.

**This is the crash scenario.** A falling price is exactly when the oracle must keep
publishing, and it is where variant A's capacity degrades. Whether that is
structural or merely an artefact of the amount scaling factor chosen for the
measurement has not been tested. **The A/B choice is open and is the next piece of
work.**

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

The gating problem (oracle freshness) is partly resolved: the construction is measured, but the atomic round transition does not hold as written (section 2.3 note); the form of the round transition is an open design decision. What remains:

1. **Audit capacity.** Who can credibly audit a SilverScript covenant system for
   immutable deployment? The language is three months old. This is very likely the
   real blocker, regardless of every technical answer above.
2. **No prior art.** Nobody has shipped a CDP stablecoin on these primitives.
   First-of-its-kind plus never-patchable is the combination that should worry us
   most.
3. **Q1c — the oracle identity binding** (§2.5.1), now reframed. The binding that
   must be secured is **asset → vault**, not vault → oracle: a forged vault harms
   only its creator unless it can mint real ENRK. A `MinterProxy` stores exactly
   one covenant id, so a permissionless population of independent vaults needs a
   common ancestor — which every mint would have to co-spend, reintroducing the
   contention the 1→N construction exists to avoid. Argent's `spawns … by …`
   supplies the lineage primitive; its own docs record the KCC20 bootstrap and
   launch proofs as unimplemented follow-ups. See
   [`ORACLE-BINDING.md`](ORACLE-BINDING.md).
4. **Variant A or B** (§2.5.2). Measurable, not yet measured.
5. **Block inclusion under contention** (§2.5). Executed on testnet-10 on a lightly loaded network (AUDIT section 13.3b); mainnet contention not tested.
6. **Stability Pool via delegation.** Worth a design attempt, but low priority
   given §6.2. **Constraint:** any delegation design must leave `PriceRound`
   non-leader. Argent `e76ee07` requires `|I(c)| = 1` — one input per covenant id
   per transaction — for a `consumes`-free ordinary entry on a leader actor. If
   the oracle ever declares a `delegate` entry, the 1→N construction dies.

7. **The form of the round transition** (§2.3). Binary sweep without atomicity,
   or N sweeps batched into one transaction. Gates the next measurement.

8. **The cost of the liquidation transaction.** Measured on testnet-10 (AUDIT section 13.3b; lightly loaded testnet). A vault input is
   815–912 B of signature script against 248–328 B for an oracle `use`. N = 642 is
   the ceiling on a pure oracle round, not on the path the protocol runs.

9. **Undefined behaviour.** `icr_percent` contains two reachable undefined
   behaviours — an unchecked divisor and an overflow above ~9.2 KAS of collateral
   — in both variants and both entries, accepted by the compiler without a
   diagnostic. See [`UNDEFINED-BEHAVIOUR-EXPOSURE.md`](UNDEFINED-BEHAVIOUR-EXPOSURE.md).

~~Compute mass ceiling on N~~ — **resolved.** 642 / 532, bounded by transient mass
(§2.5).
~~Script size limits~~ — **resolved.** 0.1% of the limit (§2.5).

~~Recovery Mode substitute~~ — **resolved.** The auction floor at 75% is the fix,
it is a static constant, and it works identically on both layers (§6.1).

---

## 9. Where the comparison now stands

The L1 path has no known hole in the primitives it relies on, but the round transition form, the asset to vault binding and the arithmetic discipline are open. Every mechanism it needs rests on a
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

**Outcome (2026-11-13): the owner chose Kaspa L1; Igra is not retained.** The Igra column of section 7 is kept as record.

---

## Sources

- [KIP-10 — transaction introspection opcodes](https://github.com/kaspanet/kips/blob/master/kip-0010.md)
- [KIP-17 — covenants](https://github.com/kaspanet/kips/blob/master/kip-0017.md)
- [KIP-20 — covenant IDs, split and delegation patterns](https://github.com/kaspanet/kips/blob/master/kip-0020.md)
- [KIP-16 — ZK opcodes and verifier precompile](https://github.com/kaspanet/kips/blob/master/kip-0016.md)
- [Hail the SilverScript — Kas Magazine](https://kasmagazine.com/article/hail-the-silverscript)
- Internal: `docs/design/EXECUTION_TARGET_ASSESSMENT.md`, `tests/backtesting/stress_test_crash.py`
