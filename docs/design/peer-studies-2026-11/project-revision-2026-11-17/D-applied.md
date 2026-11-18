# Group D - applied actions (2026-11-17)

## Applied (owner go, documentation only)
- Created `contracts/README.md` (new file): Igra crate kept as reference, L1 decision of 2026-11-13, where the L1 work lives, four known differences with file:line, fixes awaiting the owner. No existing file edited, no code touched, nothing built, run or committed.

## Doc-fix rows of D-code-vs-docs.md and the owning group
Group assignment follows the coordinator's statement that the other rows belong to groups A, B or C; I do not know the exact split, so the mapping below is by file and must be confirmed by the coordinator.
- Row 12 (a, b: README.md:12,14 layer wording): README.md - owner group unconfirmed. (c, the contracts README) - done here.
- Row 13 (FROZEN_PARAMETERS.md legend, section 7, section 10 item 1, date): docs/design/FROZEN_PARAMETERS.md - owner group unconfirmed.
- Row 4 (state the withdraw ratio in FROZEN_PARAMETERS section 2): same file; the difference is now listed in contracts/README.md.
- Rows 7, 9 (caveat that tests/enrk_mass.rs fails at N=2 and needs Argent; README structure line, REMEASUREMENT section 8): README.md, REMEASUREMENT-2026-09-15.md. Caveat is stated in contracts/README.md.
- Rows 8, 10, 11 (patch file, PROJECT_MANIFEST.md banner or deletion, empty dirs): harness-binding-fix.patch, PROJECT_MANIFEST.md (gitignored) - owner group unconfirmed.
- Rows 28, 30, 31, 36 (line count, stress_test_crash.py 85% note, README structure list, variant prototype note): README.md, PROJECT-STATE.md - owner group unconfirmed.

## Code rows still awaiting the owner (nothing applied)
1 floor 85 -> 75; 2 fee split and cap; 3 fee denomination; 4 withdraw ratio alignment; 5 icr_percent guards; 6 variant A price bounds; 7 harness binding line; 15 Stability Pool; 16 kaspa_tokens header; 17 duplicate kFIAT cap; 18 auction floor unreachable at expiry; 19 unchecked u64 subtraction and u16 wrap; 20 percent truncation; 21 circuit breaker wiring and resume; 22 repayment trap; 23 close_vault; 24 submit_bid units; 25 SystemTime; 26 unused dependencies; 27 lib.rs.old; 32 stale comments in the Argent sources.
