# Group A: SAFE proposals applied (2026-11-17)

Row numbers refer to `A-root-docs.md`. Edits made with the Edit tool only; no code touched; no git add/commit/push. Rule 5 (no statement about what is pushed) and rule 2 (no "was X" annotations in living docs) were applied: where my proposal text contained publication statements or history, it was dropped or rewritten.

| Row | File | Result | Note |
|---|---|---|---|
| 1 | README.md | applied | |
| 2 | README.md | applied | also "Igra, not retained" added in the "What is not claimed" section |
| 3 | README.md | applied | Q4 row rewritten, Q5 row added |
| 4 | README.md | applied | "Since September" paragraph, without any publication statement |
| 5 | README.md | applied | |
| 6 | README.md | applied | |
| 7 | README.md | applied | |
| 8 | README.md | applied | |
| 9 | README.md | applied | tree extended; `KFIAT-DEFINITION-GAP.md` added; no "local only" remark (rule 5) |
| 10 | README.md | applied | |
| 11 | README.md | applied | |
| 12 | README.md | applied | |
| 13 | README.md | applied | |
| 14 | README.md | skipped | not checkable |
| 15 | PROJECT-STATE.md | applied | date set to November 17, 2026 |
| 16 | PROJECT-STATE.md | skipped | publication-state statement forbidden by rule 5 |
| 17 | PROJECT-STATE.md | applied | |
| 18 | PROJECT-STATE.md | applied | |
| 19 | PROJECT-STATE.md | applied | |
| 20 | PROJECT-STATE.md | applied | |
| 21 | PROJECT-STATE.md | applied | |
| 22 | PROJECT-STATE.md | applied | preface and Fees row; ICR row reworded per #7 |
| 23 | PROJECT-STATE.md | applied | exact rule-3 wording: one item, "open; fees are never burned (owner decision)"; item 1 rewritten as plain "decided"; the role of the fee reserve is a separate open item (15) because it is a separate owner decision |
| 24 | PROJECT-STATE.md | applied | items 13-17 added; "whether to push" omitted (rule 5); "PROJECT_MANIFEST.md" removed from the defect list (rule 6) |
| 25 | PROJECT-STATE.md | applied | |
| 26 | PROJECT-STATE.md | applied | |
| 27 | PROJECT-STATE.md | applied | index rows for studies-2026-11, peer-studies-2026-11, COMMENT-2; "not yet committed" wording omitted (rule 5) |
| 28 | PROJECT-STATE.md | applied | |
| 29 | PROJECT-STATE.md | applied | |
| 30 | PROJECT-STATE.md | applied | new section "Oracle status (2026-11-17)" |
| 31 | PROJECT-STATE.md | applied | |
| 32 | PROJECT-STATE.md | skipped | NEEDS-OWNER |
| 33 | PROJECT-STATE.md | skipped | not checkable |
| 34-41 | KFIAT-DEFINITION-GAP.md | applied (34, 35, 36, 37, 38, 39, 40) ; 41 not needed | #34 note drops the "not public" remarks; #40 section 10 rewritten without push statements, which also removes the September 15 / 16 date mismatch (#41) |
| 42-51 | PROJECT_MANIFEST.md | skipped | file moved out of the repository (rule 6); no references to it remain in my files (grep) |
| 52 | docs/ENRK_ECOSYSTEM_PROPOSAL.md | applied | status line also states Kaspa L1 decided 2026-11-13 |
| 53 | docs/ENRK_ECOSYSTEM_PROPOSAL.md | applied | three places (Section 5 bullet, Q4 row, 7.1 item 3) |
| 54 | docs/ENRK_ECOSYSTEM_PROPOSAL.md | applied | short note kept before 3.1: history matters because sections 3.2-3.3 keep the original construction; the "max N = 46" qualifier added |
| 55 | docs/ENRK_ECOSYSTEM_PROPOSAL.md | applied | |
| 56 | docs/ENRK_ECOSYSTEM_PROPOSAL.md | applied | |
| 57 | docs/ENRK_ECOSYSTEM_PROPOSAL.md | skipped | NEEDS-OWNER |
| 58 | docs/ENRK_ECOSYSTEM_PROPOSAL.md | applied | date line "revised November 2026" |

Cross-group items (rule 7), in PROJECT-STATE.md:
- "25 reports" -> 29: PROJECT-STATE had no such count; the real count (`ls docs/design/studies-2026-11/reports | wc -l`) is 29, now stated in the document index row. The "25 reports" text itself is in `ECONOMICS-VERIFICATION-2026-11-11.md` §7 (outside my files, not edited).
- "max N = 46": the qualifier (contract form tested on testnet-10, not an L1 limit; N >= 47 refusal outputs not saved) added in both places that mention it.
- Dead burn / Igra fee branch: removed from the open list and the layer paragraph; the same text remains in `FROZEN_PARAMETERS.md` and `L1_NATIVE_REDUCED_SPEC.md` (outside my files).

Counts: 42 rows applied (README 13, PROJECT-STATE 16, KFIAT 7, ecosystem proposal 6), plus 2 extra README edits (KFIAT-DEFINITION-GAP in the tree; Igra mention). 15 rows skipped (#14, #16, #32, #33, #42-#51, #57). #41 became unnecessary (its text was removed by #40).
Not done: nothing else in group A. `git diff --stat` for my files: KFIAT-DEFINITION-GAP.md 34, PROJECT-STATE.md 75, README.md 43, docs/ENRK_ECOSYSTEM_PROPOSAL.md 31 lines changed (4 files, 120 insertions, 63 deletions).
