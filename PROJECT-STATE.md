# ENRK — Project State

**Last updated:** September 5, 2026
**Author:** cyprox
**Repository:** https://github.com/cyprox/ENRK_stablecoin

**Read this first.** The project now holds a dozen analyses. This document says
where things stand, what is decided, what is blocked, and what to do next.

---

## One-line status

Design and specification complete. Implementation not started, and deliberately so:
the execution layer is undecided and blocked on a single external answer.

---

## The critical path

Everything downstream waits on **one question**, put to Kaspa core developers in
§7.1 of the ecosystem proposal:

> Is the covenant oracle construction sound? Can a covenant reliably verify
> `OpInputCovenantId` on a sibling input, and does the one-to-many split preserve
> `covenant_id` across all authorised children?

- **Yes** → Kaspa L1 native. No custodian, no bridge, no size ceiling, exact
  doctrinal fit.
- **No** → Igra EVM, bounded and disclosed, or wait for a KIP-16 trustless bridge.

The answer also settles two other open items (fee destination, Stability Pool's
fate) and determines the implementation language.

**The single action outstanding: send the proposal.** Core developers first —
the four questions are addressed to their own specification. Then KEF, once
"reviewed by a core developer" can be written into the ask.

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
built only on shipped opcodes, which reopened an L1 path previously declared closed.

---

## Document index

| Document | What it holds |
|---|---|
| [`docs/design/FROZEN_PARAMETERS.md`](docs/design/FROZEN_PARAMETERS.md) | Every parameter, its value, its evidence. **Start here for implementation.** |
| [`docs/ENRK_ECOSYSTEM_PROPOSAL.md`](docs/ENRK_ECOSYSTEM_PROPOSAL.md) / [`_FR`](docs/ENRK_ECOSYSTEM_PROPOSAL_FR.md) | The dossier for Kaspa core devs and KEF |
| [`docs/design/EXECUTION_TARGET_ASSESSMENT.md`](docs/design/EXECUTION_TARGET_ASSESSMENT.md) | Kaspa L1 vs Igra, primary KIP citations, bridges, throughput ceilings |
| [`docs/design/L1_NATIVE_REDUCED_SPEC.md`](docs/design/L1_NATIVE_REDUCED_SPEC.md) | The L1 design, with the covenant oracle construction |
| [`docs/design/STRESS-TEST-CRASH-RESULTS.md`](docs/design/STRESS-TEST-CRASH-RESULTS.md) | The freeze finding, and the three modelling errors corrected |
| [`docs/design/RECOVERY-MODE-ANALYSIS.md`](docs/design/RECOVERY-MODE-ANALYSIS.md) | Why Recovery Mode buys nothing; why the auction floor is the lever |
| [`docs/design/REDEMPTION-ANALYSIS.md`](docs/design/REDEMPTION-ANALYSIS.md) | Mechanism #1: its structural limit, and the halved losses |
| [`docs/design/PHASE_4_ARCHITECTURE_PROPOSAL.md`](docs/design/PHASE_4_ARCHITECTURE_PROPOSAL.md) | The double-bookkeeping problem, the master invariant, the seniority waterfall |

Code and tests live in the repository: `contracts/igra/` (Rust reference
implementation, 119 tests) and `tests/backtesting/` (stress test and Recovery Mode
analysis, standard library only).

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

Licence: GPL-3.0
