# ECON-M2 - Crash simulator with stability fee, junior ledger and surplus rules

Findings and trade-offs only; no design decision. Every number is a model output. Date 2026-11-10.
Work dir: /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/m2
Repo untouched (git status: only the pre-existing untracked analyse_projet/). Nothing read under scratchpad/tn10, no secrets.

## 0. What was built

- stress_fee.py = copy of tests/backtesting/stress_test_crash.py with new features, all default OFF.
  check.py: 6300 field comparisons (default and frozen configs, 3 drawdowns, 50 paths) x2: ZERO differences vs the original,
  both with the features off and with r=0 + 365-day pre-period (a calm year is a no-op). Also cached pre-crash snapshot == full run
  (90 cases). Output: check_output.txt ("check: OK").
- Model additions (assumptions are mine, flagged A#):
  - Fee: r/365 per day on debt value (peg units), taken in KAS from vault collateral, not charged on vaults already in auction (A1). Fee KAS is never burned.
  - Pre-crash period: 365 days, KAS price flat, no jumps, no rng. Redemption OFF (A2: base rate 0.2%/day would redeem ~half the ENRK in a year) and
    liquidation market impact OFF (A3: the permanent cumulative impact, p3 F5, would drift a "calm" price down).
  - Ledger: income valued at receipt in peg units at the path's KAS price (junior sells on receipt, no sale impact: A4). Raw KAS is also tracked
    so it can be re-marked at the END price ("held").
  - Fee income is KAS; auction surplus is peg-unit cash (the model sells all collateral; A5).
  - D1 100% junior. D2 20% (A6) to treasury until treasury+reserve value >= 5% of opening debt (A7), then 100% junior. D3 all to reserve.
    S2: surplus goes through the same D rule. S3: surplus to reserve. S1: back to owner (original).
  - Reserve/treasury "counts as collateral" (A8): at each liquidation it tops up the auction proceeds before the ENRK/kFIAT waterfall, i.e. it is
    a layer BELOW kFIAT. At s=0 under D1/D2 the junior share of income goes to a non-absorbing sink.
  - Junior face = opening kFIAT. Net return = (income at receipt - kFIAT write-off) / face. Crash = -85%, floor 75%, redemption on in the crash
    (frozen config of loss_absorption_analysis.py), 60 days, 1000 vaults, ICR 200%.
  - Whole-cycle expectation E_w = (1-w) * calm_year_income + w * (pre-year + crash net), calm year = pre-year income alone. A "cycle"
    (425 days) is treated as one year: unit mismatch, flagged.
- 500 paths per cell (SEED+i, same paths in all cells = paired), 180 main cells (5 r x 4 s x 3 D x 3 S), bootstrap CIs on 500 resamples.

## 1. Headline results (D1/S1, no reserve: pure fee effect), -85%, 500 paths, loss in % of tranche opening size

| s | r% | ENRK p50 | p95 [CI] | p99 | kFIAT p50 | mean | p95 [CI] | latent p95 |
|---|----|----|----|----|----|----|----|----|
| 30 | 0 | 0.0 | 4.1 [3.2,5.1] | 10.0 | 3.1 | 10.0 | 38.9 [34.1,43.9] | 0.0 |
| 30 | 1 | 0.0 | 3.5 [2.9,4.2] | 9.5 | 2.5 | 9.2 | 37.8 [34.1,42.3] | 0.0 |
| 30 | 3 | 0.0 | 3.0 [2.2,3.8] | 8.5 | 1.8 | 8.4 | 35.7 [31.6,40.5] | 0.0 |
| 30 | 5 | 0.0 | 2.2 [1.8,2.5] | 6.9 | 2.8 | 7.4 | 32.2 [25.3,36.4] | 0.0 |
| 15 | 0 / 3 | 0.0 | 7.7 / 6.3 | 15.7 / 13.8 | 5.2 / 3.0 | 12.2 / 10.4 | 42.8 / 40.3 | 0.0 |
| 50 | 0 / 3 | 0.0 | 0.6 / 0.2 | 2.9 / 2.4 | 3.5 / 1.8 | 8.6 / 6.9 | 31.9 / 28.7 | 0.0 |
| 0 | 0 / 3 | 0.7 / 0.4 | 12.0 / 10.6 | 20.5 / 18.3 | - | - | - | 0.0 |

The r=0 rows reproduce the p3-sim.md baseline (kFIAT mean 10.0, p95 38.9, ENRK p95 4.1). Full table: tables_main.txt (T1), cells.csv (all 180 cells).

1. The fee does NOT make any loss metric worse in the model: paired mean kFIAT loss falls by 0.85 to 2.7 points for r=1..5 (all CIs exclude 0),
   latent hole p95 stays 0.0. Scan of all 180 main cells + 162 sensitivity cells: 0 cases where the fee enlarges the junior hole (mean kFIAT loss
   CI above 0, or latent p95 up > 0.5 pt). BUT see flag F-A: this improvement is mostly a model artefact.
2. The junior's economics are dominated by calm-year yield r/s (r=3%, s=30%: 10% of face per year). The crash costs the junior about 8-10% of face on
   average (and 36-40% at p95), so the cycle net at s=30 is: r=0 -10.0, r=1 -5.8, r=2 -2.4, r=3 +1.8, r=5 +8.6 (% of face, mean).
3. D3 (all fee to reserve) leaves the junior with no income: it is never worth holding at any r (E < 0), but the reserve cuts the kFIAT loss
   (r=3: mean 8.4 -> 1.4, p95 35.7 -> 10.6). That reserve effect comes mostly from S3 (see 4).
4. Surplus is large in this model: 14.9% of opening debt at r=0 over the cycle (about 49% of the kFIAT face at s=30), because vaults liquidated
   early in the crash are still at ICR ~150% and the whole collateral is sold. Consequences:
   - S2 (surplus to junior) makes the junior hugely profitable (cycle mean +39.5% at r=0, +56% at r=3, s=30), more than any fee level tested, i.e. the
     junior's return would come mainly from borrowers' liquidation equity, not from the fee. It also pays the junior MORE when more vaults are liquidated
     (a payoff that rises with liquidations; stated as an observation).
   - S3 (surplus to a reserve counting as collateral) builds a reserve of 14.2% of opening debt (r=3) that is used to the extent of 2.2% of debt; it cuts kFIAT mean loss to 1.6
     (vs 8.4 under S1) and ENRK p95 to 1.9 (vs 3.0), with no individual payout. S3 is the strongest loss absorber of the nine D x S combinations.
   - S1 returns this equity to the borrower. S2/S3 take it: borrower cost per cycle = fee (r) + 15-18% of opening debt of surplus forfeited by
     liquidated borrowers (T4). Borrower reaction (topping up, avoiding the 150% line) is not modelled, so this is an upper bound on what is collected.

## 2. Junior net return (pre-year + crash), % of junior face, s=30 (full table: tables_main.txt T3)

| D/S | r% | calm year | cycle mean [CI] | p5 [CI] | p50 | p95 | P(net < -50%) | P(kFIAT loss > 50%) | mean if KAS income held to end |
|---|---|---|---|---|---|---|---|---|---|
| D1/S1 | 0 | 0.0 | -10.0 [-11.3,-9.0] | -38.9 [-43.9,-33.8] | -3.1 | 0.0 | 1.6% | 1.6% | -10.0 |
| D1/S1 | 1 | 3.3 | -5.8 [-6.9,-4.8] | -34.4 [-38.5,-30.4] | 1.0 | 3.4 | 0.6% | 1.2% | -8.6 |
| D1/S1 | 2 | 6.7 | -2.4 [-3.6,-1.4] | -31.6 [-35.5,-25.7] | 4.7 | 6.8 | 0.4% | 1.2% | -8.1 |
| D1/S1 | 3 | 10.0 | 1.8 [0.8,2.8] | -25.5 [-30.2,-19.8] | 8.6 | 10.3 | 0.2% | 0.6% | -6.7 |
| D1/S1 | 5 | 15.6 | 8.6 [7.7,9.5] | -16.1 [-20.5,-9.2] | 13.2 | 16.3 | 0.0% | 0.2% | -4.7 |
| D2/S1 | 3 | 8.0 | 0.5 [-0.6,1.4] | -26.5 | 7.5 | 8.2 | 0.2% | 0.6% | -6.4 |
| D1/S2 | 3 | 10.0 | 56.2 [53.6,58.8] | -1.4 [-9.6,9.2] | 72.8 | 81.1 | 0.0% | 0.6% | 47.7 |
| D1/S3 | 3 | 10.0 | 8.6 [7.9,9.1] | -3.9 [-11.5,5.0] | 10.2 | 10.3 | 0.0% | 0.2% | 0.0 |
| D3/any | 3 | 0.0 | -1.4 to -5.8 | -10.5 to -30.6 | 0 | 0 | 0.0 - 0.0% | - | same |

Note P(net<-50%) is tiny at the base parameters because the model's kFIAT loss rarely exceeds 50%: kFIAT p95 is 36-39% at 30% share. With
the unmeasured parameters at the pessimistic corner (impact 0.16, capacity 2.5%/day) it is 10.6% (r=3, D1/S1) and 44% at r=0.

Wrong-way risk (T6, D1/S1, s=30): the fee KAS is paid in the crash window at only about 14% of the naive flat-price expectation (vaults are liquidated in
the first weeks and stop paying), and if the junior HOLDS the KAS instead of selling at receipt, marking at the end price removes 83-84% of the income
(r=3: cycle mean +1.8% at receipt vs -6.7% held; r=5: +8.6% vs -4.7%). KAS-denominated income is only worth its face if sold on receipt.

## 3. Borrower impact (T4, s=30, D1/S1)

- Fee cost to the borrower = r per year by construction (realised 3.06% of opening debt at r=3 over the cycle: the crash-window part is small).
- Extra liquidations caused by the fee in the 365 calm days (no borrower reaction; top-ups ignored, so an upper bound):
  r <= 3.0%: 0 of 1000; r=3.05%: 111; r=3.5%: 114; r=5%: 124 (123.8 mean over 500 paths); r=7%: 134; r=10%: 153 (diag_liq.txt, 200 paths).
  This is a cliff at r = 3.0% = (opening ICR floor 153% - MCR 150%), not a smooth erosion: see F-A. Total vaults liquidated by the end of the crash is
  unchanged (999.9) for every r: the fee only moves liquidations earlier.
- Where the fee creates early liquidations (r=5%), the surplus of those pre-crash liquidations is 6.1% of opening debt (S2/S3 take it).

## 4. Equilibrium junior share s* (interpolated linearly on s in {15,30,50}; tables_main.txt T7 has all 3 w x 3 h grids)

s* = share at which E_w(s) = h. E falls with s (the fixed fee income is spread over more face), so a larger s* means a larger junior tranche is sustainable.
"none" = E < h already at s=15: no share in the grid is worth holding. ">=50" = E >= h up to s=50. Values below: w = 10%/yr crash probability.

| D/S | h | r=0 | r=1 | r=2 | r=3 | r=5 |
|---|---|---|---|---|---|---|
| D1/S1 | 5% | none | 18 | 36 | >=50 | >=50 |
| D1/S1 | 10% | none | none | 20 | 29 | 46 |
| D1/S1 | 20% | none | none | none | none | 25 |
| D2/S1 | 10% | none | none | none | 25 | 38 |
| D1/S3 | 10% | none | none | 22 | 30 | 48 |
| D1/S2 | 10% | none | 26 | 34 | 45 | >=50 |
| D1/S2 | 20% | none | none | 18 | 25 | >=50 |
| D2/S2 | 10% | none | 22 | 28 | 38 | >=50 |
| D3/any | any | none | none | none | none | none |

- NO equilibrium (junior never worth holding): every D3 cell (no income to the junior); every r=0 cell under S1 and S3; at h=20% every r<=3 under S1/S3
  (only r=5 gives s*~25 for D1/S1, 21 for D2/S1); at h=10% r<=1 under S1/S3.
- Under S2 at r=0 there IS an equilibrium (s*=27 at w=10%, h=5%): the junior is paid by liquidation surplus alone.
- w moves little for S1/S3 (E is mostly the calm yield): D1/S1, h=10%, r=3: s* = 29 at w=5%, 29 at 10%, 27 at 20%. For S2 the crash INCREASES E (more liquidations, more surplus): S2 s* rises with w.
- D2 lowers s* by about 4-8 points relative to D1 at the same r (20% of income diverted to the treasury, cap A7 rarely reached without S3).
- Interpolation on s is coarse (E ~ 1/s is convex): treat s* as +-5 points.
- Which (r, D, S) makes the junior hole larger: none (0/342 cells compared). D3/S1 at r=1..5 and D1/S1 are neutral-to-better on losses but D3 leaves the junior unpaid.

## 5. Sensitivity to the two unmeasured parameters (s=30; tables_sens.txt; 500 paths per cell; base 0.08 / 5%)

D1/S1 cycle mean junior net % of face [CI], kFIAT p95, ENRK p95, by (impact, capacity/day):

| impact | cap | r=0 net | r=3 net | r=5 net | r=3 kFIAT p95 | r=3 ENRK p95 | r=3 P(net<-50%) |
|---|---|---|---|---|---|---|---|
| 0.04 | 2.5% | -18.3 | -6.6 [-8.1,-5.3] | +4.6 | 46.4 | 8.1 | 1.0% |
| 0.04 | 5% | -6.1 | +5.1 [4.2,5.9] | +11.6 | 27.9 | 1.1 | 0 |
| 0.04 | 10% | -2.4 | +8.2 [7.7,8.7] | +14.2 | 14.1 | 0.0 | 0 |
| 0.08 | 2.5% | -30.9 | -19.4 [-20.7,-18.2] | -3.6 | 53.0 | 12.8 | 1.8% |
| 0.08 | 5% | -10.0 | +1.8 [0.7,2.8] | +8.6 | 35.7 | 3.0 | 0.2% |
| 0.08 | 10% | -4.0 | +6.9 [6.2,7.4] | +13.0 | 20.6 | 0.4 | 0 |
| 0.16 | 2.5% | -49.3 | -38.0 [-38.9,-37.4] | -20.3 | 65.1 | 22.6 | 10.6% |
| 0.16 | 5% | -30.1 | -17.9 [-19.0,-16.9] | -4.0 | 49.8 | 10.7 | 1.2% |
| 0.16 | 10% | -9.1 | +2.6 [1.5,3.6] | +9.0 | 30.3 | 1.9 | 0 |

- The SIGN of the junior cycle net at r=3% flips with the unmeasured parameters (-38% to +8%); at r=5% it is -20% to +14%. Conclusions on "worth holding" and on
  s* depend on them, as in p3 section 3.5.
- Across the 9 parameter pairs, the paired effect of the fee on kFIAT mean loss is always negative (-0.4 to -2.1 at r=3; up to -13 at r=5 in the low-capacity corner).
  No cell enlarges the junior hole. S2/S3/D3 combos at r=3 (S2 table in tables_sens.txt) keep the order: S2 largest junior payout, S3/D3 lowest kFIAT loss.
- Not isolated: sensitivity of s* itself (sens runs only s=30).

## 6. Model flaws that these results depend on (p3-sim.md references)

F-A (new, important): the fee's loss reduction is an artefact of the opening population. build_population clips opening ICR at 153% (mass point:
  11.2% of vaults sit exactly at 153% at target ICR 200%). Evidence (diag_floor.txt, 500 paths, r=3 vs r=0, paired change in mean kFIAT loss): target ICR 1.8
  (23% on the floor) -2.25; 2.0 (11%) -1.68; 2.3 (3%) -0.61; 2.6 (0.8%) -0.11. Dose-response with the floor mass; the benefit only exists if the fee runs in the
  pre-year (diag_mech.txt: fee in the crash window only: +0.02, no effect; lowering opening ICR to 1.97 without fee makes losses WORSE by +0.58). The exact
  mechanism is not proven (hypothesis: the floor vaults end the year exactly on the 150% line, are liquidated in the first crash days while price is still high, and
  thereby start the capacity-limited queue earlier). The same mass point creates the liquidation cliff at r = 3.0% (section 3). Treat "the fee reduces losses" as
  NOT established; "the fee does not make losses worse in this model" is what the numbers support.
- p3 F5 (permanent cumulative square-root impact, fixed 40M volume): drives the sensitivity of section 5 and the level of every loss figure; here impact is OFF in the calm
  year (A3) so the pre-year does not drift. No fee-sale pressure is modelled (A4): fee KAS is about 0.01% of daily volume, negligible vs liquidations.
- p3 F6 (crash label is the median log drawdown; realised KAS ratio at the end is 0.09 for "-85%", 0.043-0.115 over the grid) and M4 (latent hole is a day-60 snapshot).
- p3 M2 (loss % use OPENING tranche sizes): kFIAT redeemed/liquidated at par in the calm year (r=5: 12% of vaults) still counts in the junior face, and redemption shrinks ENRK in the crash.
- p3 M3 (liquidation order is arbitrary list order) and F4 (stress_sensitivity 0.18; the freeze returns above ~0.25, not tested here: all latent holes are 0 at base, so
  "fee never enlarges the hole" is conditional on that value).
- New simplifications: flat calm KAS price (calm-year return has no price risk; deterministic except for the population draw); passive borrowers (no top-up, no exit);
  one 425-day cycle counted as one year; 20% / 5% D2 parameters and reserve-first usage invented for modelling and labelled A6-A8 (none is in the project documents);
  junior face not reduced when its vaults are repaid.

## 7. Trade-offs (no recommendation)

- Fee (any r): pays the junior r/s per calm year; costs the borrower r per year; adds no tail loss in the model but triggers a liquidation wave if r exceeds the opening ICR margin over MCR (3 points here).
- D1: the junior gets all income; D2 gives up ~4-8 points of s* to build a treasury (small effect on losses unless S3); D3 protects against loss (largest kFIAT p95 cut) but the junior has no income so no equilibrium exists.
- S1: neutral to protocol, borrower keeps equity. S2: largest junior payout, payout correlated with liquidation volume, borrower forfeits ~15% of debt per cycle. S3: strongest absorber (reserve 14% of debt, mean kFIAT loss 1.6 vs 8.4) but nobody is paid and borrower forfeits the same equity.
- Wrong-way: income paid in KAS is worth ~15% of face if held through the crash; sell-on-receipt assumption (A4) is load-bearing.

## 8. Reproduction (cwd = the work dir; Python stdlib only, `python3 -B`)

    python3 -B check.py                                  # ~60 s, expect "check: OK" (check_output.txt)
    python3 -B run_grid.py --out grid_main.pkl --paths 500      # 180 cells, 6.4 min on 8 cores
    python3 -B analyze.py grid_main.pkl cells.csv                # cells.csv (all cell statistics + p95 CIs)
    python3 -B report.py grid_main.pkl > tables_main.txt         # T1-T7 (T7 = equilibrium)
    ./run_sens.sh && python3 -B report_sens.py > tables_sens.txt # 9 sensitivity pairs, s=30, r in {0,3,5}, ~20 min
    python3 -B diag_mech.py ; python3 -B diag_floor.py ; python3 -B diag_liq.py   # F-A diagnostics

Files: stress_fee.py (simulator), run_grid.py, analyze.py, report.py, report_sens.py, run_sens.sh, check.py, diag_*.py/txt, tables_main.txt, tables_sens.txt, cells.csv,
grid_main.pkl / sens_*.pkl (per-path outputs). Original copies: stress_test_crash.py, loss_absorption_analysis.py (unchanged; stress_fee.py does not use the patching approach, it edits a copy).
Quality-gate note: qgate, one reviewer run and a code-map/handoff entry were NOT done (scratch modelling work, not a lot); module docstrings carry "Why:" without a decision reference (none known).
