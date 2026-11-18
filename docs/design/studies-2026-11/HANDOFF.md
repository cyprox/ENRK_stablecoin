# Handoff log (studies-2026-11)

Why: dated record of what each work lot changed, how it was verified and what is left open (decision: owner approval of plan 2026-11-13; location and format of this log not yet validated by the owner). Facts only; newest entry first.

## 2026-11-17: documentation revision (no code, no number changed)

**Files changed**
- Text corrections, dated notes and synchronisation with the owner decisions of 2026-11-13 in the root documents (`README.md`, `PROJECT-STATE.md`, `KFIAT-DEFINITION-GAP.md`, `docs/ENRK_ECOSYSTEM_PROPOSAL.md`), in `docs/design/` (about 20 documents) and in the study reports of `studies-2026-11/reports/`. New: `contracts/README.md`, `reports/README.md`, `docs/design/peer-studies-2026-11/` (peer studies, oracle sheet, independent reviews, revision audits and logs).
- Retired from the repository to an archive outside it (`~/ENRK_archive/2026-11-17-retired-from-repo/`): `PROJECT_MANIFEST.md` and the pre-correction copy of the W1 report with its two fragments.

**Verification:** relative links checked on 67 modified or new Markdown files (no broken link in the documents); no address or key in any document. Details: `docs/design/peer-studies-2026-11/project-revision-2026-11-17/APPLIED-SUMMARY.md`.

**Open points:** code fixes listed in `D-code-vs-docs.md` (owner's decision); wording rows that need the owner (see APPLIED-SUMMARY); commit and push of the November work (owner's go).

## 2026-11-14/15: reactive borrowers (W2), independent review, corrections, L1 decision

**Files changed**
- New: `reports/econ-w2-reactive-borrowers.md`, `reports/review-w1-x1b-w2-independent.md`, `sources/econ/w2/sim/` (simulator with rb_* options, `w2_exp.py`, `w2_run.py`, `analyze_w2.py`, `check_w2.py`, copies of check_v1/check_w1, tables, run scripts), `CODE_MAP.md`, this file.
- Edited (text corrections from the review, no number re-run): `reports/econ-w1-unit-variants-rebase.md`, `reports/econ-x1b-population-refresh.md`, `reports/econ-w2-reactive-borrowers.md`, `PROJECT-STATE.md` (repo root) (execution layer: Kaspa L1, Igra not retained, owner 2026-11-13).
- 2026-11-15 edits in `w2/sim`: `check_w1.py`, `check_w2.py` (9 section comments relabelled, false positives of the ERA001 rule), `v1_exp.py` (unused `import sys` removed).

**Commits** (local, NOT pushed; 9 ahead of origin at 54e60e4): 54e60e4 (W2, review, corrections, L1). The 2026-11-15 edits and the two new files are not committed yet unless a later commit says otherwise.

**Verification (exit codes, python3 -I -B, from `w2/sim`, 2026-11-15)**
- check_v1: exit 0, 17,280 + 60 + 56 + 200 + 180 comparisons, 0 differences.
- check_w1: exit 0, 14,590 comparisons, 0 differences.
- check_w2: exit 0, 30,060 comparisons, 0 differences.
- qgate (`ruff` F401, F841, T201, ERA001, W291, W293; `vulture` min-confidence 80) on `w2/sim`: vulture finds nothing; ruff finds only T201 (216 `print` calls in scripts that print their results, 15 files, mostly copies of earlier validated files). F401 and ERA001 findings are fixed. NOT clean as defined: the T201 question is the owner's.
- Independent review of the work: `reports/review-w1-x1b-w2-independent.md` (38 findings, none high).

**Open points**
- Decisions for the owner: T201 policy (ignore in experiment scripts via a ruff config, or replace prints); push of the local commits; commit of this lot's last edits; the open design decisions in `PROJECT-STATE.md`.
- Work proposed by the review, not done: re-run W1 WC with the exogenous redemption schedule OFF (s*, r_clear, E_w); corner profiles for W2; strengthen `check_w2` (sub-checks 5a, 5b, 5e vacuous; nothing tests exit sale size, dump accounting, miner drain, run sizing); save the x1b refusal outputs for N = 47..128; reconcile 327,600 sompi of fees; size-ceiling reporting (unbacked and stranded/latent together).
- Duplication: `analyze_w2.py` helpers copied from `analyze_w1.py` (not imported).
- Hypotheses coded in the simulator but absent from the design (listed, none adopted): owner attention, top-up and early-exit behaviour, speculators, miner opex drain, holder run at face. All their parameters are swept ASSUMPTIONS, none measured; the exogenous redemption schedule and the 1%-of-ADV liquidator throughput are also assumptions inherited from W1.
- Not committed on purpose: `w2/sim/{HL,OAT,SENS,SIZE}.pkl` (22-60 MB), regenerable with `run_runs.sh` (about 1.5 h on 3 processes).
