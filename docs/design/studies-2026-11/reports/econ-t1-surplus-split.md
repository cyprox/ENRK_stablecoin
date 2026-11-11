# ECON-T1 - Split of the auction surplus (junior phi_j / reserve phi_r / borrower remainder) - TEST, no decision
Date 2026-11-11. Every number is a MODEL OUTPUT of a simulator with known flaws; none is a forecast or a recommendation.
Work dir: /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/t1
Repo untouched (git status shows only pre-existing/other changes, none by this task); nothing read under scratchpad/tn10; no secrets. No background process of this task remains.

## 0. What was done / validated
- A previous agent was stopped mid-run. Its files were NOT trusted: check.py was re-run by me (70 s): original vs extended simulator, 6300 field comparisons x2 (default + frozen config, 3 drawdowns, 50 paths) = 0 differences; cached pre-crash snapshot == full run (90 cases) = 0; SP rule special cases (phi_j,phi_r)=(0,0)/(1,0)/(0,1) == S1/S2(D1)/S3 (60 cases) = 0 differences. "check: OK" (check_output.txt). The earlier t1_main.log contained only BrokenPipe tracebacks (killed run), so the main grid was re-run from scratch; all results below come from my runs. I reviewed run_t1.py/analyze_t1.py/report_t1.py (kept, with small edits: pairs "zero", multi-pickle load, wider pure-fee r range).
- Simulator = stress_fee.py (M2 simulator + new surplus rule "SP": each day's auction surplus -> phi_j credited to the junior as income (same as S2/D1), phi_r to the reserve that tops up auction proceeds BEFORE the ENRK/kFIAT waterfall (same as S3, reserve counts as collateral, assumption A8 of M2), remainder to the vault owner).
- Frozen config: crash -85%, floor 75%, redemption on, ICR 200% opening, 1000 vaults, 60 days, impact 0.08, capacity 5%/day, 365 calm days before (fee runs there, no redemption/impact in calm year: M2 A2/A3). D1 only (all fee income to the junior). 500 paths per cell, path i = SEED+i in EVERY cell (paired), bootstrap 500 resamples (95% CI), quantile = sorted[int(n p)].
- Grid: r in {0,1,2,3}% x s in {0,15,30,50}% x 24 (phi_j,phi_r) pairs (both axes {0,10,25,50,75,100}, phi_j+phi_r<=100: full triangle incl. all mixes) = 384 cells; plus pure fee (0,0) at r in {4,5,7,10} (16 cells; r>3 is beyond the M2 liquidation cliff, see F-A). Sensitivity: impact {0.04,0.08,0.16} x capacity {2.5,5,10}%/day, s=30, r in {0,3}, 12 splits, 500 paths each.
- Borrower-side proxies (my definitions, assumptions B1-B3):
  B1 withheld = (phi_j+phi_r) x surplus. Surplus (all cycle, incl. pre-crash liquidations when r>0) = 14.9% of opening debt at r=0, 16.3% at r=3 (equity at opening ~ 98-100% of debt, so "% of equity" ~ "% of debt": 15.1% at r=0).
  B2 extra annual cost for a borrower who expects a crash with probability w/yr = r + w x withheld(% of debt) [points/yr]; cycle treated as one crash event. It treats the contingent loss as an expected cost (a risk-neutral, fully informed borrower; liquidation timing, top-ups and exit are not modelled).
  B3 junior expected return E_w = (1-w) x calm-year income + w x (pre-year + crash net); cycle (425 d) counted as 1 year (M2 unit mismatch). The same w is used in E_w and in B2.
- Reading T2: "+5 points of withheld surplus cut demand 40-60%" applies to a FLAT yearly cost X. Using T2's semi-elasticity (-9 to -12% of demand per point for the lognormal/exponential sets, ASSUMED distributions) my B2 costs translate (flat-cost equivalent, crude) to: phi=100% -> 0.74/1.49/2.97 pts at w=5/10/20% -> about -7/-15/-30% demand; phi=50% half that; phi=25% -> 0.19/0.37/0.74 pts (-2/-4/-8%). Long-KAS-motive borrowers are ~5x less sensitive. This conversion is a stack of assumptions (T2 flat X vs contingent cost); do not read it as measured.

## 1. Effect of the split on the loss metrics (s=30, r=0 / r=3; full tables: tables_t1.md, t1_cells.csv for all 400 cells)
Losses in % of tranche opening size. res = reserve at end (% of opening debt). wh = surplus withheld (% of opening debt). cost = B2 at w=5/10/20 (pts/yr, r included).
| r | phi_j | phi_r | ENRK p50 / p95 / p99 | kFIAT mean / p95 | latent p95 | junior net mean / p5 / P(<-50%) | res | wh | cost w5/10/20 |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 (S1) | 0.0 / 4.1 / 10.0 | 10.0 / 38.9 | 0.0 | -10.0 / -38.9 / 1.6% | 0 | 0 | 0 |
| 0 | 100 | 0 (S2) | 0.0 / 4.1 / 10.0 | 10.0 / 38.9 | 0.0 | +39.5 / -20.2 / 0.8% | 0 | 14.9 | 0.74/1.49/2.97 |
| 0 | 25 | 0 | same as S1 | 10.0 / 38.9 | 0.0 | +2.3 / -34.0 / 1.0% | 0 | 3.7 | 0.19/0.37/0.74 |
| 0 | 0 | 25 | 0.0 / 4.1 / 9.7 | 6.4 / 34.8 | 0.0 | -6.4 / -34.0 / 1.0% | 2.6 | 3.7 | 0.19/0.37/0.74 |
| 0 | 0 | 50 | 0.0 / 4.0 / 9.2 | 4.4 / 30.0 | 0.0 | -4.4 / -30.0 / 1.0% | 5.7 | 7.4 | 0.37/0.74/1.49 |
| 0 | 0 | 100 (S3) | 0.0 / 2.8 / 8.7 | 2.6 / 22.3 | 0.0 | -2.6 / -21.9 / 0.8% | 12.5 | 14.9 | 0.74/1.49/2.97 |
| 0 | 25 | 25 | 0.0 / 4.1 / 9.7 | 6.4 / 34.8 | 0.0 | +6.0 / -29.8 / 1.0% | 2.6 | 7.4 | 0.37/0.74/1.49 |
| 0 | 50 | 50 | 0.0 / 4.0 / 9.2 | 4.4 / 30.0 | 0.0 | +20.4 / -20.5 / 0.8% | 5.7 | 14.9 | 0.74/1.49/2.97 |
| 3 | 0 | 0 | 0.0 / 3.0 / 8.5 | 8.4 / 35.7 | 0.0 | +1.8 / -25.5 / 0.2% | 0 | 0 | 3.0 flat |
| 3 | 25 | 0 | same | 8.4 / 35.7 | 0.0 | +15.4 / -18.2 / 0.0% | 0 | 4.1 | 3.20/3.41/3.82 |
| 3 | 100 | 0 | same | 8.4 / 35.7 | 0.0 | +56.2 / -1.4 / 0.0% | 0 | 16.3 | 3.82/4.63/6.26 |
| 3 | 0 | 50 | 0.0 / 2.6 / 7.3 | 2.9 / 23.3 | 0.0 | +7.3 / -13.2 / 0.0% | 6.5 | 8.2 | 3.41/3.82/4.63 |
| 3 | 0 | 100 | 0.0 / 1.9 / 7.1 | 1.6 / 14.1 | 0.0 | +8.6 / -3.9 / 0.0% | 14.2 | 16.3 | 3.82/4.63/6.26 |
| 3 | 50 | 50 | 0.0 / 2.6 / 7.3 | 2.9 / 23.3 | 0.0 | +34.5 / -2.0 / 0.0% | 6.5 | 16.3 | 3.82/4.63/6.26 |
Same-r rows reproduce M2 (r=0 S1: kFIAT 10.0/38.9, ENRK p95 4.1; r=3 S2: +56.2 and S3: +8.6 at s=30, kFIAT 1.6).
Findings (paired, 95% CI excludes 0 unless stated):
1. phi_j never changes any loss metric (paired differences exactly 0.00): in this model junior income is paid out, it does not enter the waterfall. It only moves the junior's return, linearly: +0.495 points of mean cycle net per 1 point of phi_j at s=30 (r=0), i.e. 100% of the surplus is worth +49.5 points of face at s=30, +98 at s=15, +29.6 at s=50 (face scales as 1/s).
2. phi_r reduces losses, roughly with diminishing returns in the ENRK tail: at s=30, r=0, phi_r 25/50/100 -> kFIAT mean -3.65/-5.6/-7.4 pts [CI -3.9..-3.3 / -6.1..-5.1 / -8.1..-6.7]; ENRK p95 -0.04/-0.14/-1.31 pts (the first 50% buys almost nothing for ENRK p95; the CI at 25% is [-0.11,-0.01]). ENRK p99 moves little (10.0 -> 8.7 at phi_r=100, r=0). At s=50 the ENRK p95 is already ~0.6 and phi_r adds nothing; at s=15 (ENRK p95 7.7) phi_r=100 gives -2.9 (r=0) / -3.8 (r=3).
3. Latent hole p95 = 0.0 in every base cell (and the paired change is 0): the base config cannot discriminate splits on latent protection. In the sensitivity corners it is nonzero (2.6 / 3.6 / 5.0 at capacity 2.5% and impact 0.04/0.08/0.16) and phi_r=100% does NOT reduce it (same value to 0.1) while the kFIAT mean falls 12-18 pts there: the reserve is exhausted/insufficient where the stranded hole forms, so reserve protects the kFIAT tranche, not the latent day-60 hole (day-60 snapshot, p3 M4).
4. Reserve size at the end (% of opening debt) = phi_r x ~14-16, minus use ~2: 12.5 at phi_r=100,r=0; 14.2 at r=3. It is large relative to the loss it absorbs in the base case (used mean ~2% of debt, M2); idle reserve is not valued in the junior or borrower metrics.
5. A fee on top of a split: r=3 lowers kFIAT mean by 1.7 and ENRK p95 by 1.1 vs r=0 at no split; the effect of r on losses is the M2 artefact F-A (below), not a fee-income effect.

## 2. Borrower side (B1-B2)
- Withheld surplus scales linearly with phi_j+phi_r: 0.149 x (phi_j+phi_r)% of opening debt per cycle at r=0 (0.163 at r=3, more pre-crash liquidations): 3.7 pts at 25%, 7.4 at 50%, 14.9 at 100% of debt (about the same % of the borrowers' opening equity). Only liquidated borrowers pay; in this model ~100% of vaults are liquidated by day 60 at -85%, so the average equals the per-liquidated amount.
- Proxy extra annual cost (r + w x wh): phi=100%: 1.49 pts/yr at w=10% (0.74 at 5%, 2.97 at 20%); phi=50%: 0.74/1.49 (w=10/20); phi=25%: 0.37/0.74. Compared with a pure fee r: phi=100% at w=10% (1.49) costs about as much as r=1.5; phi=25-50% at w<=10% costs less than r=1%; phi=100% at w=20% (2.97) is about r=3.
- A given phi_j+phi_r costs the borrower the same whichever way it is split (cost depends on the sum only); the split decides who is protected. phi_j buys junior return (+0.5 pt of face per point of phi at s=30), phi_r buys loss reduction.
- The cost is contingent: zero for a borrower who is never liquidated, large for one who is, and a borrower who can top up or exit avoids it (not modelled). The proxy is an upper bound for such borrowers and an understatement for a borrower who values the downside more than its expectation.

## 3. Pareto frontier
Junior hurdle: E_w >= h, E_w = (1-w)*calm + w*cycle net (B3). Cost = B2. Grid resolution for r is 1 point, so differences below ~0.5 pt of cost are within the grid step. Full tables (all w): tables_t1.md "Hurdle frontier".
(a) Minimum (r, phi_j, phi_r) clearing h (w=10%), cost in pts/yr, vs the cheapest pure fee (r in 0..10, r>3 with the F-A caveat):
| h | s | cheapest cell | cost | pure fee | cost |
|---|---|---|---|---|---|
| 5 | 15 | r=1, no split | 1.00 | r=1 | 1.00 |
| 5 | 30 | r=1, phi_j=50 | 1.78 | r=2 | 2.00 |
| 5 | 50 | r=3, no split | 3.00 | r=3 | 3.00 |
| 10 | 15 | r=1, phi_j=50 | 1.77 | r=2 | 2.00 |
| 10 | 30 | r=3, phi_j=25 | 3.41 | r=4 | 4.00 |
| 10 | 50 | none with r<=3 (any split) | - | r=7 | 7.00 |
| 20 | 15 | r=3, phi_j=10 | 3.16 | r=4 | 4.00 |
| 20 | 30 | none with r<=3 | - | r=10 | 10.00 |
| 20 | 50 | none | - | none (r<=10) | - |
The cheapest solutions use phi_r = 0 in almost every case (the reserve earns the junior nothing). At w=20% the optimum shifts to lower r with large phi_j (h=5, s=30: r=0, phi_j=75, cost 2.23 vs pure fee r=3, 3.00) and at w=5% to r=1 with phi_j 75 + phi_r 25 (1.78). The split saves 0.2-0.6 pt of cost vs the pure fee at the same hurdle, 1-2 grid steps: the ranking is robust to the sampling CIs (E_w CI half-width about 1 pt) but not to the choice of w, and E_w is sign-sensitive to impact/capacity (section 4). Minimum r by fixed split (table "Minimum r that clears"): at h=10, s=30, w=10%: pure fee 4; phi_j 25-75% -> 3; phi_j 100% -> 2; phi_r-only splits never clear with r<=3.
(b) Protection per unit of extra borrower cost (w=10%, base = same s, r=0, no split; gain in pts per pt of cost): ENRK p95 at s=30: phi_r=100 at r=0: 0.88 (cost 1.49); r=1 + phi_r=100: 0.72; pure fee r=1: 0.64 (the best pure fee); phi_r=75: 0.60. At s=15: phi_r 50-100 at r=0: 1.8-1.95 vs pure fee r=1 0.89. At s=50 the best is the pure fee r=1 (0.23; ENRK p95 is already 0.6). kFIAT mean per unit cost: phi_r small (10%) gives 22 at s=15 and 5-6 at s=30, versus 0.85 for the pure fee: the reserve share is 6-25x cheaper per point of kFIAT loss removed. kFIAT p95: phi_r 10-100% at r=0, s=30: 11-18 per point (pure fee 1.1). Latent hole: 0 gain everywhere in the base config.
(c) Junior and senior both "safe", cheapest cost (w=10%): safe = E10 >= h AND P(net<-50%)<=1% AND ENRK p95 <= X; X=1 or 2 is an ANALYSIS label, not a design threshold. h=5, s=30, X=2: r=3, phi_r=100% (junior still gets calm-year fee income), cost 4.63, ENRK p95 1.9, vs pure fee needing r=7 (cost 7.0; beyond M2's cliff, extrapolated). h=5, s=50: r=3 pure fee (3.0) meets X=1 and 2. h=10 and 20: no split with r<=3 qualifies; the pure fee qualifies at r=7 only (h=10 s=30/50 X=2; h=20 s=30 X=2), cost 7.0. For s=15 nothing qualifies (ENRK p95 6.3-6.8 at r<=3). So in the cells where both are satisfiable at all, a split (reserve plus a fee of 3%) is cheaper in borrower cost than a pure fee, but every pure-fee comparison there relies on r > 3%, i.e. on the region where the model creates a liquidation wave (F-A) and extrapolates the junior income linearly.
(d) Answer to "any split safe at lower cost than a pure stability fee?": Yes for the junior alone (a phi_j of 25-75% saves 0.2-0.6 pt of cost at h=5..20, s=15-30); yes for junior-and-senior at h=5, s=30 (4.63 vs 7.0, with the caveat above); no at h>=10 with X=2 below r=7 and no for s=15. It needs r>0: phi_r/phi_j alone at r=0 never clears h>=10.

## 4. Sensitivity: impact {0.04,0.08,0.16} x capacity {2.5,5,10}%/day (s=30, 500 paths/cell; tables_sens_t1.md has every split)
| impact | cap | r=3 none: ENRK p95 / kF mean / net / E10 | r=3 phi_r=100: dENRK p95 [CI] / dkF mean | r=3 phi_j=100: net / E10 | r=0 phi_j=100: net / E10 |
|---|---|---|---|---|---|
| 0.04 | 2.5 | 8.1 / 16.9 / -6.6 / 8.3 | -0.95 [-2.3,-0.6] / -12.0 | +35.1 / 12.5 | +19.8 / 2.0 |
| 0.04 | 5 | 1.1 / 5.2 / +5.1 / 9.5 | -0.80 / -4.4 | +62.5 / 15.3 | +46.7 / 4.7 |
| 0.04 | 10 | 0.0 / 2.1 / +8.2 / 9.8 | -0.02 / -2.0 | +70.4 / 16.0 | +55.8 / 5.6 |
| 0.08 | 2.5 | 12.8 / 29.6 / -19.4 / 7.1 | -1.04 [-2.35,-0.62] / -18.9 | +12.7 / 10.3 | -1.8 / -0.2 |
| 0.08 | 5 (base) | 3.0 / 8.4 / +1.8 / 9.2 | -1.12 / -6.8 | +56.2 / 14.6 | +39.5 / 3.9 |
| 0.08 | 10 | 0.4 / 3.3 / +6.9 / 9.7 | -0.37 / -3.0 | +67.2 / 15.7 | +52.4 / 5.2 |
| 0.16 | 2.5 | 22.6 / 48.2 / -38.0 / 5.2 | -0.94 / -17.6 | -16.2 / 7.4 | -29.6 / -3.0 |
| 0.16 | 5 | 10.7 / 28.0 / -17.9 / 7.2 | -0.84 / -20.4 | +16.3 / 10.6 | +0.6 / 0.1 |
| 0.16 | 10 | 1.9 / 7.5 / +2.6 / 9.3 | -1.21 / -7.0 | +49.8 / 14.0 | +34.3 / 3.4 |
- Direction of every effect is the same in all 9 pairs: phi_j never changes losses (paired diff 0.00); phi_r lowers kFIAT mean in all cells (by 2 to 20 pts at phi_r=100) and ENRK p95 by 0.0-1.3 pts; the borrower cost depends on the surplus size (5.9% of debt at impact 0.16 / cap 2.5 up to 17.5% at impact 0.04 / cap 10, phi=100, r=0; reason not investigated).
- Sizes change a lot: phi_r=100 cuts kFIAT mean by 2 (cap 10) to 20 pts (impact 0.16, cap 5). The junior's net at phi_j=0 flips sign with parameters (r=3: -38 to +8); with phi_j=100 it flips from +70 to -16 (r=3) and from +56 to -30 (r=0): at impact 0.16 / capacity 2.5% even the whole surplus does not clear h=5 at r=0 (E10 -3.0), where most of the surplus is lost to market impact, the junior is wiped out and the reserve cannot help the latent hole (5.0 -> 5.0).
- Conclusions about WHICH minimal (r, phi) clears a hurdle are therefore conditional on the unmeasured parameters, as in M2 section 5; I did not re-run the full frontier per corner (only the headline splits).

## 5. Model flaws that these findings depend on (p3-sim.md, M2)
- F5 (permanent cumulative sqrt impact, fixed volume): drives the level of the surplus (14.9% of debt) and of all losses; sensitivity above. The size of the withheld surplus, hence the borrower cost B2 and the junior payout of phi_j, depends directly on it: it is large because vaults liquidated early are still at ICR ~150% and the whole collateral is sold (M2).
- F6 (crash label = median log drawdown; realised KAS ratio at the end 0.04-0.115) and the single -85%, 60-day scenario: P(net<-50%) and E_w refer to this scenario only; w is applied as probability of this exact crash. Milder crashes produce less surplus and less reserve use (not run).
- M2 (opening-size denominators; redemption shrinks ENRK), M3 (liquidation order arbitrary), M4 (latent hole = day-60 snapshot; here 0 at base so the "latent protection per unit cost" question has no base-case answer), F4 (stress_sensitivity 0.18; cliff above ~0.25 not tested).
- M2's F-A (new in M2): fee loss reduction partly an artefact of the opening-ICR floor (11% of vaults at exactly 153%) and a liquidation cliff at r=3.0%: affects every r>0 comparison, the r=4..10 pure-fee cells used as the comparator in 3(a),(c), and the claim "r=3 lowers losses".
- Reserve usage rule (reserve tops up proceeds BEFORE the waterfall, below kFIAT), A8, is my assumption from M2 and is not in the design documents; a reserve that covers shortfalls before the waterfall is exactly what phi_r models, but the absence of a cap (A7 not applied for SP) and idle reserve (12-14% of debt) are not costed.
- Not modelled: borrower reaction (top-up/exit/pre-emptive repayment to avoid the surplus loss), liquidator/auction behaviour change when the vault owner no longer receives surplus (a bidder-incentive or gaming channel: owners could liquidate themselves; keepers; anything that makes surplus appear smaller), junior behaviour (income sold at receipt, A4; held KAS income is worth ~15% of face after the crash), no cap on junior payout.
- E_w uses one 425-day cycle as one year (unit mismatch), the same w in cost and return. B2 treats a contingent loss as an expected flat cost.

## 6. What is and is not established (no recommendation)
- Established in the model, with paired CIs: phi_j is loss-neutral and raises junior return linearly; phi_r reduces kFIAT loss strongly and ENRK p95 modestly (large only at s=15 or when capacity is low); both cost the borrower the same 0.149 x phi points of debt per crash cycle; per unit of borrower cost, phi_r buys 6-25x more kFIAT mean reduction than a pure fee and about 1.4-2.2x the ENRK p95 reduction at s=15-30 (0.9 vs 0.64 per pt at s=30); modest phi_j (25-75%) with r=1-3 clears a junior hurdle at 0.2-0.6 pts less cost than the pure fee (within 1-2 grid steps).
- Not established: any ranking that depends on impact/capacity (sign flips), on r>3 (F-A), on w, on how borrowers actually react, on latent hole (zero at base).

## 7. Reproduction (cwd = work dir; python3 stdlib + numpy 2.2.6 already installed)
    cd /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/t1
    python3 -B check.py                                   # ~70 s -> "check: OK" (check_output.txt)
    python3 -B run_t1.py --out t1_main.pkl --paths 500 --rs 0,1,2,3 --ss 0,15,30,50 --pairs full      # 384 cells, ~20 min on 8 cores (CPU shared)
    python3 -B run_t1.py --out t1_fee.pkl  --paths 500 --rs 4,5,7,10 --ss 0,15,30,50 --pairs zero     # pure-fee comparator, ~1 min
    python3 -B analyze_t1.py t1_main.pkl,t1_fee.pkl t1_cells.csv      # all cell statistics (400 rows)
    python3 -B report_t1.py  t1_main.pkl,t1_fee.pkl > tables_t1.md    # tables, paired effects, frontier
    ./run_sens_t1.sh && python3 -B report_sens_t1.py > tables_sens_t1.md   # 9 impact x capacity pairs, ~30 min
Files: stress_fee.py (simulator), run_t1.py, analyze_t1.py, report_t1.py, report_sens_t1.py, run_sens_t1.sh, check.py/check_output.txt, t1_main.pkl, t1_fee.pkl, t1_sens_*.pkl, t1_cells.csv, tables_t1.md, tables_sens_t1.md. (Older M2 files in the dir - grid_main.pkl, cells.csv, tables_main.txt, diag_* - are M2 leftovers copied by the previous agent, unused here.)
Not done: qgate, reviewer run, code map/handoff (scratch modelling, not a lot); module docstrings carry "Why:" without a decision reference (none known). The borrower "delta" column in tables_t1.md (bor delta) is not interpretable as a cost (it includes the minted stablecoin) and is not used.
