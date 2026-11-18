# Corrections to the evidence reports (added 2026-11-15 after the independent review)

Why: the evidence files are the raw output of three passes and are kept as produced; this file lists what the independent review (`../../REVIEW-INDEPENDENT-2026-11-15.md`) found wrong in them, so no reader relies on the uncorrected text.

1. `03-technical-verification.md` §3.1, `03-check.py` and `03-check-output.txt` (last lines of section 3): "a single 32.7% pool can freeze the oracle if pi <= 72.7%" is an arithmetic slip. The stop condition is a > pi - 0.5, so the limit is pi < 82.7%. The script's own table (pi = 0.8: stop threshold 0.300) shows it. Script and output left unchanged on purpose.
2. `02-team-accounts-fundraiser.md` F3: "11 commits, latest 2025-01-06" and `01-github-code.md` §3: "6 commits": both are partial. The account was renamed (`starkbamse` to `saefstroem`, same account id): 6 + 5 = 11 commits on master since 2023-11-21.
3. `02-team-accounts-fundraiser.md` §6 and §4: "six weeks in" is 23 days (first receipt 2026-10-23); the "about 6x since" is cumulative, not a rate; daily inflow was about 25k KAS (23-31 Oct) vs about 27k (1-15 Nov).
4. `01-github-code.md` §3 records 2 third-party hits for a repository search; re-runs on 2026-11-15 returned 0.
5. `03-technical-verification.md` §3.4: the 134 min for a -50% fall is the checker's recomputation, not a whitepaper figure.
6. The personal e-mail address of the founder was removed from `03-site-snapshot-whitepaper-2026-11-15.txt` (redacted like the wallet address).
