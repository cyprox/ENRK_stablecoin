# ENRK — Kaspa Energy Reserve Stablecoin

An over-collateralised stablecoin whose unit of account is **one kilowatt hour of
thermodynamic value**, not a fiat currency. Designed to be **immutable after
deployment**: no DAO, no admin keys, no upgrade path. Evolution happens by fork,
chosen by users.

---

## Status — read this before anything else

**Design and specification complete. Implementation not started.**

The execution layer is undecided and blocked on one external answer: whether the
covenant-based price oracle described in
[`docs/design/L1_NATIVE_REDUCED_SPEC.md`](docs/design/L1_NATIVE_REDUCED_SPEC.md)
is sound on Kaspa L1. That question is put to Kaspa core developers in §7.1 of the
ecosystem proposal.

No code is deployed. No audit has been performed. Nothing here should be read as
an invitation to use the protocol.

**Start here:** [**`PROJECT-STATE.md`**](PROJECT-STATE.md) — what is decided, what
is blocked, what happens next.

---

## What the protocol is

| | |
|---|---|
| **Unit of account** | 1 ENRK = 1 kWh of thermodynamic value. No USD, no fiat. |
| **Peg index** | 40% Kaspa hashrate, 30% global energy price, 20% Kaspa fees, 10% crypto adoption. Frozen weights, clipped to [0.1, 5.0]. |
| **Collateral** | KAS, over-collateralised. |
| **Structure** | Dual tranche — ENRK (senior, redeemable) and kFIAT (junior, loss-absorbing, capped at 30% of debt at issuance). |
| **Liquidation** | Dutch auction, permissionless. |
| **Governance** | **None.** Every parameter frozen at compile time. |

The thermodynamic thesis is what makes Kaspa the right chain rather than an
arbitrary one: KAS has a production cost anchored in proof-of-work electricity
consumption. If price falls below that cost, miners power down, hashrate falls,
difficulty adjusts, and cost realigns with price. Collateral and unit of account
are causally linked through the consensus mechanism itself.

---

## Frozen parameters

Every value below is fixed at compile time. Changing any of them requires a fork.
Full justification, with the evidence behind each figure, in
[`docs/design/FROZEN_PARAMETERS.md`](docs/design/FROZEN_PARAMETERS.md).

| Parameter | Value |
|---|---|
| Peg formula | 40 hashrate / 30 energy / 20 fees / 10 adoption |
| ICR minimum (at mint) | 200% |
| MCR (liquidation trigger) | 150% |
| kFIAT cap | 30% of total debt **at mint** |
| Auction | 120 minutes, 100% → **75%** |
| Liquidation fee | 4% |
| Mint fee | 2% |
| Redemption | Lowest-ICR-first, 100% floor, ENRK only, 1% fee |
| Fee denomination | **KAS**, taken from vault collateral |
| Treasury | 20% of fees until 2,500,000 peg units, then **0% forever** |
| Circuit breaker | 10% peg deviation, 6h oracle downtime, **no override** |

---

## What we found wrong with our own design

A Monte Carlo stress test of the whole protocol — vault populations, liquidation
with realistic bidder scarcity, the seniority waterfall, reflexive price impact,
and a liquidator capital constraint — produced four findings that changed the
design. They are published here rather than discovered later.

**The protocol freezes; it does not explode.** Past a 61% drawdown, no auction
fills at any point in its descent. Debt becomes latent — 57% of total debt at p95,
uncovered, with tokens still circulating. For an immutable protocol this is the
critical property: **there is nobody to unfreeze it.**

**The Stability Pool cannot buy.** `attempt_buyback` computes a cost, never debits
it, and reduces the pool's own ENRK balance. It is a burn, not a bid — and its
ammunition is denominated in the asset it defends. It must be fixed or removed;
this repository does not claim it works.

**Redemption was never implemented.** Equilibrium mechanism #1 exists only as
error variants and a fee constant. Modelling shows it halves losses under stress
and needs no liquidator capital, so it functions precisely when auctions cannot.
It must be built.

**The 30% kFIAT cap is a mint-time ceiling, not a permanent guarantee.** Burning
ENRK shrinks the denominator, so peg defence and the cap pull against each other.
Documented as such rather than claimed otherwise.

**The fix is a static parameter.** Moving the Dutch auction floor from 85% to 75%
eliminates the freeze — p95 latent hole from 46% to zero — for +2.4% additional
discount in calm markets. The floor is a safety valve, not a price.

Three false paths were rejected with numbers: a gold reserve, Liquity-style
Recovery Mode (active 47 of 60 days, zero points of improvement), and a 250% ICR
(buys nothing, costs 25% capital efficiency).

---

## Repository structure

```
PROJECT-STATE.md              Status, critical path, document index — start here

docs/
  ENRK_ECOSYSTEM_PROPOSAL.md      Dossier for Kaspa core devs and KEF (English)
  ENRK_ECOSYSTEM_PROPOSAL_FR.md   Same, French
  design/
    FROZEN_PARAMETERS.md              Every parameter, its value, its evidence
    EXECUTION_TARGET_ASSESSMENT.md    Kaspa L1 vs Igra, with primary KIP citations
    L1_NATIVE_REDUCED_SPEC.md         L1 design and the covenant oracle construction
    PHASE_4_ARCHITECTURE_PROPOSAL.md  Master invariant, seniority waterfall
    Immutable-By-Design.md            Why no governance, and what forking replaces it with
    STRESS-TEST-CRASH-RESULTS.md      The freeze finding, and three corrected model errors
    RECOVERY-MODE-ANALYSIS.md         Why Recovery Mode buys nothing
    REDEMPTION-ANALYSIS.md            Mechanism #1: structural limit, halved losses

contracts/igra/               Rust reference implementation (119 tests)
tests/backtesting/            Stress test and Recovery Mode analysis (stdlib only)
```

---

## What is not claimed

- No code is deployed. No audit has been performed.
- The Rust implementation in `contracts/igra/` targeted an EVM rollup and **does
  not deploy**. It survives as an executable specification and a
  differential-testing oracle, nothing more.
- The covenant oracle construction is derived from KIP text and has **not been
  validated by anyone who wrote those KIPs**. That validation is the current
  blocker.
- Three sizing questions are unresolved: the compute-mass ceiling on input count,
  SilverScript script size limits, and block inclusion for a large sweep
  transaction.
- Being first on these primitives is a risk, not a feature. Immutable code plus
  three-month-old primitives plus no auditors with covenant experience is a
  combination taken seriously here.

---

## Model assumptions to distrust

Two parameters dominate every stress-test figure: `impact_coefficient` (0.08,
square-root law) and `daily_liquidation_capacity` (5% of debt per day). They are
assumptions, not measurements. Vary them and re-run before trusting any number.

---

**Author:** cyprox — sole developer. Contact via this repository.

**Licence:** GPL-3.0

Development is funded by a capped share of protocol fees, disclosed in the frozen
parameter specification: 20% of fees to a treasury address until a fixed
cumulative ceiling, then 0% forever. The ceiling is a compile-time constant, its
counter is readable on-chain by anyone, and no party can raise it.
