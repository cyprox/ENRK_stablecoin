# P3 - Audit of the ENRK crash simulation model (read-only)

Scratch dir: /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/sim
(copies of the model; helper scripts raw.py, par.py, q4.py, q4b.py, sens.py, pol.py, ss.py, icr.py; raw outputs in out/).
Nothing in the repo or analyse_projet/ was modified. All runs: `python3 -B`, ~0.02 s/run.
Line numbers refer to tests/backtesting/stress_test_crash.py (identical to the scratch copy, md5 verified) unless noted.

## 0. Reproducibility of committed result files
- `python3 -B stress_test_crash.py` output == tests/backtesting/stress_test_results.txt (diff empty). REPRODUCED.
- `python3 -B recovery_mode_analysis.py` == recovery_mode_results.txt (diff empty, 28 s). REPRODUCED.
- NOT reproducible from committed code: the redemption tables of REDEMPTION-ANALYSIS.md (no driver or result file committed;
  `enable_redemption` has no committed script that prints them) and several numbers in STRESS-TEST-CRASH-RESULTS.md (see F2, F3).

## 1. Findings

### IMPORTANT
F1. "kFIAT 2% at -85% with redemption" (FROZEN_PARAMETERS.md:106, REDEMPTION-ANALYSIS.md:83) does not correspond to any statistic
    of the documented configuration (floor 75%, redemption on, ICR 200%, 1000 vaults, -85%):
      paths/seed          kFIAT p50   mean    p95    p99    share of paths with 0 loss
      200  (SEED+0)         6.3      11.3   39.0    -      9%
      500  (SEED+0)         3.1      10.0   38.9   55.4    8%
      1000 (SEED+0)         4.0      10.5   39.5   54.0    8%
      500  (SEED+1e6)       3.5      10.1   40.9   53.9   10%
      500  (SEED+2e6)       5.7      11.3   40.7   59.0    7%
      500  (SEED+3e6)       5.9      10.7   38.5   50.2    5%
    Bootstrap 95% CI on kFIAT p95 (1000 paths): [37.4, 42.7]. Median is seed-sensitive (3.1 to 6.3), mean and p95 are stable.
    The only places where "about 2%" appears: floor 85% + redemption (mean 1.7 at 1000 paths, 200 paths: 1.7; median 0.06-0.1)
    and -95% floor 85% + redemption median 1.7. That is a DIFFERENT config (the one the docs call "freeze"). Best explanation: the doc
    figure comes from an earlier model state or an uncommitted driver. Other numbers of the same table also differ at 200 paths:
      doc: 85/no-red latent 9% med / 46% p95;  repro 16.3 / 44.8     doc: 85/red latent 4% / 32%;  repro 6.5 / 28.1
      doc: 75/red ENRK 0.0 / 5.0, kFIAT 2%;     repro ENRK 0.0 / 4.3, kFIAT med 6.3 mean 11.3 p95 39.0
      doc: 75/no-red ENRK 1.0 / 11.2, kFIAT 14; repro 1.2 / 11.1, kFIAT med 15.5 (close, OK)
      doc -95% 75/red: 0.5 / 10.7, kFIAT 16;    repro 1.3 / 9.9, kFIAT med 19.0
    Recommendation: replace by "kFIAT loss, as % of the kFIAT tranche, -85%, frozen config, 1000 paths: median ~4% (3-6 depending
    on seed), mean ~10%, p95 ~39% (= roughly 12% of total debt), 8% of paths lose nothing". State the statistic and the path count.
    A 2% median/mean figure understates the tail by a factor of ~20 and contradicts the sentence "kFIAT benefits indirectly".
    Commit the driver that produces the redemption tables.

F2. FROZEN_PARAMETERS.md:47 "250% ICR moves ENRK p95 from 11.2% to 11.6% - very slightly worse" is not reproduced: floor 75%, no redemption,
    -85%: 200 paths ICR 200% p95 11.1 [8.2,15.7] vs 250% 9.8 [5.9,13.1]; 1000 paths 9.6 [8.7,11.8] vs 7.9 [6.8,9.8] (250% better).
    The CIs overlap at 200 paths, so the doc claim "worse" is noise at best, and the design reason ("liquidating early beats holding more
    collateral") is not supported. Also note the 245% "minimum ICR for zero ENRK loss" (line 510-524) is a bisection on ONE path
    (seed SEED) over a non-monotone function; STRESS-TEST doc line ~92 recommends 250% from it. Rationale for rejecting 250% needs a rerun
    (cmd: `python3 -B icr.py`).

F3. STRESS-TEST-CRASH-RESULTS.md "Headline results" (lines 46-58) disagrees with the committed stress_test_results.txt: doc kFIAT -85% 5/12/15,
    -95% 3/7/9 vs file 5/10/14 and 3/6/7. Stale table; ENRK/latent rows match.

F4. Frozen-floor conclusion "75% removes the freeze (latent p95 46% -> 0%)" is a knife-edge on an assumed parameter: required discount =
    0.04 + stress_sensitivity*drawdown_so_far (line 328); with the reflexive drawdown (~91% at median) the freeze returns once
    stress_sensitivity > ~0.25 (floor 75%, redemption, -85%, 500 paths):
      stress_sens 0.18: ENRK p95 4.1, kFIAT p95 38.9, latent p95 0.0 | 0.22: 4.7/41.4/0.0 | 0.25: 5.2/43.3/0.0
                  0.28: 3.3/33.4/latent p95 8.3 | 0.32: 0.4/20.0/latent p95 23.4
    The doc says "75% always clears"; it only does under the assumed 0.18. Not tested by any committed sensitivity.

F5. Impact model (lines 447-450): square-root impact applied as PERMANENT, cumulative, with no resilience/decay, on a fixed
    40M KAS daily volume while the system holds ~100M KAS (about 2.5 days of volume; n_vaults is hard-linked to this scale, so
    results are not scale invariant and the docs do not say it). Because sqrt is concave, spreading liquidations over more days (low
    capacity) produces MORE total impact than one big dump, which is the opposite of Almgren-Chriss (permanent impact is linear in
    volume, only temporary impact is sqrt). Fills use the pre-impact price of the day; the buyer's resale is assumed same-day.
    Effect on headline: the nominal -85% is -91% at the median (KAS p50 0.09 in the frozen table); -95% becomes -97%.

F6. Crash label is not the realised drawdown (lines 311-315): the drift is calibrated to the EXPECTED jump (log), so realised exogenous
    ratio = 0.30 * 0.75^k for k jumps (k~Binomial(60,0.04); 8.6% of paths have k=0 -> only -70% before reflexion). The exogenous path
    is otherwise deterministic (no volatility, no bounce), so path diversity is only jump timing. "-85%" is a median-log target.

### MINOR
M1. `redemption_fee` (line 209) is never used (no 1% fee in the redemption pass, lines 345-371); redeemed collateral is not dumped
    (documented); redemption demand is exogenous (documented). Redemption can hit vaults already in auction (line 352-358).
M2. Loss % denominators (line 482-483) are OPENING tranche sizes; redemption shrinks ENRK debt (16-21% redeemed at -85%) so kFIAT's
    share of remaining debt exceeds 30% at runtime (cap is at mint only, acknowledged in FROZEN_PARAMETERS 3). ENRK loss % with and
    without redemption are therefore on different effective bases.
M3. Liquidation order is list order (random), not by ICR or size (line 376, 399): a daily-capacity queue with arbitrary priority.
M4. Latent hole is a day-60 snapshot (line 457-466): depends on crash_days; ENRK loss "0%" at floor 85% is not safety (docs say so).
M5. SEED+i sequential seeds, fixed base seed: every table in every doc uses the same path set, so differences between configs are
    paired (good, common random numbers; jump draws are consumed every day, line 319) but p95 of 200 paths has CI of about +-4 points.
M6. loss_absorption_analysis.py docstring says "from tests/backtesting/" but the file lives in analyse_projet/ (needs stress_test_crash.py beside it).

## 2. Patch review (analyse_projet/loss_absorption_analysis.py)
Verified by reading + runs; `check` passes for waterfall only (50 paths, 5 fields); no invariant test exists for the other policies.
- Deficit allocation (l.57-92): residual (sk, se) after the waterfall is moved to alive vaults, pro rata to CURRENT total debt (or equal per vault).
  Debt is moved, not created: sum of vault debt + written-off is conserved by construction (residual removed = written-off part + pushed part,
  pushed part added to survivors). Token supply invariant holds; the kFIAT cap 30% cannot be broken by it (bk goes to debt_kfiat, be to debt_enrk,
  tranche totals unchanged). OK.
- Cap consistency (l.68-69): cap_left = soc_cap * (surviving debt NOW) - (cumulative pushed since day 0). Inconsistent basis: the stock
  shrinks as vaults die and grows with pushed debt, while soc is a cumulative FLOW that also re-counts the same shortfall each time it is re-pushed
  (soc_pct reaches 57%/79% at p95 for B1). So the nominal "5% cap" binds at roughly 2% of opening debt (observed pushed p95 = 2.2% for B3), and
  the "15% cap" at ~5%. Cap values in the table are therefore NOT percent of any one clear base. Recommend: cap on cumulative pushed / opening debt, or on
  surviving debt at time t versus pushed currently outstanding. Order dependence: vaults later in the loop see the added debt on the same day.
- Counters: soc_pct (l.137) = cumulative pushed / opening debt, can exceed 100% (documented in the print footnote). tax_max (l.134-138) =
  max over vaults of (cumulative added / INITIAL debt of that vault); uses initial debt (ignores redemption shrinkage) and counts re-pushed amounts
  and vaults later liquidated, hence 7,000-109,000% values: this metric is not a borrower burden and should be dropped or redefined (net outstanding added
  debt at end / debt at that time).
- written-off sums: no double count: kw += sk-bk, ew += se-be. But a pushed unit later written off at a survivor's liquidation is counted as loss once there,
  which is correct for token holders. Caveat: the loss % of policy runs are not comparable with waterfall without adding latent (see below).
- kfiat_then_borrowers (l.78-81): kFIAT keeps its whole residual (bk=0); borrowers take only the ENRK-tier shortfall (se) up to cap; the rest hits ENRK.
  Since se>0 implies the kFIAT residual is already total, the name matches "kFIAT, then borrowers, then ENRK". Good. D1 (cap 10%) vs A:
  ENRK p95 3.5 vs 4.1 and kFIAT 40.4 vs 38.9 at -85%.
- share policy (l.75-77): f = min(share, cap_left/total): fine; applies the same fraction to both tranches (so it protects kFIAT as much as ENRK, unlike D).
- Conceptual: pushed debt lands on underwater and soon-to-be-liquidated vaults too (no filter), and consumes liquidation capacity again when re-liquidated
  (daily_liquidation_capacity is counted in debt incl. pushed). In waterfall, written-off debt leaves the system and frees capacity; in B1 it stays and is
  re-auctioned. That, not borrower solvency, is what recreates the freeze. Hence the result is capacity-dependent (table in section 3.4).
- Compare on a common metric: total unbacked = 0.3*kFIAT% + 0.7*ENRK% + latent (% of opening debt), -85%, 500 paths, means: A 3.5 (0.3*10.0+0.7*0.62+0.11);
  B1 3.7 (0.3*2.4+0+2.94). Uncapped carry-over does NOT reduce total loss; it turns realised loss into latent, unrealised hole.

## 3. Tables

### 3.1 frozen --paths 500 (floor 75%, redemption on; columns as the script prints)
 crash  KAS p50  ENRK p50   p95   max  kFIAT p50   p95  latent p95
  -10%    0.80      0.0    0.1   5.1      0.0     17.8     0.0
  -30%    0.51      0.0    0.6   6.6      0.0     24.3     0.0
  -50%    0.33      0.0    2.7   8.2      0.4     34.7     0.0
  -70%    0.17      0.0    2.1  11.4      3.5     32.3     0.0
  -85%    0.09      0.0    4.1  16.2      3.1     38.9     0.0
  -95%    0.03      0.7    8.9  21.3     16.5     49.2     0.0
  Note kFIAT p95 is 17.8% at only -10% (a first-loss tranche hit even by a mild crash) and non-monotone ENRK p95 (2.7 at -50, 2.1 at -70).

### 3.2 absorption --paths 500 (percent; pushed p50/p95 = cumulative shortfall pushed to survivors, % opening debt; "max burden" = tax_max p95, see counters)
 -85%: policy                              ENRK p95  p99  kFIAT p95  latent p95  pushed p50/p95  burden
  A waterfall                                 4.1  10.0     38.9       0.0       0.0/0            0
  B1 borrowers first, no cap                  0.0   0.1     13.9      16.0       3.9/57      10367
  B2 same, equal split                        0.0   0.1     14.3      15.7       3.6/77      73051
  B3 cap 5%                                   4.3  10.2     38.6       0.0       0.5/2           4
  B4 cap 15%                                  4.4  10.4     39.4       0.0       0.9/5          13
  C1 25% share                                4.0  10.1     39.5       0.0       0.3/5         399
  C2 50% share                                3.9  10.3     40.0       0.0       0.7/14       1774
  C3 75% share                                3.0   6.7     33.0       5.9       1.6/31       4636
  D1 kFIAT, borrowers cap 10%, ENRK           3.5   9.7     40.4       0.0       0.0/1           7
  D2 kFIAT, borrowers no cap, ENRK            2.5   4.4     42.4       0.0       0.0/11       3024
 -95%: A 8.9/15.3/49.2/0.0 | B1 0.3/0.6/14.3/23.8 (pushed 23.8/79) | B2 0.2/0.5/14.7/23.5 | B3 9.4/15.9/49.9/0.0 | B4 9.7/16.1/50.3/4.3
       C1 9.0/15.5/50.4/0.0 | C2 8.9/15.8/49.8/5.6 | C3 6.5/11.5/39.5/9.4 | D1 8.5/15.2/50.2/0.0 | D2 4.3/6.1/52.0/6.6
 -50%: A 2.7/5.6/34.7/0.0 | B1 0.0/0.1/11.0/12.2 | B3 2.8/5.9/34.3/0.0 | B4 2.8/6.0/35.0/0.0 | C3 1.4/3.8/26.0/4.8 | D2 1.1/3.4/36.8/0.0
 -70%: A 2.1/6.3/32.3/0.0 | B1 0.0/0.2/6.9/11.8 | B3 2.3/6.8/32.0/0.0 | C3 1.7/4.8/31.6/2.5 | D2 0.9/4.4/35.6/0.0
 (full output: out/abs_0.50.txt .. abs_0.95.txt)

### 3.3 levers --paths 500 (-85%, waterfall)
  kFIAT share 0/15/30/50%:  ENRK p95 12.0/7.7/4.1/0.6; kFIAT p95 0.0/42.8/38.9/31.9; latent 0 in all
  opening ICR 160/180/200/250/300%: ENRK p95 10.7/7.2/4.1/3.3/2.4; kFIAT p95 54.6/46.9/38.9/38.4/33.9 (monotone: more ICR is better here, cf. F2)
  floor 75% no redemption: ENRK 9.3 / p99 16.9 / kFIAT 53.6 / latent 4.0
  floor 85% + redemption: ENRK 0.0 / 0.0 / kFIAT 6.6 / latent p95 26.4
  floor 85% no redemption: ENRK 0.1 / 0.2 / kFIAT 10.0 / latent p95 41.7

### 3.4 Answer to the carry-over claim
Claim: uncapped carry-over onto borrowers brings the freeze back (latent ~16% at p95, -85%), a capped one changes almost nothing.
 - Reproduced: B1 latent p95 16.0 (B2 15.7), vs 0.0 waterfall, at the default capacity 5%/day; B3 (5%) and B4 (15%) are within noise of A
   (kFIAT mean 9.8 / 9.7 vs 10.0, ENRK p95 4.3 / 4.4 vs 4.1, latent mean 0.12 / 0.13 vs 0.11).
 - Capacity dependence (500 paths, -85%, frozen; latent mean / p95; kFIAT mean):
     daily capacity 2.5%: A 0.67/3.6, kFIAT 30.9 | B1 13.79/29.1, kFIAT 0.0 (all paths frozen) | B3 0.75/3.9 | B4 0.92/4.6 | B5 cap 30%: 1.17/5.3
     daily capacity 5%  : A 0.11/0.0, kFIAT 10.0 | B1 2.94/16.0, kFIAT 2.4 | B3 0.12/0.0 | B4 0.13/0.0 | B5 cap 30%: 0.18/0.0
     daily capacity 10% : A 0.02/0.0, kFIAT 4.0  | B1 0.42/0.0, kFIAT 1.5 | B3 0.02/0.0 | B4 0.02/0.0 | B5 0.02/0.0
   So the claim holds in direction, but (a) the B1 freeze is entirely a liquidation-capacity effect (disappears at 10%/day at p95), (b) capped variants
   "change almost nothing" partly because the cap binds at only ~2% of opening debt (see cap inconsistency), i.e. they also relieve kFIAT almost nothing
   (kFIAT mean 10.0 -> 9.8), (c) -95%: even a 15% cap re-opens a small hole (latent p95 4.3 vs 0.0).
 - The share of loss moved is the point: uncapped carry-over does not remove losses (section 2 totals), it makes them latent. Conclusion stands qualitatively; the
   exact "16%" is a function of the 5%/day capacity assumption.

### 3.5 Sensitivity at -85%, frozen config, 500 paths (bootstrap 95% CI on p95 in brackets)
 impact cap/day  KAS p50 | ENRK p50  p95 [CI]        | kFIAT p50 mean  p95 [CI]        | latent p95
 0.04   0.025     0.12   |  0.1   9.3 [7.4,11.1]  | 16.7  18.3  49.7 [46.4,51.1] |  2.6
 0.04   0.05      0.12   |  0.0   1.7 [0.9,2.5]   |  2.3   6.1  31.3 [25.5,33.5] |  0.0
 0.04   0.10      0.12   |  0.0   0.1 [0.0,0.1]   |  0.7   2.4  17.2 [13.5,20.4] |  0.0
 0.08   0.025     0.09   |  2.4  14.0 [11.8,15.7] | 30.6  30.9  55.7 [53.4,57.4] |  3.6
 0.08   0.05      0.09   |  0.0   4.1 [3.2,5.0]   |  3.1  10.0  38.9 [35.9,43.1] |  0.0   <- base
 0.08   0.10      0.09   |  0.0   0.6 [0.3,0.9]   |  1.7   4.0  23.4 [16.2,29.8] |  0.0
 0.16   0.025     0.04   | 11.1  23.9 [22.2,25.0] | 47.9  49.3  66.0 [64.5,67.9] |  5.0
 0.16   0.05      0.06   |  2.2  12.4 [10.8,13.3] | 24.2  30.1  53.4 [48.9,57.3] |  0.0
 0.16   0.10      0.06   |  0.0   3.5 [1.9,5.4]   |  0.7   9.1  34.8 [27.0,41.4] |  0.0
 Reading: ENRK p95 spans 0.1% to 23.9% over the 3x3 grid (a 240x range); base 4.1% sits in a steep region (halving capacity: x3.4, doubling impact: x3.0).
 The two assumptions dominate every conclusion; the model does not support a statement like "ENRK is safe/loses X%" without them.
 Seed ranges (500 paths each, SEED+0 / +1e6 / +2e6): ENRK p95 4.1/3.6/4.2; kFIAT p50 3.1/3.5/5.7; kFIAT mean 10.0/10.1/11.3; kFIAT p95 38.9/40.9/40.7;
 latent p95 0 in all. Seed noise at 500 paths: +-0.5 on ENRK p95, +-1 on kFIAT p95 and kFIAT mean, but up to +-1.3 on kFIAT median.
 stress_sensitivity: see F4 (cliff above ~0.25).

## 4. Commands (cwd = scratch sim dir; model files copied there)
  python3 -B loss_absorption_analysis.py check
  python3 -B loss_absorption_analysis.py levers --paths 500                      # 3.3
  for d in 0.10 0.30 0.50 0.70 0.85 0.95; do python3 -B par.py frozen 500 $d; done   # 3.1 (same numbers as `frozen --paths 500`)
  for d in 0.50 0.70 0.85 0.95; do python3 -B par.py absorption 500 $d; done      # 3.2 (same as `absorption --paths 500`, parallelised)
  python3 -B q4.py ; python3 -B q4b.py          # F1 (1000/500 paths, seed offsets, 200-path 4-config table)
  python3 -B sens.py                            # 3.5 impact x capacity grid + 3 seed ranges
  python3 -B pol.py                             # 3.4 policy x capacity
  python3 -B ss.py                              # F4 stress_sensitivity
  python3 -B icr.py                             # F2 ICR 200 vs 250
  (cd orig; python3 -B stress_test_crash.py | diff - repo/tests/backtesting/stress_test_results.txt)   # section 0
  (cd orig; python3 -B recovery_mode_analysis.py | diff - repo/tests/backtesting/recovery_mode_results.txt)
