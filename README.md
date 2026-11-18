# ENRK — Kaspa Energy Reserve Stablecoin

An over-collateralised stablecoin whose unit of account is **one kilowatt hour of
thermodynamic value**, not a fiat currency. Designed to be **immutable after
deployment**: no DAO, no admin keys, no upgrade path. Evolution happens by fork,
chosen by users.

---

## Status — read this before anything else

**The core design and specification are written; several design questions are still open and belong to the owner (see `PROJECT-STATE.md`, section Open). Implementation not started.**

The execution layer is decided by the owner (2026-11-13): Kaspa L1 covenants; Igra is not retained. The covenant-based price oracle described in
[`docs/design/L1_NATIVE_REDUCED_SPEC.md`](docs/design/L1_NATIVE_REDUCED_SPEC.md)
was **implemented, compiled and measured** on September 6, 2026 — written in Argent,
executed through the real Kaspa mainnet script engine — which answered three of the
four questions filed as
[`kaspanet/kips` issue #46](https://github.com/kaspanet/kips/issues/46):

| | Question | Result |
|---|---|---|
| Q1a | Sibling input `covenant_id` observable? | **Yes** |
| Q1b | 1→N split preserves `covenant_id`? | **Yes** |
| Q1c | `covenant_id` as a compile-time constant? | **No** — new constraint |
| Q2 | Ceiling on N per oracle round | **642** / **532**, bounded by transient mass |
| Q3 | Script size | 0.1% of the 1 MB limit |
| Q4 | Block inclusion under contention | **Answered on testnet-10, not on mainnet**: an N = 640 round (97.5 % of the compute limit) was included in about 8 s on a lightly loaded testnet; mainnet contention not tested |
| Q5 (new) | Can a vault and an oracle price UTXO be co-spent? | **Refused as written; accepted once both vault entries declare the oracle outputs** (executed on testnet-10) |

Method and reproduction:
[`docs/design/GITHUB-ISSUE-46-UPDATE.md`](docs/design/GITHUB-ISSUE-46-UPDATE.md).
Source under [`examples/enrk/`](examples/enrk/) and
[`tests/enrk_mass.rs`](tests/enrk_mass.rs).

**Re-measured on September 15, 2026** against Argent `e76ee07` and the released
Silverscript v1.0.0: every published figure reproduced to the unit. The same
exercise found three defects in this repository, including a published
reproduction procedure that does not reproduce, and one claim the generated code
contradicts. See
[`docs/design/REMEASUREMENT-2026-09-15.md`](docs/design/REMEASUREMENT-2026-09-15.md).

**A local engine agreeing with our reading is not a core developer agreeing with
it.** Confirmation has not arrived. Two questions the measurement opened rather
than closed — where the oracle identity is bound (Q1c), and which of the two
variants to deploy — are open and documented in
[`PROJECT-STATE.md`](PROJECT-STATE.md).

No code is deployed. No audit has been performed. Nothing here should be read as
an invitation to use the protocol.

**Since September.** A full audit (Nov 9-10) and testnet-10 executions of the oracle and vault lifecycle; an economics and mechanism verification (Nov 11-15) with simulations of crash safety, unit of account and reactive borrowers; studies of peer designs (Kaspa Dollar, kUSD, Monolith, Frax) and an oracle sheet (Nov 15-17). Owner decisions taken: execution layer Kaspa L1 (Igra not retained, 2026-11-13); a recurring stability fee; fees are never burned; ENRK has its own price oracle. Still open: the fate of the peg index, the loss-absorption structure, the role of the fee reserve, the debt-ceiling method, the issuance-cap design and the oracle phasing and bound. See `PROJECT-STATE.md`.

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

Status note: the peg index (unit of account and formula), the junior share and the loss-absorption structure are under review; the owner has not decided them (see `docs/design/ECONOMICS-VERIFICATION-2026-11-11.md`, section 9). The values in the table are unchanged until he does.

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

These values date from September 3-5. Since then: (a) the stress-test figures behind them were found to inherit a hidden cushion from the simulator's default index response (`ECONOMICS-VERIFICATION` section 1); (b) the circuit breaker as coded was found harmful because it can halt liquidations, and its fate is an open owner decision; (c) the owner has decided there will be a recurring stability fee, never burned; its rate, and the destination of fees after the treasury cap, are not decided.

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
discount in calm markets. The floor is a safety valve, not a price. (Measured on the original simulator; its default index response lowers debt value in a crash, so the figure has not been shown to hold when the index does not fall with KAS. See `ECONOMICS-VERIFICATION` section 1.)

Three false paths were rejected with numbers: a gold reserve, Liquity-style
Recovery Mode (active 47 of 60 days, zero points of improvement), and a 250% ICR
(rejected on capital efficiency, 25% more capital for the borrower; in the model it protects slightly more, audit I2).

---

## Repository structure

```
PROJECT-STATE.md              Status, critical path, document index — start here
KFIAT-DEFINITION-GAP.md       The undefined denomination of kFIAT

docs/
  ENRK-System-Map.pdf             The protocol in 12 pages, as of September 5 (overview only)
  ENRK_ECOSYSTEM_PROPOSAL.md      Dossier for Kaspa core devs and KEF
  design/
    FROZEN_PARAMETERS.md              Every parameter, its value, its evidence
    EXECUTION_TARGET_ASSESSMENT.md    Kaspa L1 vs Igra, with primary KIP citations
    L1_NATIVE_REDUCED_SPEC.md         L1 design and the covenant oracle construction
    PHASE_4_ARCHITECTURE_PROPOSAL.md  Master invariant, seniority waterfall
    Immutable-By-Design.md            Why no governance, and what forking replaces it with
    STRESS-TEST-CRASH-RESULTS.md      The freeze finding, and three corrected model errors
    RECOVERY-MODE-ANALYSIS.md         Why Recovery Mode buys nothing
    REDEMPTION-ANALYSIS.md            Mechanism #1: structural limit, halved losses
    BACKTESTING-PEG-FORMULAS.md       The three peg alternatives, and why Alt 3.5
    PEG-FORMULA-RECOMMENDATION.md     The chosen formula, its calibration, black scenarios
    STABLECOIN-FAILURE-ANALYSIS.md    Terra, DOLA, Curve — the failures designed against
    GITHUB-ISSUE-46-COMMENT.md        Oracle validation — summary posted to issue #46
    GITHUB-ISSUE-46-UPDATE.md         Oracle validation — full report, tables, method
    REMEASUREMENT-2026-09-15.md       Re-measurement on Argent e76ee07 + Silverscript v1.0.0
    UNDEFINED-BEHAVIOUR-EXPOSURE.md   Undefined-behaviour audit of the Argent sources
    ORACLE-BINDING.md                 Asset-to-vault binding (Q1c)
    AUDIT-2026-11-09.md               Audit and testnet-10 results
    ECONOMICS-VERIFICATION-2026-11-11.md  Economics and mechanism verification
    studies-2026-11/                  Reports, scripts, handoff log
    peer-studies-2026-11/             Kaspa Dollar review, oracle sheet, comparison with Monolith and Frax

examples/enrk/                Argent source for the oracle/vault construction
  a/oracle.ag  a/vault.ag       Variant A — price encoded in the UTXO amount
  b/oracle.ag  b/vault.ag       Variant B — price as a typed state field
  probe_const_covid.ag          Probe for Q1c; fails to compile, as documented

contracts/igra/               Rust reference implementation (119 tests)
tests/enrk_mass.rs            Mass measurement harness — real mainnet script engine
tests/backtesting/            Stress test and Recovery Mode analysis (stdlib only)
```


---

## What is not claimed

- No code is deployed. No audit has been performed.
- The Rust implementation in `contracts/igra/` targeted an EVM rollup (Igra, not retained) and **does
  not deploy**. It survives as an executable specification and a
  differential-testing oracle, nothing more.
- The covenant oracle construction has been compiled and measured against the real
  Kaspa mainnet script engine, but it has **not been reviewed by anyone who wrote
  those KIPs**. A local engine agreeing with our reading is not the same thing.
  That review is the current blocker.
- Block inclusion for a large sweep transaction was answered on testnet-10 only
  (an N = 640 round was included in about 8 s on a lightly loaded testnet);
  behaviour under mainnet contention is not tested.
- The measurement surfaced a constraint we had not anticipated: `covenant_id`
  cannot be a compile-time constant, so each vault carries the oracle identity in
  its own state. **What guarantees a vault is bound to the correct oracle at
  creation is not yet specified**, and on immutable code that is a security
  question.
- Which of the two oracle variants to deploy is not decided.
- **The round transition is not atomic as written.** `sweep` emits two outputs,
  not N, so the stale-price-free property claimed in the specification does not
  follow from the construction as it stands. The form of the split is an open
  design decision.
- **Our own Argent sources contain two reachable undefined behaviours**, in the
  ICR computation used by both vault entries of both variants, accepted by the
  compiler without a diagnostic. On today's engine they fail closed, which makes
  affected vaults impossible to liquidate rather than exploitable. Documented in
  [`docs/design/UNDEFINED-BEHAVIOUR-EXPOSURE.md`](docs/design/UNDEFINED-BEHAVIOUR-EXPOSURE.md)
  rather than fixed quietly.
- The mass cost of a liquidation transaction was measured in November: about
  0.4 % of compute and 0.7 % of transient mass for one vault and one price
  input (local engine), and 180 vaults in one transaction on testnet-10. These
  are lower bounds: real signatures and the auction distribution rules are not
  included.
- Being first on these primitives is a risk, not a feature. Immutable code, plus
  primitives nobody has shipped a CDP stablecoin on, plus a language that reached
  v1.0.0 with no published audit, plus no auditors with covenant experience, is a
  combination taken seriously here. Nobody has shipped one; two peer designs exist before launch: Kaspa Dollar (specification, no public code at the 2026-11-15 review) and kUSD (testnet-10 research code, not audited).

---

## Model assumptions to distrust

Two parameters dominate every stress-test figure: `impact_coefficient` (0.08,
square-root law) and `daily_liquidation_capacity` (5% of debt per day). They are
assumptions, not measurements. Vary them and re-run before trusting any number.

One more, on the toolchain side: Silverscript reached v1.0.0 on September 9,
2026, but its release describes a review process rather than an audit, and no
audit report exists. Argent says of itself that it needs one after Silverscript's.
Nobody has audited a Silverscript covenant system for immutable deployment.

---

**Author:** cyprox — sole developer. Contact via this repository.

**Licence:** GPL-3.0

Development is funded by a capped share of protocol fees, disclosed in the frozen
parameter specification: 20% of fees to a treasury address until a fixed
cumulative ceiling, then 0% forever. The ceiling is a compile-time constant, its
counter is readable on-chain by anyone, and no party can raise it.
