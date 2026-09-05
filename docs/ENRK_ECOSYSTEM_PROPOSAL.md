# ENRK — An Energy-Backed Stablecoin on Kaspa L1 Covenants

**A proposal to the Kaspa Ecosystem Foundation and Kaspa core developers**

**Date:** September 2026
**Repository:** https://github.com/cyprox/ENRK_stablecoin
**Status:** Design and specification complete. Pre-implementation. Seeking
technical validation and audit partnership.

---

## Summary

ENRK is an over-collateralised stablecoin whose unit of account is **one kilowatt
hour of thermodynamic value**, not a fiat currency. It is designed to be
**immutable after deployment**: no DAO, no admin keys, no upgrade path. Evolution
happens by fork, chosen by users.

We believe it can be built **natively on Kaspa L1**, using the covenant primitives
that shipped with Toccata in June 2026, with **no bridge and no custodian**.

This document sets out the construction, the evidence behind it, the things we
found wrong with our own design, and what we are asking for.

We are not asking for money first. We are asking a technical question first
(§7.1). If the answer is no, this proposal is void and we would rather know now.

---

## 1. What the protocol is

| | |
|---|---|
| **Unit of account** | 1 ENRK = 1 kWh of thermodynamic value. No USD, no fiat. |
| **Peg index** | 40% Kaspa hashrate, 30% global energy price, 20% Kaspa fees, 10% crypto adoption. Frozen weights. |
| **Collateral** | KAS, over-collateralised. |
| **Structure** | Dual tranche — ENRK (senior, redeemable) and kFIAT (junior, loss-absorbing, capped at 30% of debt at issuance). |
| **Liquidation** | Dutch auction, permissionless. |
| **Governance** | **None.** Every parameter frozen at compile time. |

The thermodynamic thesis is what makes Kaspa the right chain rather than an
arbitrary one: KAS has a production cost anchored in proof-of-work electricity
consumption. If price falls below that cost, miners power down, hashrate falls,
difficulty adjusts, and cost realigns with price. The collateral and the unit of
account are causally linked through the consensus mechanism itself. That link does
not exist on a proof-of-stake chain, and it is why this design belongs here.

---

## 2. Why Kaspa L1, and the alternative we rejected

We evaluated Igra EVM seriously and were prepared to deploy there. Solidity,
Liquity's battle-tested lineage, a large audit market, MEV resistance inherited
from based-rollup sequencing. On engineering grounds it is the safer path.

We rejected it for two reasons we could not get past.

**The collateral would sit with a custodian.** Both documented KAS bridges are
operator-controlled. The official route is a manual multisig with a 48–72 hour
release and no SLA. KAT Bridge is materially better operationally — 2–5 minutes,
published contracts, four audits, continuous public reserve reconciliation — but
it is a 3-of-5 threshold whose five signers are operated by a single organisation
and are not publicly named, with no bonding or slashing. Its own documentation
states plainly that three colluding signers could drain the vault.

**Both KAS routes are capped at ~200,000 KAS per 24 hours.** For a protocol
holding on the order of 100M KAS of collateral, that is roughly 500 days to
unwind. The exit throughput sets a hard ceiling on the size of any stablecoin
that lives behind it.

An immutable protocol standing on a custodial bridge is immutable in the part that
matters least. On Kaspa L1 the collateral never moves, and the only trusted
component is a price oracle — which can misprice liquidations, but cannot take
anything.

That is not a difference of degree. It is a different category of risk, and it is
the whole reason for this proposal.

---

## 3. The technical core: a contention-free price oracle from covenants

This is the part we most want reviewed, because everything else depends on it.

### 3.1 The problem

A CDP protocol needs a price readable by many concurrent transactions. Kaspa L1 has
no reference inputs — KIP-10 states directly that there are no opcodes to read
unspent UTXOs without spending them — and no built-in oracle. We initially
concluded the L1 path was closed.

That conclusion was wrong. **The protocol does not need to read without spending.**
It can spend an oracle UTXO published for exactly that purpose, in the same
transaction as the operation needing the price.

### 3.2 The construction

Using only shipped opcodes:

```
From KIP-10:   OpTxInputAmount (0xbe)   amount of input N
               OpTxInputSpk    (0xbf)   script pubkey of input N

From KIP-20:   OpInputCovenantId        32-byte covenant_id of input N
               OpAuthOutputCount        authorised outputs of a covenant input
               OpAuthOutputIdx          index of the k-th authorised output
```

**Setup.** The oracle creates one genesis covenant UTXO. Its `covenant_id` is
frozen into every vault script.

**Each price round.** The oracle spends it in a one-to-many split, producing N
child UTXOs, all carrying the same `covenant_id`, each encoding the current price
in its amount. KIP-20 supports this directly: *"A common pattern is a single
covenant input authorizing one or many covenant outputs in the spending
transaction."*

**Consumption.** A liquidator builds a transaction with the vault as input 0 and
one oracle UTXO as input 1. The vault covenant asserts:

```
OpInputCovenantId(1) == ORACLE_COVENANT_ID     authenticity, by lineage
price := OpTxInputAmount(1)                     the value
```

Authenticity comes from covenant lineage rather than a signature check — which
matters, because Kaspa script has no opcode to verify a signature over an arbitrary
message. Covenant IDs sidestep that limitation entirely.

**The oracle UTXO has two branches:**

```
USE (anyone)     spendable if (a) the transaction also spends a UTXO of the
                 VAULT covenant lineage, and (b) an output is created carrying
                 the same covenant_id and the same amount

SWEEP (oracle)   OP_CHECKSIG against the oracle key; allows republication
                 at a new price
```

### 3.3 Why the three requirements resolve

| | |
|---|---|
| **No contention** | N UTXOs live simultaneously; each consumer takes a different one. |
| **DoS resistance** | The USE branch forces identical replication — a spender must recreate what they consume, so the feed cannot be drained. Condition (a) additionally forces the attacker to touch a real vault. |
| **Freshness** | Sweep and republish occur in a **single transaction**. Round R is consumed and round R+1 created atomically. There is no instant at which both exist, so there is no stale-price window. |

Stale prices are a theft vector, not an inconvenience — a liquidator who can pick
an old favourable price liquidates vaults that are healthy at the true price. The
atomic round transition removes the window entirely.

### 3.4 Why the atomic transition is free — KIP-9

The obvious objection is cost. Under Kaspa's storage mass rules there is none.
KIP-9 states: *"Compounding several outputs into an equal or smaller number of
outputs of equal value will never incur storage mass. This is true regardless of
the magnitude."*

For N inputs of value `a` and N outputs of value `b`, the storage mass formula
`C·(Σ(1/o) − |I|²/Σ(v))⁺` reduces to `C·N·(1/b − 1/a)⁺`, giving an asymmetry that
shapes the design:

- **a rising price is free** — the term goes negative and clamps to zero
- **a falling price costs mass**, proportional to N and to the depth of the fall

The constraint is `N·(1/k − 1) ≤ limit` for a per-round price ratio `k`. Bounding
per-round movement tightly buys a large N, which pushes the design toward frequent
rounds of small amplitude — what a good oracle should do anyway.

---

## 4. Evidence: what we found wrong with our own design

We built a Monte Carlo stress test of the whole protocol — not just the peg
formula — with vault populations, liquidation with realistic bidder scarcity, the
seniority waterfall, reflexive price impact from dumped collateral, gap risk, and
a liquidator capital constraint. It is in the repository and runs on the standard
library alone.

**The model was wrong three times before it was right**, and each fix reversed a
conclusion:

1. Failed auctions destroyed the collateral. Wrong — a failed auction destroys
   nothing; the vault stays open and is re-auctioned.
2. Linear market impact turned a −50% exogenous crash into −85% actual, flattening
   every comparison. Replaced with the square-root impact law.
3. Liquidator capital was unlimited, so the system always cleared. Added a daily
   capacity constraint — which is what actually broke on Black Thursday.

Before those fixes it reported "everything is fine" for entirely wrong reasons.

### What it then found

**The protocol freezes; it does not explode.** At −95%, kFIAT realised losses are
*lower* than at −85% — because liquidations stop happening at all. 591 of 1000
vaults stay open and underwater. Debt becomes latent: 30% of total debt at the
median, 57% at p95, uncovered, with tokens still circulating.

For an immutable protocol this is the critical property: **there is nobody to
unfreeze it.**

**Our Stability Pool does not work.** It burns ENRK it already holds rather than
bidding, and its ammunition is denominated in the asset it defends. It cannot
place a bid under a falling price.

**Recovery Mode would not have helped.** We modelled Liquity-style Recovery Mode as
the fix. It triggered on 47 of 60 days and improved the p95 latent hole by zero
points — because it accelerates *eligibility* while the failure is in *execution*.
In Liquity it works because a Stability Pool absorbs liquidations without needing
a bidder; the two are a pair.

**The fix is a static parameter.** Moving the Dutch auction floor from 85% to 75%
eliminates the freeze entirely — p95 latent hole from 46% to zero — for +2.4%
additional discount in calm markets. Floors of 75%, 70% and 60% give identical
results, because a Dutch auction clears at the first acceptable price: once the
floor is deep enough to cover maximum demand, going deeper costs nothing. The floor
is a safety valve, not a price.

**Our 30% kFIAT cap is a mint-time ceiling, not a permanent guarantee.** Burning
ENRK shrinks the denominator, so peg defence and the cap pull against each other.
We document it as such rather than claiming otherwise.

---

## 5. What we are not claiming

- No code is deployed. No audit has been performed.
- An earlier Rust implementation (~5,000 lines, 119 passing tests) targeted the
  wrong execution environment and does not deploy. It survives as an executable
  specification and a differential-testing oracle, nothing more.
- The oracle construction in §3 is derived from KIP text and has **not been
  validated by anyone who wrote those KIPs.** That is the first thing we want.
- Three sizing questions are unresolved: the compute-mass ceiling on input count,
  SilverScript script size limits, and block inclusion for a several-hundred-input
  sweep transaction (§7.1).
- Recovery Mode is unavailable on L1. Per §4 this costs essentially nothing, but it
  is a real difference from Liquity.
- Being first on these primitives is a risk, not a feature. Immutable code plus
  three-month-old primitives plus no auditors with covenant experience is a
  combination we take seriously.

---

## 6. What the ecosystem gets

**A flagship application for Toccata.** Covenants, covenant IDs, native assets and
SilverScript shipped in June. ENRK exercises KIP-10, KIP-17 and KIP-20 adversarially,
in production, with real value at stake.

**Free adversarial QA on the KIPs.** Everything we find, we publish — including
what we find against ourselves, as §4 shows.

**The first covenant audit methodology.** Nobody has audited a SilverScript covenant
system for immutable deployment. Whoever does it first produces the methodology,
the tooling and the catalogue of pitfalls that every subsequent Kaspa DeFi project
inherits. That is a public good the ecosystem does not currently have.

**A reference implementation.** Fully specified, stress-tested, open source, GPL-3.0,
with the failure analysis published alongside the design.

**Evidence that L1 covenants can carry real DeFi.** Kaskad chose Igra EVM. KRON is
on L1 but is an AMM, not a credit system. A working CDP stablecoin on covenants
would be the strongest available demonstration that Toccata's primitives are
sufficient for serious financial applications.

---

## 7. What we are asking for

### 7.1 First — a technical answer, not funding

Four questions. Any core developer can answer them, and they decide whether this
project proceeds:

1. **Is the §3 oracle construction sound?** Specifically: can a covenant reliably
   verify `OpInputCovenantId` on a sibling input, and does the one-to-many split
   preserve `covenant_id` across all authorised children as we read KIP-20 to say?
2. **What is the compute-mass ceiling on input count** when every input executes a
   covenant script? This sets the maximum N and we could not establish it.
3. **What are SilverScript's script size limits?** The USE branch must scan inputs
   for the vault lineage — a loop plus comparisons.
4. **Is a several-hundred-input sweep transaction reliably includable**, or will it
   be crowded out?

If the answer to (1) is no, this proposal ends and we deploy elsewhere or wait. We
would rather learn that from you now than from an auditor in six months.

### 7.2 Then — audit partnership

Two code audits and one economic audit, on Solidity-market pricing of roughly
40–100k USD per code audit before any covenant premium. We are seeking ecosystem
support for this, and we would structure it explicitly to avoid a conflict of
interest:

- independent mandate, with no editorial input from any funder
- **full publication of every report regardless of outcome**
- ideally a second review not funded from the same source

An economic audit matters more than a second code audit. The freeze we found in §4
is a design defect in perfectly correct code — no code auditor would have caught
it. That is how stablecoins die.

### 7.3 What we are not asking for

No token allocation, no listing support, no marketing, no privileged bridge access,
and no exceptions to any protocol limit.

---

## 8. Status

| | |
|---|---|
| Economic design | Complete |
| Peg formula, backtested | Complete |
| Full-protocol crash stress test | Complete, published |
| Covenant oracle construction | Specified, **unvalidated** |
| Execution target assessment | Complete |
| Implementation | Not started |
| Audit | Not started |

Everything referenced here is in the repository: the specifications, the stress
test and its results, the execution-target assessment with primary KIP citations,
and the record of the design decisions we reversed.

**https://github.com/cyprox/ENRK_stablecoin**

Licence: GPL-3.0.

**Author:** cyprox — sole developer. Contact via the repository.

Development is funded by a capped share of protocol fees, disclosed in the frozen
parameter specification: 20% of fees to a treasury address until a fixed cumulative
ceiling, then 0% forever, with the flow moving permanently to the protocol. The
ceiling is a compile-time constant, its counter is readable on-chain by anyone, and
no party can raise it. This is stated here rather than discovered later, because an
undisclosed founder revenue stream is how projects lose trust — not because taking
one is illegitimate.
