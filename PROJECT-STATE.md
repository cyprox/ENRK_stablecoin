# ENRK — Project State

**Last updated:** September 8, 2026
**Author:** cyprox
**Repository:** https://github.com/cyprox/ENRK_stablecoin

**Read this first.** The project now holds a dozen analyses. This document says
where things stand, what is decided, what is blocked, and what to do next.

---

## One-line status

Design and specification complete. Implementation not started, and deliberately so:
the execution layer is undecided. The oracle construction has been measured against
the real Kaspa script engine, which answered three of the four questions it was
blocked on. One remains open, and no core developer has confirmed the reading yet.

---

## The critical path

Four questions were put to Kaspa core developers in §7.1 of the ecosystem proposal
and filed as [`kaspanet/kips` issue #46](https://github.com/kaspanet/kips/issues/46)
on September 5, 2026.

**Three of them were answered on September 6 by compilation and measurement**, not
by argument. Two oracle/vault variants were written in Argent
(`argent-lang/argent` d08e52d — 82 of 86 commits by Michael Sutton, co-author of
KIP-20), compiled, and executed through the real Kaspa mainnet script engine via
`argent-runtime` and `MassCalculator`.

| | Question | Result |
|---|---|---|
| Q1a | Can a covenant observe a sibling input's `covenant_id`? | **Yes** |
| Q1b | Does the 1→N split preserve `covenant_id` across children? | **Yes** |
| Q1c | Can `covenant_id` be a compile-time constant? | **No** — newly surfaced |
| Q2 | Ceiling on N per oracle round | **640** (variant A) / **530** (variant B), bounded by transient mass, not compute mass |
| Q3 | SilverScript / Argent script size | Negligible — 1,046 B and 1,206 B, 0.1% of the 1 MB limit |
| Q4 | Block inclusion under contention | **Open** — requires Testnet-10 |

Method, tables and reproduction instructions: `docs/design/GITHUB-ISSUE-46-UPDATE.md`.
Source under `examples/enrk/` and `tests/enrk_mass.rs`. Published as two comments on
issue #46 on September 6, 2026.

**Status: measured, awaiting confirmation.** The construction holds as far as a
local mainnet engine can establish. What has not happened is a core developer
saying so, and the KEF ask still depends on that.

### What the measurement opened rather than closed

1. **Q1c — where the oracle identity lives.** The oracle's `covenant_id` cannot be
   frozen into the vault script as a compile-time constant; the compiler requires a
   state field or an argument. The vault therefore carries the oracle identity in
   its own state, fixed at vault creation. **What guarantees it is the right oracle
   at that moment is not yet specified.** On immutable code this is a security
   question, not a formatting one, and it is unresolved.

2. **Variant A or B — not decided.** A allows roughly 21% more N in calm markets.
   B incurs zero storage mass under any price movement, where A incurs 711,040
   units at N=640 on a −10% drop, exceeding the 500,000 per-block limit. A also
   locks working capital, since the USE branch requires recreating an output of
   identical amount. The trade-off is measurable and the measurement is not yet
   done.

The layer decision still depends on core-developer confirmation, and settles two
other open items (fee destination, Stability Pool's fate) plus the implementation
language.

---

## Decided and frozen

| | |
|---|---|
| Peg formula | 40 hashrate / 30 energy / 20 fees / 10 adoption, clipped [0.1, 5.0] |
| ICR minimum | 200% (250% rejected — buys nothing, costs 25% capital efficiency) |
| MCR | 150% (raising it buys almost no protection) |
| kFIAT cap | 30% of debt **at mint**, not a permanent guarantee |
| Auction | 120 min, 100% → **75%** (changed from 85%) |
| Redemption | Lowest-ICR-first, 100% floor, ENRK only, 1% fee |
| Fees | 2% mint / 4% liquidation / 1% redemption, **taken in KAS from collateral** |
| Treasury | 20% until **2,500,000 peg units**, then 0% forever |
| Circuit breaker | 10% peg deviation, 6h oracle downtime, no override |
| Governance | None. Ever. Forks only. |

Full justifications: [`docs/design/FROZEN_PARAMETERS.md`](docs/design/FROZEN_PARAMETERS.md).

---

## Open, all blocked on the layer decision

1. Execution layer — Kaspa L1 covenants vs Igra EVM
2. Fee destination after the treasury cap — burn on L1, pro-rata reserve on Igra
3. Stability Pool — fix it or remove it

---

## What the analysis found

**Four defects in our own design**, none found by an auditor:

- the protocol **freezes** rather than exploding, and nobody can unfreeze it
- the Stability Pool **cannot buy** — it burns what it already holds
- redemption, equilibrium mechanism #1, was **never implemented**
- the kFIAT cap is a mint-time ceiling, not a permanent guarantee

**Three false paths rejected with numbers:**

- a gold reserve (LFG precedent: $3B consumed in seven days)
- Recovery Mode (47 of 60 days active, zero points of improvement)
- 250% ICR (buys nothing, costs 25% capital efficiency)

**One fix, quantified:** auction floor at 75% plus redemption. Together they take
the p95 latent hole from 46% to zero and halve the losses.

**One correction of course:** ~5,000 lines of Rust were written for the wrong
execution target. Igra is an EVM rollup; the code does not deploy. It survives as
an executable specification and a differential-testing oracle. Found before an
audit, not after.

**One original construction:** a contention-free price oracle from Kaspa covenants,
built only on shipped opcodes, which reopened an L1 path previously declared closed
— and which has since been compiled and measured rather than argued.

---

## Document index

| Document | What it holds |
|---|---|
| [`docs/ENRK-System-Map.pdf`](docs/ENRK-System-Map.pdf) | **The whole protocol in 12 pages** — actors and incentives, attack surface, fee and burn flow, stress-test results, rejected paths. Start here for the overview. |
| [`docs/design/FROZEN_PARAMETERS.md`](docs/design/FROZEN_PARAMETERS.md) | Every parameter, its value, its evidence. **Start here for implementation.** |
| [`docs/ENRK_ECOSYSTEM_PROPOSAL.md`](docs/ENRK_ECOSYSTEM_PROPOSAL.md) | The dossier for Kaspa core devs and KEF |
| [`docs/design/EXECUTION_TARGET_ASSESSMENT.md`](docs/design/EXECUTION_TARGET_ASSESSMENT.md) | Kaspa L1 vs Igra, primary KIP citations, bridges, throughput ceilings |
| [`docs/design/L1_NATIVE_REDUCED_SPEC.md`](docs/design/L1_NATIVE_REDUCED_SPEC.md) | The L1 design, with the covenant oracle construction |
| [`docs/design/STRESS-TEST-CRASH-RESULTS.md`](docs/design/STRESS-TEST-CRASH-RESULTS.md) | The freeze finding, and the three modelling errors corrected |
| [`docs/design/RECOVERY-MODE-ANALYSIS.md`](docs/design/RECOVERY-MODE-ANALYSIS.md) | Why Recovery Mode buys nothing; why the auction floor is the lever |
| [`docs/design/REDEMPTION-ANALYSIS.md`](docs/design/REDEMPTION-ANALYSIS.md) | Mechanism #1: its structural limit, and the halved losses |
| [`docs/design/PHASE_4_ARCHITECTURE_PROPOSAL.md`](docs/design/PHASE_4_ARCHITECTURE_PROPOSAL.md) | The double-bookkeeping problem, the master invariant, the seniority waterfall |
| [`docs/design/Immutable-By-Design.md`](docs/design/Immutable-By-Design.md) | Why there is no governance, what is frozen, and what forking replaces it with |
| [`docs/design/GITHUB-ISSUE-46-UPDATE.md`](docs/design/GITHUB-ISSUE-46-UPDATE.md) | Oracle validation: method, tables, the KIP-9 asymmetry, reproduction steps |
| [`docs/design/GITHUB-ISSUE-46-COMMENT.md`](docs/design/GITHUB-ISSUE-46-COMMENT.md) | The same, as summarised for issue #46 |
| [`docs/design/PEG-FORMULA-RECOMMENDATION.md`](docs/design/PEG-FORMULA-RECOMMENDATION.md) | The chosen peg formula, its calibration, and the black scenarios |
| [`docs/design/BACKTESTING-PEG-FORMULAS.md`](docs/design/BACKTESTING-PEG-FORMULAS.md) | The three peg alternatives, and why Alt 3.5 |
| [`docs/design/STABLECOIN-FAILURE-ANALYSIS.md`](docs/design/STABLECOIN-FAILURE-ANALYSIS.md) | Terra, DOLA, Curve — the failures the design is built against |

Code and tests live in the repository: `contracts/igra/` (Rust reference
implementation, 119 tests), `tests/backtesting/` (stress test and Recovery Mode
analysis, standard library only), `examples/enrk/` (Argent source for both oracle
variants) and `tests/enrk_mass.rs` (the mass measurement harness).

---

## Known non-technical risks

**No prior art.** Nobody has shipped a CDP stablecoin on Kaspa covenants. First of
its kind plus never-patchable is the combination that should worry us most.

**Almost no auditors.** SilverScript is three months old. This is very likely the
real blocker, regardless of any technical answer — and it is the argument the
ecosystem proposal is built on: the first covenant audit produces a methodology the
whole ecosystem inherits.

**Model assumptions.** Two parameters dominate the stress test:
`impact_coefficient` (0.08) and `daily_liquidation_capacity` (5% of debt per day).
They are assumptions, not measurements. Vary them and re-run before trusting any
figure.

---

## Document hygiene

Three rules, and they exist because each was broken once.

**1. When an analysis reverses a conclusion, the document holding the old conclusion
is revised or deleted the same day.** On September 4 there was a four-hour window in
which `STRESS-TEST-CRASH-RESULTS` recommended Recovery Mode and
`RECOVERY-MODE-ANALYSIS` disproved it. A project whose own documents disagree cannot
be audited, and this one intends to be.

**2. Every decision and every measurement is written into this repository the same
day. A working session is a plan, never a store.** Chat transcripts, scratch folders
and session outputs are not durable: they are compacted, wiped, or simply lost. On
September 6 the oracle measurements existed only in a transcript and two GitHub
comments for two days, during which four documents in this repository continued to
state that the questions were open. Nothing counts as recorded until it is committed
here.

**3. Before asserting the state of a file, read the file.** On September 8 two
sessions reached opposite conclusions about `README.md` — one from a stale memory
note, one from a cached GitHub page. Three `curl` calls against
`raw.githubusercontent.com` settled it. Neither a summary nor a rendered web page is
evidence about a file's contents.

An earlier hygiene pass on September 5 audited every document against
`FROZEN_PARAMETERS.md`. Seven were deleted and seven revised — all seven deletions
asserted some combination of an 85% auction floor, an 80/20 fee split to a Stability
Pool, a working Stability Pool buyback, a Band/Chainlink oracle, or a DAO able to
resolve a circuit-breaker event. None of those is the design.

---

Licence: GPL-3.0
