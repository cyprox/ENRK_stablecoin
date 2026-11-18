# Documentation revision of 2026-11-17: what was applied

Why: record of which proposals of the four audits (A root documents, B `docs/design/`, C study reports, D code against documents) were applied, by whom, and what was left for the owner (decision: owner go "go SAFE" of 2026-11-17).

Nothing was committed or pushed. No code, number, threshold or design decision was changed.

## Applied
- **A (root documents):** 42 rows applied by the group A agent with the Edit tool (README, PROJECT-STATE, KFIAT-DEFINITION-GAP, ECOSYSTEM_PROPOSAL); log in `A-applied.md`.
- **B (`docs/design/`):** about 70 rows applied by the coordinator (the group B agent declined to act on a relayed approval): FROZEN_PARAMETERS (rows 1, 2, 5-12, 14), AUDIT (15-20), ECONOMICS-VERIFICATION (22-31), BACKTESTING (32, 34, 35), PEG-FORMULA-RECOMMENDATION (36-40), EXECUTION_TARGET_ASSESSMENT (42-52), L1_NATIVE_REDUCED_SPEC (53-62), GITHUB-ISSUE-46-COMMENT (63, 64) and -UPDATE (66-69), Immutable-By-Design (71-75), ORACLE-BINDING (76), PHASE_4 (77-80), STRESS-TEST (81, 82, 84), RECOVERY-MODE (85), STABLECOIN-FAILURE (88, 90), REMEASUREMENT (91-94), UNDEFINED-BEHAVIOUR (96, 97).
- **C (study reports):** 44 rows applied by the coordinator (the group C agent declined likewise): W1, W2 and x1b report bodies, status notes on m2/t1/t2/t3/v1, corrections in v2/v3/v4/v5, p1, p4, p5a, p5b, a3, r3, ledger, CODE_MAP, HANDOFF, plus a new `reports/README.md` (scratchpad path note).
- **D (code against documents):** one new file, `contracts/README.md` (the Igra crate is not retained, list of differences with the frozen parameters). No code touched.
- **Retired from the repository, archived outside it** (`~/ENRK_archive/2026-11-17-retired-from-repo/`): `PROJECT_MANIFEST.md` (untracked, superseded) and the pre-correction copy of the W1 report with its two fragments.

## Left for the owner (not applied)
- **Code fixes** (D table): auction floor 85 -> 75, fee split and treasury cap, fee collection, `icr_percent` guard, price 0 in variant A, breaker without resume, `withdraw_collateral` 150% against 200%, harness patch. Listed in `D-code-vs-docs.md`.
- **Wording that needs the owner's validation** (B rows 3, 4, 70, 83, 86, 87: the 250% ICR and the kFIAT 2% statements are not reproduced by the repository's model; 13: price used to convert the 2.5M peg-unit cap; 33: scenario probabilities with no source; 41: "no USD oracle"; 65: issue #46 comment-2 before any posting; 89: causal-link sentence; 98: the harness patch).
- **Issue #46 numbering** (B row 21) needs a look at the posted text on GitHub.
- **C rows 35 and 40:** an inferred date for p3/p4 and the content of the x1b bank files.
- **Commit and push** of the November work.

## Checks run after the edits
- 67 modified or new Markdown files scanned for relative links: no broken link in the documents (two false positives inside the audit working files).
- No wallet address, key or secret in any modified or new document.
- Monolith and Frax comparison files: corrections of B rows 99-103 applied on 2026-11-18 on the owner's go (originals and their copies in `peer-studies-2026-11/` stay identical); FIAT-STABLECOINS-RAPPEL unchanged.
