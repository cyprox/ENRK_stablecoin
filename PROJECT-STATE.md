# ENRK — Project State

**Last updated:** November 10, 2026
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

**Audit of November 9–10, 2026** ([`docs/design/AUDIT-2026-11-09.md`](docs/design/AUDIT-2026-11-09.md)).
As written, a vault and an oracle price UTXO could not be co-spent: the vault demanded
zero oracle outputs while every oracle spend creates one. With the oracle outputs
declared in both vault entries, the lifecycle was executed on testnet-10 with real
transactions: oracle genesis, vault genesis, a real liquidation, and oracle rounds of 64
and 256 inputs, all confirmed. Inclusion near a full block (N ≈ 500–640) is untested.

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
| Q2 | Ceiling on N per oracle round | **642** (variant A) / **532** (variant B), bounded by transient mass, not compute mass. No 100 k standard-mass cap exists after Toccata in rusty-kaspa v2.1.0 (audit P4); N = 256 was included on testnet-10 |
| Q3 | SilverScript / Argent script size | Negligible — 1,046 B and 1,206 B, 0.1% of the 1 MB limit |
| Q4 | Block inclusion under contention | **Partly answered** — N = 256 round (compute mass 195,930) included on testnet-10; N ≈ 500–640 not tested; mainnet contention not tested |
| Q5 (new) | Can a vault and an oracle price UTXO be co-spent? | **Refused as written; accepted once both vault entries declare the oracle outputs** (executed locally and on testnet-10, audit B1/P1) |

Method, tables and reproduction instructions: `docs/design/GITHUB-ISSUE-46-UPDATE.md`.
Source under `examples/enrk/` and `tests/enrk_mass.rs`. Published as two comments on
issue #46 on September 6, 2026.

**Re-measured September 15, 2026** against Argent `e76ee07` and the released
Silverscript v1.0.0. Every published figure reproduced to the unit, so Q1a, Q1b,
Q2 and Q3 stand on a toolchain two revisions and one language release later. The
exercise also found three defects in this repository and one claim the generated
code contradicts. Full record, corrections and reproduction:
[`docs/design/REMEASUREMENT-2026-09-15.md`](docs/design/REMEASUREMENT-2026-09-15.md).

**Status: measured, awaiting confirmation.** The construction holds as far as a
local mainnet engine can establish. What has not happened is a core developer
saying so, and the KEF ask still depends on that.

### What the measurement opened rather than closed

1. **Q1c — where the oracle identity lives.** The oracle's `covenant_id` cannot be
   frozen into the vault script as a compile-time constant; the compiler requires a
   state field or an argument. Reframed on September 15: the binding that must be
   secured is **asset → vault**, not vault → oracle, because a forged vault is
   inert unless it can mint real ENRK — and a `MinterProxy` holds exactly one
   covenant id, so a permissionless vault population needs a common ancestor that
   every mint would contend on. Michael Sutton pointed at Argent's open-ICC
   `spawns` pattern for the lineage primitive; Argent's own docs record the
   KCC20 bootstrap and launch proofs as unimplemented follow-ups. See
   [`docs/design/ORACLE-BINDING.md`](docs/design/ORACLE-BINDING.md).
   **Unresolved.**

1b. **The round transition is not atomic as written.** `sweep` emits two outputs,
   not N. The atomicity that removes the stale-price window in
   `L1_NATIVE_REDUCED_SPEC` §2.3 does not follow from a binary split. Open design
   decision, and it gates the next measurement.

1c. **Two undefined behaviours in our own Argent sources.** `icr_percent` divides
   by an unchecked `debt` and overflows above ~9.2 KAS of collateral at price 1e8
   (bound: `collateral × price × 100 ≤ 9.22e18`; executed: 9 KAS accepted, 10 KAS refused),
   in both variants and both entries. The compiler accepts it silently. On today's engine
   both fail closed, so affected vaults become impossible to liquidate or withdraw
   from rather than exploitable — the freeze, reached by arithmetic. See
   [`docs/design/UNDEFINED-BEHAVIOUR-EXPOSURE.md`](docs/design/UNDEFINED-BEHAVIOUR-EXPOSURE.md).

2. **Variant A or B — not decided.** A allows roughly 21% more N in calm markets.
   B incurs zero storage mass under any price movement, where A incurs 711,040
   units at N=640 on a −10% drop, exceeding the 500,000 per-block limit. A also
   locks working capital, since the USE branch requires recreating an output of
   identical amount. The trade-off is measurable and the measurement is not yet
   done.

1d. **Genesis storage mass.** Covenant outputs have plurality 2, so a genesis of N price
   UTXOs costs about 4·N·10¹²/value in storage mass. A genesis of 128 UTXOs of 10 KAS was
   refused by the node (512,000 > 500,000). Each UTXO needs value ≥ 8·10⁶·N sompi, or the
   population must grow by `sweep` batches. Rounds that keep values unchanged cost no
   storage mass. See audit §13.3b.

1e. **Variant A `sweep` accepts a price of 0**; variant B refuses `next_price ≤ 0`. Neither
   bounds a single-round price move (audit I26).

1f. **Oracle authentication in the generated vault code rests on a statement whose result
   is never used.** It survives only because the compiler's alias-lowering pass is
   disabled, while the language's undefined-behaviour specification allows a future
   compiler to drop it (audit §13.2).

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

Opened by the November audit and by `KFIAT-DEFINITION-GAP.md`:

8. kFIAT denomination — fixed face in peg units, or residual claim at market. Gates the cap,
   the ICR and every published figure, all of which assume par.
9. Loss-absorption rule (waterfall, or carry-over to borrowers with or without a cap).
10. A reason to hold kFIAT: nothing forces or rewards minting it today.
11. A hard debt ceiling or ramp sized from measured KAS liquidity.
12. An unfreeze mechanism and the Stability Pool's fate.

Independent of the layer, and opened by the September 15 re-measurement:

4. The form of the oracle round transition (binary sweep, or N sweeps batched)
5. The asset → vault minting binding
6. An arithmetic discipline for immutable Argent code, and its audit scope
7. The mass cost of the liquidation transaction, never measured

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

**Code reality (audit B2, B3, I8):** `contracts/igra` still carries the 85 % floor and the
80/20 fee split; the seniority cascade and redemption are not implemented; `submit_bid`
mixes KAS and stablecoin units; two different ICRs exist for one vault.

**Two frozen statements are not reproduced by the repository's own model (audit I1, I2):**
"250 % ICR is slightly worse than 200 %" (250 % is better in the model; the rejection may
stand on capital efficiency alone) and "kFIAT 2 %" at −85 % (reproducible: mean ~10 %,
p95 ~39 %; the median is unstable at 3–6 %). Values in the frozen table are unchanged; the
wording is to be reviewed.

**One original construction:** a contention-free price oracle from Kaspa covenants,
built only on shipped opcodes, which reopened an L1 path previously declared closed
— and which has since been compiled and measured rather than argued.

---

## Document index

| Document | What it holds |
|---|---|
| [`docs/ENRK-System-Map.pdf`](docs/ENRK-System-Map.pdf) | The protocol in 12 pages, **as of September 5** — it predates the oracle measurements and the November audit; use it for the overview only. |
| [`docs/design/FROZEN_PARAMETERS.md`](docs/design/FROZEN_PARAMETERS.md) | Every parameter, its value, its evidence. **Start here for implementation.** |
| [`docs/ENRK_ECOSYSTEM_PROPOSAL.md`](docs/ENRK_ECOSYSTEM_PROPOSAL.md) | The dossier for Kaspa core devs and KEF |
| [`docs/design/EXECUTION_TARGET_ASSESSMENT.md`](docs/design/EXECUTION_TARGET_ASSESSMENT.md) | Kaspa L1 vs Igra, primary KIP citations, bridges, throughput ceilings |
| [`docs/design/L1_NATIVE_REDUCED_SPEC.md`](docs/design/L1_NATIVE_REDUCED_SPEC.md) | The L1 design, with the covenant oracle construction |
| [`docs/design/STRESS-TEST-CRASH-RESULTS.md`](docs/design/STRESS-TEST-CRASH-RESULTS.md) | The freeze finding, and the three modelling errors corrected |
| [`docs/design/RECOVERY-MODE-ANALYSIS.md`](docs/design/RECOVERY-MODE-ANALYSIS.md) | Why Recovery Mode buys nothing; why the auction floor is the lever |
| [`docs/design/REDEMPTION-ANALYSIS.md`](docs/design/REDEMPTION-ANALYSIS.md) | Mechanism #1: its structural limit, and the halved losses |
| [`docs/design/PHASE_4_ARCHITECTURE_PROPOSAL.md`](docs/design/PHASE_4_ARCHITECTURE_PROPOSAL.md) | The double-bookkeeping problem, the master invariant, the seniority waterfall |
| [`docs/design/Immutable-By-Design.md`](docs/design/Immutable-By-Design.md) | Why there is no governance, what is frozen, and what forking replaces it with |
| [`docs/design/REMEASUREMENT-2026-09-15.md`](docs/design/REMEASUREMENT-2026-09-15.md) | **The current state of the measurement.** Re-measurement on Argent `e76ee07` + Silverscript v1.0.0, corrections, what is open and in what order. Start here to resume the work. |
| [`docs/design/UNDEFINED-BEHAVIOUR-EXPOSURE.md`](docs/design/UNDEFINED-BEHAVIOUR-EXPOSURE.md) | Line-by-line audit of both variants against Silverscript's undefined-behaviour specification |
| [`docs/design/ORACLE-BINDING.md`](docs/design/ORACLE-BINDING.md) | Q1c reframed: the asset → vault binding, Argent's `spawns` lineage, and what Argent does not yet provide |
| [`docs/design/AUDIT-2026-11-09.md`](docs/design/AUDIT-2026-11-09.md) | **The current audit.** Findings by severity, the Kaspa fact base, testnet-10 results, options and the decisions that belong to the owner. Start here to resume. |
| [`KFIAT-DEFINITION-GAP.md`](KFIAT-DEFINITION-GAP.md) | The undefined denomination of kFIAT, the two ICRs, the unimplemented waterfall. |
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

**Almost no auditors.** Silverscript reached **v1.0.0 on September 9, 2026**, with
a tagged release and an explicit SemVer commitment — a real improvement over
building on a moving `master`. But the release notes describe a review, testing
and standardisation process, not an audit; the word does not appear in the release
notes or anywhere in the repository, `SECURITY.md` at the tagged commit still
calls the language experimental, and no audit report was found. Argent states of
itself that it needs its own audit after Silverscript's. So the risk changes shape
rather than going away: **nobody has audited a Silverscript covenant system for
immutable deployment**, and an ENRK audit must cover two layers, our source and
Argent's lowering. This remains very likely the real blocker, and it is the
argument the ecosystem proposal is built on: the first covenant audit produces a
methodology the whole ecosystem inherits.

**Model assumptions.** Two parameters dominate the stress test:
`impact_coefficient` (0.08) and `daily_liquidation_capacity` (5% of debt per day).
They are assumptions, not measurements. Vary them and re-run before trusting any
figure. Measured on November 10, 2026 (one calm snapshot, public order books): real KAS
volume is about 70–230 M KAS/day against 40 M modelled; 0.08 is plausible for calm markets
up to 5 % of daily volume and probably optimistic in stress; the book has no square-root
behaviour beyond ~9 % of daily volume; the worst observed 60-day drawdown is about −62 %,
so −85 % in 60 days is outside the history. ENRK p95 loss spans 0.1–23.9 % over
impact × capacity combinations (audit I14, §13.3).

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

On November 10, 2026 the first version of the audit stated a 100,000 standard-mass cap that
rusty-kaspa had already removed; it was corrected the same day from the source of the
release in question. Rule 3 applies to node policy as well as to files: read the code of
the release you are talking about.

An earlier hygiene pass on September 5 audited every document against
`FROZEN_PARAMETERS.md`. Seven were deleted and seven revised — all seven deletions
asserted some combination of an 85% auction floor, an 80/20 fee split to a Stability
Pool, a working Stability Pool buyback, a Band/Chainlink oracle, or a DAO able to
resolve a circuit-breaker event. None of those is the design.

---

Licence: GPL-3.0
