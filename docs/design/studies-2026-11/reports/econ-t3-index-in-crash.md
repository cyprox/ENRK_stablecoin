# ECON-T3 - Peg-index dynamics inside the crash simulator (TEST only, no design decision)

Every number is a model output. Date 2026-11-11. Repo untouched; nothing read under scratchpad/tn10; no secrets.
Work dir: /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/t3
Tables: tables_t3.txt (T1-T8), cells_t3.csv (1424 main cells). Per-path data: main.pkl, sstar.pkl, cap.pkl (500 paths/cell, paired: path i = seed+i in every cell).

## 0. Key correction to the brief's premise (read first)
The simulator does NOT keep the index flat. In the M2/p3 baseline (default `IndexResponse`: hash-rate r^0.4, fees r^0.6, adoption r^0.3, energy 1.0) the index FALLS with KAS:
at KAS -85% it ends at I = 0.54 (p5-p95 0.48-0.61). Debt value therefore shrinks ~46% in the crash. That correlated fall is what the M2 numbers contain ("orig85" below).
The literal "flat index, I = 1" crash ("flat85") is a different, much worse reference: ENRK p95 loss 13.8% vs 3.0% (r=3%, s=30, S1). Two comparators are reported everywhere:
orig85 = M2 baseline (index falls with KAS); flat85 = I fixed at 1 (the KAS-only crash of the brief). "Index adds" = paired difference vs flat at the same KAS drawdown and length.

## 1. Model changes (stress_fee.py = M2 copy + ECON-T3 block; all default OFF)
Where debt value uses the index (already so in the code via `peg`, now with I(t) from a new source; L = 1): ICR = C*P/(D_units*I) (Vault.icr, _mean_icr); fee k = r/365*I/P (fee on debt VALUE); redemption pays take*I/P collateral (redemption at index value); auction proceeds = collateral value*fill/I (peg units) and the junior waterfall / surplus / reserve draw are in peg units; latent hole = D_units - C*P/I_end at the last day; ledger values income at receipt in peg units.
Added: `index_mode` orig|flat|proc|det (I source), class IndexState, `breaker` none|mb|liq_latch|liq_live, `capacity_mode` units|value, new outputs unbacked_usd_pct (write-offs valued at I of the write-off day + latent hole at end I, % of opening debt VALUE), unbacked_units_pct, breaker_days, peg_max/min.
Index process (proc), assumptions marked A:
- log I = diffusion (annual vol 22% base; 19/26/55% tested; martingale drift) + beta*0.5*(KAS log-return lagged 14 days); beta = rho*sigma_I/sigma_K (sigma_K 4.9%/day). A1: shrink 0.5 as in a4 s4.4 - so the realised KAS-index link is weaker than rho; rho -0.5/+0.5 tested.
- Energy jumps: daily prob 8%/30, sign +/-, size U(15%,40%) on the energy leg, weight 0.3, permanent. Clip [0.1, 5.0] (peg.rs).
- A2: process runs in the crash only (pre-year I = 1), so the calm-year income is index-independent and the pre-crash state is cached.
- det: log-linear ramp to a target multiplier on the last crash day. Named: energy x2 -> I = 1.30 (KAS -50%, 60 d); hash-rate -60% -> I = 0.76 (KAS -70%); 2024 episode I = 1.52, KAS -50%, 97 d; x1.5/x2/x3 at KAS -85% and -70%, 60 d.
Circuit breaker (circuit_breaker.rs: trunc(|I-1|*100) > 10, i.e. |I-1| >= 11%, latched "until manual resolution"): none = never called (as in the code base); mb = wired to I, pauses redemption (mint/burn), liquidations continue; liq_latch = also halts liquidations while latched (the code is silent). liq_live (un-latched) implemented, not run. A3: wiring to I is my assumption.
capacity: as coded the liquidation capacity is 5% of opening debt UNITS/day; `value` = liquidator capital in USD (units capacity = 5%*D0/I), run as sensitivity (T8).
Unchanged M2 setup: -85%/60 d (frozen: floor 75%, redemption on in the crash), 1000 vaults, ICR 200%, D1, 365-day calm pre-year, junior net = (income at receipt - kFIAT write-off)/face, in PEG UNITS (the USD value of the junior face moving with I is not counted).

## 2. Validation (all re-run in this session)
- check.py: extended simulator, features off vs original tests/backtesting copy: 6300 field comparisons x2, 0 differences; cached pre-year == full run (90). check_output.txt "check: OK".
- check_t3.py: index_mode=flat == ORIGINAL simulator with IndexResponse(0,0,0,1) (30240 field comparisons incl. proc vol 0 / det target 1 / breaker idle / capacity value at I=1 / pre_days): 0 differences; shared-snapshot cache (the grid's pre-year reused for other scenarios, stress, breaker, capacity, s) == full run: 80 cases, 0 differences; process differs from flat, breaker trips. "check_t3: OK".
- Reproduces M2: orig85 r=3, s=30, S1: kFIAT mean 8.4, p95 35.7, ENRK p95 3.0, junior net +1.8; r=0: kFIAT 10.0, p95 38.9; s* (h=10%, w=10%) = 29 = M2's 29.
- Previous partial agent's files: copied M2 grid/sens pickles and M2 scripts were deleted (not trusted, not used); stress_fee.py edits and check_t3.py were reviewed line by line, kept, and check_t3 extended.

## 3. Headline results (500 paths, r=3%, s=30%, S1, stress 0.18, breaker never called, KAS -85%; loss in % of opening tranche; unbacked in % of opening debt VALUE)
| index | ENRK p50 | ENRK p95 [CI] | p99 | kFIAT mean | kFIAT p95 | latent p95 | unbacked mean | junior cycle net mean [CI] |
|---|---|---|---|---|---|---|---|---|
| orig85 (M2: I falls to 0.54) | 0.0 | 3.0 [2.2,3.8] | 8.5 | 8.4 | 35.7 | 0.0 | 2.07 | +1.8 [0.9,2.9] |
| flat85 (I = 1) | 0.9 | 13.8 [11.2,15.5] | 20.6 | 25.7 | 54.8 | 0.0 | 10.16 | -15.5 [-16.8,-14.2] |
| p_base vol22 rho0 | 1.1 | 14.1 [11.3,15.5] | 22.3 | 25.9 | 55.0 | 0.0 | 10.42 | -15.8 [-17.1,-14.3] |
| p rho -0.5 / +0.5 | 1.1/1.0 | 13.9/13.9 | 22.8/22.2 | 25.9/25.7 | 55.5/55.4 | 0.0 | 10.48/10.15 | -15.8/-15.5 |
| p vol19 / vol26 | 1.1/1.2 | 13.9/14.5 | 21.3/22.0 | 25.8/26.0 | 55.5/57.0 | 0.0 | 10.32/10.54 | -15.6/-15.9 |
| p vol55 (noisy proxy) | 1.8 | 15.4 [13.7,17.7] | 24.2 | 27.9 | 59.5 | 0.0 | 11.80 | -17.7 [-19.2,-16.2] |
| p vol55 rho -0.5 | 1.9 | 15.5 | 23.7 | 27.5 | 57.7 | 0.0 | 11.83 | -17.3 |
| det x1.5 | 2.2 | 17.3 [14.5,19.1] | 23.7 | 33.0 | 57.8 | 4.2 | 15.33 | -22.8 [-23.9,-21.6] |
| det x2 | 3.6 | 20.0 [16.9,21.9] | 26.2 | 37.3 | 59.7 | 4.9 | 19.63 | -27.2 [-28.3,-26.2] |
| det x3 | 6.0 | 22.8 [19.2,24.6] | 29.0 | 42.8 | 63.3 | 5.1 | 26.55 | -32.7 [-33.6,-31.7] |
Other KAS paths (flat comparator ENRK p95 / unbacked mean): KAS -70% flat 8.0 / 5.26; x1.5 11.3 / 8.98; x2 14.0 / 12.78; x3 17.7 / 19.31; hash-rate -60% (I 0.76) 6.8 / 4.31. KAS -50% flat 5.5 / 4.54; energy x2 (I 1.30) 6.9 / 4.91. KAS -50% 97 d flat 8.7 / 6.15; 2024 episode (I +52%) 13.7 / 12.79, kFIAT p95 63.0, junior net -17.9 (flat -5.5).
r=0, s=0 (no junior, no fee; T1): ENRK p95 orig85 12.0, flat85 25.4, p_base 26.2, x2 31.5, x3 34.3; unbacked mean 1.97 / 8.96 / 9.75 / 18.45 / 25.63. S3 (surplus to reserve) at r=3, s=30: ENRK p95 orig 1.9, flat 12.5, x2 18.4; kFIAT mean 1.6 / 8.5 / 13.2 (T1 block 4). Latent-hole p95 is 0.0 in most cells but the bootstrap CI upper end is 3.4-5.5 (it is a ~5% event: p95 sits on the edge; the deterministic x1.5-x3 cells show 4.2-5.1).

## 4. How much the index adds to the KAS-only crash (paired vs flat, same paths; r=3%, s=30, S1; T2)
- Stochastic index, zero drift (vol 19-26%, any rho, with/without jumps): ENRK mean +0.03 to +0.20 pts, unbacked +0.0 to +0.4 pts, kFIAT mean +0.0 to +0.4 (CIs mostly include 0), p95 unchanged (<= +0.7). Index noise alone is a small effect at 22% vol.
- Noisy proxy vol 55%: ENRK +0.8, kFIAT +2.2 [1.5,3.0], unbacked +1.6 pts; junior net -2.2.
- rho: -0.5 vs +0.5 differ by 0.1-0.3 pts only (the shrink-0.5 link gives a mean final I of 1.12 vs 0.89 at vol 22%): the correlation sign matters little in this specification; this is smaller than the a4 jointsim finding (+1.2 pts for rho -0.5), because a4 had no shrink-0.5 on the crash drift and a different KAS path.
- Deterministic adverse: KAS -85%: x1.5 +1.9 ENRK mean (+3.5 at p95), unbacked +5.2; x2 +3.6, +9.5; x3 +6.2, +16.4; kFIAT mean +7.3 / +11.7 / +17.1; junior net -7.3 / -11.7 / -17.2 pts. KAS -70%: x1.5 +1.0 / +3.7; x2 +2.1 / +7.5; x3 +4.0 / +14.1. 2024 episode: ENRK +1.5, kFIAT mean +12.4, unbacked +6.6. Energy x2 with KAS -50%: ENRK +0.1, unbacked +0.4 (small: I = 1.30 only).
- Hash-rate -60% with KAS -70% (I 0.76): ENRK -0.3, unbacked -0.95 (helps the system; a4 notes it costs ENRK holders in USD: not measured here).
- Versus the M2 baseline (index falling with KAS) the flat index adds +10.8 pts of ENRK p95 loss and +8.1 pts unbacked mean (T2 orig85 row, sign reversed): the M2 loss numbers contain a 46% debt-value cushion.

## 5. Circuit breaker assumptions (T3, r=3%, s=30, S1, stress 0.18)
- Trips (|I-1| >= 11% any day): p_base 42% of paths (vol19 33%, vol26 54%, vol55 97%); all deterministic and orig85 paths 100%. So with a stochastic index at 22% vol a breaker wired to I trips on noise alone in ~4 of 10 crash windows (60 days, includes jumps; no jumps 37%).
- mb (redemption paused, liquidations continue): small effect with a stochastic index (unbacked +0.07 at p_base); with the deterministic rises it hurts: x2 kFIAT mean 37.3 -> 40.3, unbacked 19.6 -> 21.6; x3 26.6 -> 31.8; 2024 episode 12.8 -> 15.6 (loss of the redemption outlet).
- liq_latch (liquidations also halted while latched): the realised ENRK/kFIAT write-offs FALL (x2: ENRK p95 20.0 -> 0.5) because nothing is liquidated, but the loss moves to the latent hole and unbacked debt: x2 latent p95 4.9 -> 46.6, unbacked mean 19.6 -> 86.8 (x3: 196.6, i.e. more than the whole opening debt value, because debt value keeps growing with I while nothing is liquidated); 2024 episode 12.8 -> 29.4; orig85 2.1 -> 18.5; p_vol55 11.8 -> 29.5; p_base 10.4 -> 11.5 (latent p95 12.3). CAUTION: the "junior cycle net" and the "ENRK loss" columns look BETTER under liq_latch (e.g. x2 net -27.2 -> +7.1) only because the hole is not yet written off; read the unbacked/latent columns. Not a benefit.
- Breaker never called vs wired: for the named moderate scenarios (N2 energy x2 / N4 hash-rate) all three assumptions are within 0.5 pts of each other.

## 6. stress_sensitivity (T4; r=3%, s=30, S1 ; ENRK p95 / latent p95 / unbacked mean; breaker none)
| index | 0.18 | 0.25 | 0.28 | 0.32 |
|---|---|---|---|---|
| orig85 | 3.0/0.0/2.1 | 4.0/0.0/2.6 | 2.7/6.4/3.0 | 0.3/21.1/4.0 |
| flat85 | 13.8/0.0/10.2 | 15.4/0.0/11.3 | 11.0/8.2/12.1 | 4.8/33.2/14.5 |
| p_base | 14.1/0.0/10.4 | 15.9/0.0/11.6 | 11.7/8.7/12.3 | 5.4/33.4/14.8 |
| det x2 | 20.0/4.9/19.6 | 21.3/5.0/21.1 | 14.5/9.2/23.2 | 8.7/37.9/31.1 |
| det x3 | 22.8/5.1/26.5 | 24.1/5.1/28.1 | 17.5/9.9/31.9 | 11.3/39.8/45.9 |
| 2024 episode | 13.7/0.1/12.8 | 15.5/0.1/14.1 | 14.7/3.7/14.8 | 11.2/12.8/16.3 |
- p3 F4 is reproduced: the freeze (latent hole) returns between 0.25 and 0.28 and is large at 0.32 for every index case, orig85 included (21%) and flat85 (33%). Realised ENRK p95 loss FALLS at high stress (nothing is liquidated), so on a realised-loss metric alone higher stress looks better; the unbacked mean rises monotonically (10.2 -> 14.5 flat; 19.6 -> 31.1 at x2). At 0.32 the index adds on top: the latent p95 for x2 is 37.9 vs 33.2 flat. liq_latch at stress >= 0.25 for orig85 gives latent 59.5 regardless of stress (liquidations stop at day ~8).
- No-fee/no-junior (T4b) gives the same ordering.

## 7. Junior (kFIAT) cycle net return and equilibrium share (T5, T7)
Net return, % of face, mean [CI]; (s=30, stress 0.18, breaker none):
| index | r=0 S1 | r=3 S1 | r=3 S3 | P(kFIAT loss > 50%) r=3 S1 |
|---|---|---|---|---|
| orig85 | -10.0 [-11.1,-8.9] | +1.8 [0.9,2.9] | +8.6 [8.0,9.2] | 0.6% |
| flat85 | -26.8 [-28.2,-25.4] | -15.5 [-16.8,-14.2] | +1.7 [0.4,3.0] | 7.4% |
| p_base | -28.3 | -15.8 | +1.2 [-0.2,2.6] | 8.0% |
| p vol55 | -30.1 | -17.7 | -1.0 | 13.0% |
| det x1.5 / x2 / x3 | -34.6 / -39.2 / -44.8 | -22.8 / -27.2 / -32.7 | -1.0 / -3.1 / -9.9 | 13.8 / 21.0 / 27.4% |
| 2024 episode | -27.1 | -17.9 | -3.1 | 14.4% |
Under every flat or index-rising case the junior at r=3% S1 loses money on average (M2 headline +1.8 was due to the index falling); S3 (reserve counts as collateral) restores about +17 pts and is the only D/S rule tested in the grid that keeps the mean >= 0 at flat/noise indices; with a +100% index (x2) even S3 is -3.1. The calm-year income (10.0% at r=3, s=30) is unchanged.
Equilibrium s* (D1/S1, r=3%, w=10% crash prob/yr, hurdle h; interpolation on s in {15,30,50}, +-5 pts; T7; breaker none):
| index | h=5% | h=10% | h=20% | h=10%, w=5% / 20% |
|---|---|---|---|---|
| orig85 (M2) | >=50 | 29 | none | 29 / 27 |
| flat85 | 44 | 26 | none | 28 / 22 |
| p_base (rho 0 / -0.5 / +0.5 identical) | 43-44 | 26 | none | 28 / 22 |
| p vol55 | 42 | 26 | none | 28 / 21 |
| det x1.5 | 40 | 25 | none | 27 / 19 |
| det x2 | 37 | 24 | none | 27 / 18 |
| det x3 | 34 | 23 | none | 27 / 16 |
(stress 0.25: 1-2 pts lower.) So in the model the index moves s* down by 3 pts (flat vs M2 baseline) and by 5-6 more pts at x2-x3 (h=5%: 50+ -> 44 -> 34); at w=20% the h=10% s* falls from 27 to 16-22. For h=20% no share is worth holding under any index case (M2: also none for r=3 S1). Under liq_latch s* appears to RISE (e.g. x2: 24 -> 30, h=5%: >=50) - an artefact of unrealised losses (see 5), not a result.

## 8. Capacity sensitivity (T8)
Liquidator capital in USD instead of units: small for N2/N4/p_base (<= 0.4 pts ENRK p95), larger when I is high: x3 ENRK p95 22.8 -> 26.4, unbacked 26.6 -> 33.1; x2 20.0 -> 21.4, 19.6 -> 22.5; 2024 episode 13.7 -> 16.2, latent p95 0.1 -> 3.5. The as-coded units capacity understates the high-I damage.

## 9. Limits and flags
- Pre-year runs at I = 1 (A2): the process is not run through the calm year; calm-year income and the opening ICR distribution are not affected by I. Junior net is in peg units (not USD).
- Drawdown labels are medians (p3 F6): KAS ends at 0.09 for "-85%" in the paths. 60-day crash only; index jumps are permanent and symmetric; "corr" implementation is a lagged-KAS-return term with shrink 0.5 (A1), not a full copula; with that shrink the rho sign has little effect, so the "rho = +-0.5 changes little" result is partly by construction.
- det scenarios put the full index rise in the crash window by assumption; their probability is not modelled (the 2024 history: a4 section 3.3 frequency 4% for index>+5% and KAS>-10% 30-day windows).
- Cells with p95 latent hole 0.0 hide a ~5% tail (CI upper 3.4-5.5): p95 is at the edge of that event class; p99 not printed for latent.
- ENRK loss, kFIAT loss and net return are realised write-offs; they fall when liquidations freeze (high stress, liq_latch). Use unbacked_usd / latent columns for the true hole.
- Persisting M2/p3 flaws apply (permanent sqrt impact, arbitrary liquidation order, passive borrowers, opening ICR floor mass at 153%, capacity 5%/day uncalibrated, S3/D parameters invented). No qgate, reviewer or code-map entry was done (scratch modelling).

## 10. Reproduction (cwd = the work dir; Python stdlib + numpy 2.2.6, `python3 -B`)
    python3 -B check.py                       # ~70 s -> check_output.txt "check: OK"
    python3 -B check_t3.py                    # ~2 min -> check_t3_output.txt "check_t3: OK"
    python3 -B run_t3.py --kind main  --out main.pkl  --paths 500 --procs 8   # 178 index/breaker/stress combos x 8 (r,s,S) = 1424 cells; ~90 min on a loaded 8-core machine
    python3 -B run_t3.py --kind sstar --out sstar.pkl --paths 500 --procs 8    # s in {15,30,50} for s*
    python3 -B run_t3.py --kind cap   --out cap.pkl   --paths 500 --procs 8    # capacity-in-USD sensitivity
    python3 -B analyze_t3.py main.pkl sstar.pkl cap.pkl > tables_t3.txt        # T1-T8 + cells_t3.csv
Files: stress_fee.py (simulator), t3_scen.py (scenarios/grids), run_t3.py, analyze_t3.py, check.py, check_t3.py, stress_test_crash.py (original copy). No background process left.
