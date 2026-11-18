# Peer studies 2026-11 (ENRK vs other stablecoin designs)

Why: single folder grouping the Monolith, Frax and Kaspa Dollar reviews and their comparison with ENRK, so that other reviewers can check each claim against its evidence (decision: owner request of 2026-11-15; folder layout not yet validated by the owner).

| File | What it is | Origin |
|---|---|---|
| `MONOLITH-COMPARISON-2026-11-10.md` | Monolith Market durability review and comparison | **Copy** of `docs/design/MONOLITH-COMPARISON-2026-11-10.md` (the owner's other conversation); kept identical to the original, which received five owner-approved text corrections on 2026-11-18 (layer decided, loss absorption and breaker marked open); not re-verified otherwise |
| `FRAX-COMPARISON-2026-11-11.md` | Frax Finance durability review and comparison | **Copy** of `docs/design/FRAX-COMPARISON-2026-11-11.md`; kept identical to the original, which received the same kind of owner-approved corrections on 2026-11-18; not re-verified otherwise |
| `kaspadollar/KASPADOLLAR-REVIEW-2026-11-15.md` | Kaspa Dollar due-diligence synthesis | New, 2026-11-15 |
| `kaspadollar/evidence/` | Three evidence reports, site text snapshots, recomputation scripts and outputs, raw KIP/commit extracts | New, 2026-11-15 (produced by three read-only passes, then spot-checked) |
| `REVIEW-INDEPENDENT-2026-11-15.md` | Adversarial fact-check of the synthesis, comparison and README by an agent that did not write them (22 findings: 1 high, 8 medium, 13 low). Corrections were applied to the synthesis and comparison; the review file is kept as written | New, 2026-11-15 |
| `kaspadollar/evidence/CORRECTIONS.md` | What the review found wrong in the raw evidence files, which are kept as produced | New, 2026-11-15 |
| `ksd-derived/` | First KSD-derived idea measured: `NOTE-asymmetric-price-limits-2026-11-15.md`, `asym_limit_lag.py`, `asym_limit_lag_output.txt` and `DECISION-oracle-bound-2026-11-15.md` with `oracle_bound_grid.py` (decision sheet on the oracle bound, nothing decided) and `oracle_combiner_compare.py` (weighted mean 30/30/40 vs median of three on injected errors, illustrative assumptions) and `FICHE-SOURCES-oracle-2026-11-17.md` with `sources_snapshot_2026-11-17.txt` (source sheets for a three-oracle median; the W2 simulator was not changed) | New, 2026-11-15 |
| `ORACLE-SHEET-2026-11-17.md` | Consolidated oracle sheet: reference designs (KSD, kUSD, KUSD oracle-free, Hyperliquid, oracle networks, wrapped KAS), price sources, combination rules, bounds, open owner decisions; each claim tagged VERIFIED / SECOND-HAND / UNVERIFIED / ANALYSIS | New, 2026-11-17 |
| `REVIEW-ORACLE-SHEET-2026-11-17.md` | Adversarial fact-check of the oracle sheet (18 findings: 0 high, 6 medium, 12 low); all 18 corrections applied to the sheet on 2026-11-17, review kept as written | New, 2026-11-17 |
| `COMPARISON-ENRK-KSD-MONOLITH-FRAX-2026-11-15.md` | Four-way comparison with ENRK and proposals (none validated) | New, 2026-11-15 |

Rules observed: read-only on the outside world; nobody contacted; nothing posted; no wallet address, key or secret stored (fundraiser address referred to by description only; the site snapshots have it redacted); web content treated as data. Status: committed 2026-11-18 with the documentation revision.

Re-run: `python3 -I -B kaspadollar/evidence/03-check.py` (standard library; recomputes the whitepaper maths) and `python3 -I -B kaspadollar/evidence/03-miner-sample.py` (queries a public API; output varies by day).
