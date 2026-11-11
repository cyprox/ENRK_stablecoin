# ECON-V6 - Verification of P15 (index fixes, a-f) and P3 (kFIAT denomination). TEST only, no design decision.
Date 2026-11-11. Repo untouched, nothing read under scratchpad/tn10, no secrets. Every number is a model or data output; ASSUMED items are labelled.
Work dir: SP/econ/v6 = /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/v6
Files: stress_fee.py (simulator, t3 copy + V6 block, all new options default OFF), v6_scen.py, v6_run.py, analyze_v6.py, tables_v6.txt (all sim tables), v6.pkl (322 cells x 1000 paired paths), hist6.py -> hist6_out.txt + hist6.json (history tables), check*.py + outputs.

## 0. Validation (re-run on the FINAL code, this session)
- check.py: extended simulator vs original, 6300 fields x2 + 90 cache checks: 0 differences ("check: OK").
- check_t3.py: flat == original with IndexResponse(0,0,0,1) (30240 fields), cache and snapshot checks 90: 0 differences ("check_t3: OK").
- check_v6.py (new): 7848 fields, 0 differences: (i) the new breaker spec idx/red/latch == old `mb`, idx/liq/latch == `liq_latch`, idx/liq/live == `liq_live`; (ii) kfiat_mode A2 changes no loss field; (iii) shaping options inert at defaults; (iv) mint-only == no breaker; clip/slope/rate-limit give exact published values (1.5, 1.5, 1.005^60, 0.8).
- Headline cells: 1000 paired paths (path i = seed+i in every cell), bootstrap 95% CI (500 resamples). Crash = ECON-T3 (KAS -85%/60 d, frozen floor 75%, redemption on, ICR 200%, 1000 vaults, r=3%, s=30%, S1, stress 0.18). Pre-year at I=1 (A2 of T3). Junior net in peg units.
- Processes: 2 workers for the run, none left. Not done: qgate, reviewer, code map (scratch modelling).

## 1. Verdicts (summary)
| Item | Verdict | One line |
|---|---|---|
| (a) define L | CONFIRMED as a necessary fix; NEEDS DECISION on the option | L is undefined in code; ICR = C*P/(D*L*I). Options differ by orders of magnitude in index risk (vol 4% to 23%+) |
| (b) baseline convention | CONFIRMED that it matters; it changes the sign of the index effect | launch / full-mean / trailing-365 / fixed 2024-01-01 give different histories, holder returns and ICR paths |
| (c) energy source | PARTLY CONFIRMED | IMF index = commodity-volatile (30%), US electricity/CPI = near-stable (2-4%); cadence monthly at best; a Kaspa-native proxy is KAS-correlated (0.57) |
| (d) fee and adoption legs | CONFIRMED unusable as measured; removal tested | removing them is a re-weighting decision; replacements measurable today are weak |
| (e) breaker rewrite | CONFIRMED as coded is harmful if it can pause liquidations; NEEDS DECISION on trigger | pausing liquidations is the single worst lever in every adverse case |
| (f) clip / bounded move | PARTLY CONFIRMED | caps lower the CDP loss only when binding, and cost holders the upside; rate limit helps on rises, hurts on falls |
| P3 A1 vs A2 | A2 == A1 on all aggregates by construction (0 differences); A2 borrower-relief variant inconsistent | differences are distributional and operational, not in the four metrics |

## 2. (a) Definition of L
Code: peg.rs fixes only a dimensionless I in [0.1,5]; no module derives a USD price for 1 ENRK (a4 s1.1). ICR = C*P_KAS/(D*L*I); d ln ICR = r_KAS - r_I (L constant).
Options tested (history, fullmean baseline, hist6_out.txt section a; sim, tables_v6.txt BASE). Touch = share of 180-day windows from 200% ICR that touch 150%.
| option | index vol/yr | ICR touch 180d (KAS-only 63%) | P(ICR<100% in 180d) (KAS-only 28%) | holder 365d USD return p5 / med / p95 | sim: ENRK p95 / unbacked mean at KAS -85% |
|---|---|---|---|---|---|
| L1 as coded, I drifts (hashrate+energy legs) | 23% | 67% | 31% | -46% / +16% / +145% | p_base 14.5 / 10.6 |
| L1b same with the noisy fee/adoption proxies | 104% | 80% | 58% | -57% / +40% / +237% | p_vol55 15.4 / 11.9 |
| L2a USD-anchored basket = US retail electricity | 4% | 65% | 30% | +3% / +5% / +7% | p_anch 14.5 / 10.5 |
| L2b anchored = IMF energy index | 30% | 66% | 33% | -17% / -3% / +63% | p_comm 14.5 / 10.9 |
| L3 unit fixed at 1 USD (index not in ICR) | 0% | 63% | 28% | 0 | flat85 14.5 / 10.5 |
Reading: (1) with L1 the holder's USD value is the index (sign not determined by the design, a4 s5); borrowers carry the opposite position; (2) an anchored basket with low vol (electricity, CPI) is, for the CDP, almost the same as a fixed USD unit: the sim shows no measurable difference among flat85, p_anch and p_base at zero drift (ENRK p95 14.5 in all three; CIs overlap); the damage comes from DRIFT in the adverse direction, not from noise at 5-22% vol (unbacked mean x1.5 15.6, x2 19.9, x3 26.8 vs flat 10.5); (3) the index FALLING with KAS (M2 baseline, orig85: unbacked 2.2) or a fixed falling index (x0.6: 5.5) is a large cushion; so the undefined L hides a 46% cushion that exists only if the index is pro-cyclical (T3).
Unverified: L options 2a-2c are history-only for holders; borrower mint demand under each L is not modelled.

## 3. (b) Baseline convention (a4 data, 2023-03-21..2026-11-10, proxies F=A=1; "full" = noisy proxies)
| baseline | idx vol | share of days outside +-11% | index min..max | touch 90/180/365 d (KAS-only 48/63/74) | P(ICR<100%) 180d (KAS-only 28%) | ICR on 2024-11-04 for the 2024-07-31 vault (KAS-only 101%) | holder 365d p5/med/p95 |
|---|---|---|---|---|---|---|---|
| launch (first 7 d) | 19% | 99% | 0.99..2.71 | 49/65/77 | 28% | 101% | -2% / 0% / +91% |
| full-sample mean (hindsight) | 23% | 67% | 0.61..1.75 | 51/67/83 | 31% | 66% | -46% / +16% / +145% |
| trailing 365 d | 26% | 65% | 0.76..2.24 | 52/73/96 | 24% | 110% | -62% / -42% / +24% |
| fixed external date 2024-01-01 | 23% | 96% | 0.62..2.62 | 55/72/85 | 36% | 101% | -29% / +25% / +262% |
Findings: the baseline decides the SIGN of the index effect on the same vault (66% vs 110% on 2024-11-04), the share of days the coded breaker would be tripped (65-99%), and whether holders lose 42% (trailing) or gain 16-25% (fixed or mean) in a median year. The trailing baseline reduces the index effect during the 2024 hashrate surge (it absorbs it) but makes 80% of 365-day holder returns negative after the decline. Touch shares differ from the KAS-only by -6 to +9 pts (HE); with noisy proxies by up to +17 pts. A launch baseline is not hindsight-free in practice here: hashrate grew x615 so a launch hash-rate component sits at the 5.0 clip most of the time (a4 s0.6).
Verdict: CONFIRMED that no convention is neutral; the choice moves who pays. UNTESTABLE HERE: which convention a real launch date would use (the dataset starts 2023-03).

## 4. (c) Energy source (monthly returns 2023-03..2026-10; hist6_out.txt section c)
| source | vol/yr | corr with KAS (monthly / 30d) | max monthly move | cadence | publication lag (ASSUMED typical) |
|---|---|---|---|---|---|
| IMF energy index (FRED PNRGINDEXM) | 30% | 0.15 / 0.09 | +52% / -14% | monthly | ~1 month |
| US retail electricity (APU000072610) | 4% | 0.10 / -0.10 | +4% / -3% | monthly | 2-6 weeks |
| US CPI electricity | 2% | 0.09 / 0.05 | +2% / -1% | monthly | 2-6 weeks |
| US PPI electric power | 10% | 0.08 / -0.11 | +8% / -8% | monthly | ~1.5 months |
| Henry Hub gas (daily) | 86% | 0.00 / 0.01 | +86% / -58% | daily | 1 day |
| EU gas (monthly) | 46% | 0.11 / 0.11 | +58% / -27% | monthly | ~1 month |
| Kaspa-native: break-even price K*emission/H | 144% | 0.57 / 0.52 | +59% / -85% | every block/day | none (needs the KAS oracle) |
| Kaspa-native: network bill H x US elec | 119% | 0.19 / 0.24 | x5.3 | daily + monthly external | ~1 month |
What an on-chain oracle could realistically publish: the covenant oracle (L1 spec s2) is a signer-controlled sweep (OP_CHECKSIG) of price UTXOs; an energy value would be one more signed number, so trust = the signer(s) plus the off-chain source. Sources of record are monthly (IMF, BLS electricity), so a realistic cadence is once a month with a stated validity; the daily sources (gas) are too volatile (86%) and a poor proxy for electricity. Cost: not measured here (no L1 fee model run); p4 notes one round uses 99.6-99.93% of a block's transient mass for N~640, but a monthly value can ride a rare round. A Kaspa-native proxy removes the external trust but is a KAS-price derivative (corr 0.57): it would make the index pro-cyclical with KAS, which cuts CDP risk and hurts holders. A hashrate x electricity-price "network bill" is mostly the hashrate leg again (vol 119%, hash-rate dominated).
Verdict PARTLY CONFIRMED: the stable choice (US electricity/CPI, vol 2-4%) makes the 30% energy leg almost a constant; the IMF index makes it a 30%-vol commodity leg. Which is intended is a decision. Untested: IEA/GlobalPetrolPrices/ENTSO-E (keys or licences), industrial global electricity.

## 5. (d) Fee and adoption legs (fullmean baseline; hist6_out.txt section d)
Coded fee leg: 100-122 sompi/gram, ~0.002 KAS per standard tx vs the 0.1 KAS baseline gives 0.02-0.1, clipped to 0.1: a constant 0.1 (a4). That shifts the index by -0.18 against F=1 and adds no information. Adoption: undefined in code; the proxy is spam-polluted.
| variant | vol | corr with KAS (wk / 30d) | outside +-11% | touch 180d (KAS 63%) | P(<100%) 180d (KAS 28%) | holder p5 / med / p95 |
|---|---|---|---|---|---|---|
| V0 coded 4/3/2/1 with noisy tx7d, addr30d | 104% | 0.07 / 0.01 | 87% | 80% | 58% | -57 / +40 / +237 |
| V1 F=A=1 (hold flat) | 23% | 0.04 / 0.14 | 67% | 67% | 31% | -46 / +16 / +145 |
| V2 hashrate+energy re-weighted .571/.429 | 32% | 0.04 / 0.15 | 79% | 68% | 36% | -56 / +29 / +263 |
| V7 F,A = 30d rolling median | 65% | -0.01 / 0.04 | 91% | 72% | 52% | -56 / +37 / +228 |
| V8 H (30d median) + E re-weighted | 24% | 0.00 / 0.08 | 78% | 68% | 36% | -56 / +30 / +267 |
| V9 .4 H + .3 E + .3 KAS 90d mean | 26% | 0.11 / 0.27 | 84% | 70% | 29% | -58 / +8 / +241 |
| V5 energy only (IMF) | 30% | 0.03 / 0.09 | 35% | 66% | 33% | -17 / -3 / +63 |
| V4 hashrate only | 47% | 0.06 / 0.17 | 96% | 72% | 39% | -68 / +104 / +2011 |
Findings: removing the polluted legs cuts index vol from 104% to 23-32% and the extra ICR<100% share from +30 pts to +3..+8 pts; re-weighting to hashrate+energy raises vol (more weight on the 74%-vol hashrate) and widens the holder tails; the only measurable KAS-linked replacement (V9) raises the correlation with KAS (0.27 at 30 d) and brings P(ICR<100) back to the KAS-only level, at the cost of a lower holder median. No measurable replacement for fees exists keylessly (a4: no fee-history endpoint). Verdict: CONFIRMED the two legs are unusable as specified; the rest is a decision. Untested: a real Kaspa fee series (not obtainable), mass-based activity measures.

## 6. (e) Breaker rewrite (simulator; tables_v6.txt BREAKER; r=3%, s=30, S1; 1000 paths; delta = paired vs no breaker)
Trigger rates (share of paths that ever pause): coded |I-1|>=11%: calm index noise vol 22% -> 41% of 60-day windows, vol 55% -> 97%, any adverse ramp -> 100%. Hysteresis (trip 25%, release 15%; ASSUMED values): 2% under vol 22%, 45% under vol 55%, 100% when the index rises x1.5/x2. Market-price trigger (ENRK price = I x min(1, system CR) x AR(1) noise sd 1.5%, threshold 5%; ASSUMED): 18-20% false positives in calm windows (noise 3.3 sigma plus KAS jumps), 71-75% in the flat -85% crash, first day 12-13. Oracle-freshness only (1%/day outage, mean 1.5 d; ASSUMED): 45% of 60-day windows, independent of the index.
Unbacked mean (% opening debt value) and ENRK p95, breaker action vs none:
| scenario | none | coded latched, redemption paused | coded latched, liquidations halted | hysteresis, liq halted | market 5% live, liq halted | freshness latched, liq halted | freshness live, liq halted |
|---|---|---|---|---|---|---|---|
| calm index vol 22% | 2.78 / 3.8 | 2.89 | 2.73 | 2.77 | 2.34 | 2.57 | 2.82 |
| calm vol 55% | 3.08 / 4.5 | 3.89 (p95 6.0) | 2.84 (latent p95 12.3) | 3.04 | 2.64 | 2.96 | 3.14 |
| flat -85% | 10.46 / 14.5 | 10.46 | 10.46 | 10.46 | 18.78 (latent p95 43.6) | 16.20 (latent 57.2) | 10.82 |
| p_base | 10.63 | 10.68 | 11.51 (latent 9.7) | 10.63 | 19.46 | 16.49 | 11.00 |
| index x1.5 | 15.64 / 17.5 | 15.75 | 28.43 (latent 15.7) | 15.64 | 41.94 | 25.81 | 16.17 |
| index x2 | 19.90 / 20.1 | 21.88 | 86.82 (latent 46.6) | 19.93 | 67.39 | 34.64 | 20.59 |
| 2024 episode (I x1.52, KAS -50%, 97 d) | 12.91 / 13.5 | 15.70 | 27.76 | 14.58 | 21.26 | 20.76 | 13.11 |
Findings (model): (1) halting liquidations (any trigger) transfers the crash into the latent hole: x2 unbacked 19.9 -> 86.8 (coded), 67.4 (market trigger); realised ENRK/kFIAT losses look better (ENRK p95 20.1 -> 0.5) only because nothing is written off: read the unbacked and latent columns. (2) Pausing redemption costs +0.1 to +2.8 pts unbacked in adverse cases (loss of the redemption outlet), +0.8 under noisy vol 55%. (3) Pause mint only: zero effect on every loss metric BY CONSTRUCTION (the crash model has no new mint); its cost or benefit is untestable here. (4) Hysteresis removes the noise trips at vol 22% (41% -> 2%) and, with mint/redemption actions, adds at most +0.55 in the 2024 episode; with liquidation halt it still costs +1.67 there. (5) The market-price trigger is a late detector (day 12-13 in flat -85%, i.e. already in distress) and is not index-driven; wired to a liquidation halt it is as damaging as the coded rule. (6) Freshness-only with a live (un-latched) pause costs +0.4 to +0.7; latched with liquidation halt +5.7 to +14.7: the coded "6 h oracle downtime pauses until manual resolution" is a fragility in itself.
Verdict: CONFIRMED that the coded breaker (index deviation, latched, may pause liquidations) is net harmful; the safest tested set is: act on mint only, or on redemption with hysteresis, never on liquidations. NEEDS DECISION. Breaker wired to I is my assumption (A3 of T3): the code calls it nowhere.

## 7. (f) Clip bounds and bounded move per period (sim, tables_v6.txt SHAPING; r=3%, s=30, S1; delta unbacked paired vs frozen [0.1,5]; holder dI = mean final index change)
| scenario | hi 2.0 | hi 1.5 | hi 1.25 | hi 1.10 | slope .5 above 1 | step .5%/day | step .25%/day |
|---|---|---|---|---|---|---|---|
| x1.5 (frozen unbacked 15.64) | 0 / 0 | 0 / 0 | -0.07 / -0.25 | -0.50 / -0.40 | -2.64 / -0.25 | -1.45 / -0.15 | -3.38 / -0.34 |
| x2 (19.90) | 0 / 0 | -0.16 / -0.50 | -0.24 / -0.75 | -3.79 / -0.90 | -4.88 / -0.50 | -5.72 / -0.65 | -7.65 / -0.84 |
| x3 (26.76) | -0.33 / -1.0 | -0.50 / -1.5 | -3.19 / -1.75 | -10.24 / -1.90 | -8.49 / -1.0 | -12.58 / -1.65 | -14.50 / -1.84 |
| 2024 episode (12.91) | 0 / 0 | -0.01 / -0.02 | -0.73 / -0.27 | -3.09 / -0.42 | -4.08 / -0.26 | 0 / 0 | -3.66 / -0.25 |
| index falls x0.6 (5.54) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | +1.73 / +0.14 | +3.25 / +0.26 |
(cell = delta unbacked pts / holder dI in index units; negative unbacked = safer.)
Findings: the frozen upper clip 5.0 is irrelevant in all cases. A cap works only if it binds before the index gets there: hi 1.25 lowers x2 unbacked by only 0.24 because the ENRK p95 is driven by the path of the index through the crash, not the final value; a tight cap 1.10 lowers it by 3.8 (20%) but removes 0.9 of index value from holders; the bounded move per day (0.25%/day) gives -7.65 (-38%) at x2 but the published index lags 0.84 below the market value of the basket, and on a FALLING index it hurts the CDP (x0.6: +3.25, because debt value stays high). Lower clip: no gain. History (hist6 section f): hi 1.25 cuts the holder p95 365-day return from +145% to +88% and the p5 from -46% to -29%, median unchanged; step .5%/day changes index vol 23% -> 14% with 3% rms gap; touch shares move by <= 1 pt (history is dominated by KAS).
Verdict PARTLY CONFIRMED: both tools reduce the "index up, KAS down" damage, at the explicit price of holder exposure; neither removes it. The clip bounds interact with the breaker: any breaker threshold below the clip makes the clip moot.

## 8. What makes a CDP structurally safer against "index up while KAS down", and the cost
Ranked by unbacked mean in the KAS -85% crash with index x2 (frozen 19.9; flat/USD-fixed 10.5):
1. Debt fixed in USD equivalents (L3, index not used in ICR): 10.5. Cost to ENRK holders: all index exposure (the holder's USD value is constant; whether that is a cost depends on whether the index exposure was wanted). Also removes the energy-hedge purpose of the design (an owner decision, not a modelling matter).
2. Index move per day <= 0.25%: 12.3 at x2 (-7.65), published index lags a 2x basket by 0.84; cost: holders receive the rise late and the lag persists, and a fall is also slowed (+3.25 unbacked at x0.6).
3. Slope 0.5 above 1 (debt rises half as fast): 15.0 (-4.9); cost: holders get half of any rise (-0.50 at x2).
4. Cap at 1.10: 16.1 (-3.8); cost -0.90 at x2, zero below the cap; cap at 1.25 or 1.5: -0.2; useless at x2.
5. Not halting liquidations (breaker): avoids +47 to +67 (market or coded trigger).
6. Option noted but not simulated: junior (kFIAT) share and S3 (surplus kept as reserve) change the holder loss, not the index exposure (T1/T3).
Structural reading: the dangerous direction is only the rise (a fall helps the CDP); an asymmetric rule (slow up, immediate down) is the minimal cost design in these tests; the cost is borne by holders as a lagged or truncated upside. Probability of the adverse case in history: index up >5% with KAS down >10% in 30-day windows 1-7% (HE) to 7-11% (noisy); 20-29% index-up/KAS-down at any size (a4).

## 9. P3: kFIAT denomination, A1 (fixed face in peg units) vs A2 (monotone write-down index driven by uncovered kFIAT)
A2 implemented as accounting in the simulator: W = 1 - uncovered/opening kFIAT face (cumulative form, monotone), vault debt stays at face (p5b recommendation); a second form W = alive kFIAT debt/(alive + uncovered) is also logged.
| scenario (r=3%, s=30, S1, 1000 paths) | mode | kFIAT loss mean / p95 | ENRK p95 | latent p95 | junior net | W end mean (p5 / p50) | P(W<0.5) |
|---|---|---|---|---|---|---|---|
| flat -85% | A1 / A2 | 26.5 / 55.2 | 14.5 | 0.0 | -16.3 | 0.74 (0.45 / 0.82) | 7% |
| index x1.5 | A1 / A2 | 33.7 / 58.6 | 17.5 | 0.0 (CI up 4.5) | -23.6 | 0.66 (0.42 / 0.74) | 15% |
| index x2 | A1 / A2 | 38.1 / 59.9 | 20.1 | 0.0 (CI up 4.9) | -27.9 | 0.62 (0.40 / 0.69) | 22% |
| 2024 episode | A1 / A2 | 29.1 / 62.7 | 13.5 | 0.0 | -18.4 | 0.71 (0.38 / 0.79) | 16% |
| stochastic p_base | A1 / A2 | 26.5 / 56.3 | 14.5 | 0.0 | -16.4 | 0.73 | 9% |
Max absolute difference A2 - A1 over all paths and the five loss fields, all 16 cells: 0 (exactly). s=15 and s=50: same; S3 (reserve counts): same (kFIAT loss x2 14.2, junior net -4.1).
Findings: (1) Both forms book the same total shortfall; the index is a bookkeeping way to spread the same loss over all holders; no aggregate metric differs. (2) Making borrowers' kFIAT debt shrink with W ("borrower relief") is inconsistent: the u uncovered tokens would remain in supply valued at W*u, an unbacked remainder, and iterating the relief drives W to 0; it was not simulated for that reason. (3) The ratio form W = alive/(alive+uncovered) collapses to ~0 as healthy vaults repay (W~0.01-0.05 mean at the end): the definition of the index denominator matters; with the cumulative form W is stable. (4) Operationally A2 needs global state (p5b: UNVERIFIED on UTXO), and borrowers repaying face while holders are owed W creates an excess (1-W) per face repaid with no assigned destination: a design question A1 does not have. (5) Both forms leave the same hole: the realised-loss metrics understate the true hole when W is driven only by realised shortfalls (latent p95 is 0.0 but its CI upper end is 4.5-5.1 at x1.5-x3).
Verdict: A1 and A2 are CONFIRMED equivalent for the four metrics in this model; the choice rests on non-modelled factors (holders' quote-ability, state, who gets the excess). NEEDS DECISION. Adverse junior outcome (A1 or A2): net -16 to -28 pts of face at r=3% under flat to x2; P(kFIAT loss >50%) 7-22%.

## 10. Not finished / limits
- Mint-only pause cannot be tested (no minting in the crash model); effect on holders of a mint pause is not measured. Oracle publication cost on L1 not measured; the fee/adoption replacement with real Kaspa fee data not possible (no keyless fee history).
- The market-price model (breaker trigger), the outage process, hysteresis levels (25/15%) and rate limits are assumptions chosen for testing, not recommendations.
- Index processes run in the crash only (pre-year at I=1); shaping tests use deterministic ramps for the headline rows; drawdown labels are medians (T3 F6).
- Holder-side results are history (a4 data, one bear/bull cycle); L options 2a-2c not run with borrower demand. Persisting M2/T3 flaws apply (permanent sqrt impact, passive borrowers, uncalibrated capacity 5%/day).
- A2 borrower-relief variant and a recovery rule for W not simulated. No qgate, reviewer or code-map entry.

## 11. Reproduction (cwd = SP/econ/v6; python3 -B, numpy 2.2.6)
    python3 -B check.py; python3 -B check_t3.py; python3 -B check_v6.py      # all "OK", 0 differences
    python3 -B hist6.py > hist6_out.txt                                       # history tables (needs xraw/*.csv: FRED GETs 2026-11-11, DHHNGSP PNGASEUUSDM CUSR0000SEHF01 PCU221122221122 APU000072610 PNRGINDEXM)
    python3 -B v6_run.py --out v6.pkl --paths 1000 --procs 2                   # ~75 min
    python3 -B analyze_v6.py v6.pkl > tables_v6.txt
No background process left.
