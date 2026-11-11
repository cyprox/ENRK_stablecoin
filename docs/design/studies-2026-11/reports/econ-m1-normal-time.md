# ECON-M1 Normal-time economics of ENRK (stability fee, KAS fees, junior)
Date 2026-11-10. Every number is a MODEL OUTPUT under the stated assumptions, never a forecast. No design decision is made here.
Files (all in scratchpad/econ/m1/): m1_sim.py, m1_tables.py, results_vs1.0.json, results_vs1.4.json, tables_vs1.0.md (all grids, base vol), tables_vs1.4.md (vol x1.4), calib_vs*.txt.
Reproduce (numpy 2.2.6 installed; ~80 s per vol setting):
  cd /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/m1
  python3 m1_sim.py 1.0 > calib_vs1.0.txt ; python3 m1_sim.py 1.4 > calib_vs1.4.txt
  python3 m1_tables.py 1.0 > tables_vs1.0.md ; python3 m1_tables.py 1.4 > tables_vs1.4.md

## 1. Inputs
MEASURED: fees mint 2% / liq 4% / redemption 1%, KAS from vault collateral, treasury 20% to cap 2,500,000 units (~$300k), ICR min 200%, MCR 150%, redemption lowest-ICR-first min 100% (docs/design/FROZEN_PARAMETERS.md s1-6); liquidation fee applied to sale proceeds (tests/backtesting/stress_test_crash.py:37,420); KAS series = KuCoin KAS-USDT daily, 1285 days 2023-05-06..2026-11-10 (scratchpad/raw/kc_KAS.json, same as reports/r4-market.md). From it: daily sd 4.88% (annualised vol 93%), worst day -28.6% (close-to-close, r4 says -24.9% on a different measure; not reconciled). Rolling 365d return on this sample: p5 -71%, p25 -61%, median -47%, p75 +19%, p95 +556%; 45% of windows < -50%. The sample is bear-heavy.
ASSUMED (not data): regimes by drift and vol multiplier on the measured vol: calm drift +5%/yr vol x0.4; bull x2 price drift vol x0.7; sideways 0 drift vol x0.7; slow bear -50%/yr drift vol x0.7 (vs x1.4 as sensitivity). Paths: 300 per regime, 10-day block bootstrap of demeaned real daily log returns, days below -15% clipped (no crash). Resulting 1-yr price return p10/p50/p90 at vol x1.0: calm -34/+8/+75%, bull -10/+114/+380%, sideways -49/+17/+173%, slow bear -78/-50/+23%. Even "calm" has a p10 of -34% because KAS vol is high.
ASSUMED vault model: 100 vaults per path, opening ICR = base x lognormal(sd 0.15) floored at 200%; debt in USD (peg index = USD); daily steps; stability fee accrued daily in KAS from collateral; liquidation when ICR < 150% at the daily price, 4% fee on proceeds, no slippage, no liquidator shortfall, no top-ups by borrowers, liquidated vaults NOT replaced (denominator = average outstanding debt); redemptions hit lowest-ICR vaults at the stated rate regardless of peg; churn adds mint fee 2% x churn x average debt only (replacement mints do not alter the simulated population). Bad debt is 0 in every cell by construction (daily 150% trigger, no gap beyond -15%): normal-time losses to junior from bad debt are not captured; crash losses are out of scope.
Regime "mix" = equal weights of the 4 regimes (ASSUMED weights; the data cannot give them).

## 2. Revenue, % of average debt per year (churn 1, redemption 2%, ICR 250%, vol x1.0)
| regime | r | mint | stab | liq | red | total |
| calm | 0% | 2.00 | 0 | 1.00 | 0.02 | 3.02 |
| calm | 2% | 2.00 | 2.00 | 1.05 | 0.02 | 5.07 |
| calm | 5% | 2.00 | 5.00 | 1.12 | 0.02 | 8.14 |
| bull | 0% / 2% / 5% | 2.00 | 0 / 2.00 / 5.00 | 1.24-1.31 | 0.02 | 3.26 / 5.29 / 8.33 |
| sideways | 0% / 2% / 5% | 2.00 | 0 / 2.01 / 5.01 | 5.41-5.58 | 0.03 | 7.44 / 9.51 / 12.63 |
| slow bear | 0% / 2% / 5% | 2.00 | 0 / 2.01 / 5.03 | 12.1-12.4 | 0.03 | 14.11 / 16.24 / 19.44 |
| mix | 0 / 1 / 2 / 3 / 5% | 2.00 | 0 / 1.00 / 2.00 / 3.01 / 5.01 | 4.93-5.09 | 0.03 | 6.96 / 7.99 / 9.03 / 10.07 / 12.13 |
Reading: the stability fee adds exactly r (accrual is linear). Liquidation fees dominate in sideways/bear (they are paid by borrowers who lose collateral; they are not a recurring "yield" and vanish if borrowers keep ICR high). Redemption fees are negligible (1% x 2%).
Sensitivities (mix, % of debt, total): churn 0.5/1/2 at r=0: 5.96/6.96/8.96; at r=5%: 11.13/12.13/14.13 (mint fee = 2% x churn). Redemption 0/2/10% at r=2%: 9.15/9.03/8.64 (small, redemptions take out low-ICR vaults before they liquidate). Opening ICR 200/250/300 at r=2%: 14.84/9.03/6.82 (liquidation fees collapse with higher ICR). Vol x1.4: mix total at r=0 / 2% / 5% = 10.96 / 13.05 / 16.18 (liquidation grows with vol).
USD per year (mix, q=2%, ICR 250), M USD, for average debt 1/5/20M: churn 1: r=0 0.070/0.348/1.392; r=2% 0.090/0.451/1.806; r=5% 0.121/0.607/2.427. Churn 0.5: r=2% 0.080/0.401/1.606. Churn 2: r=2% 0.110/0.551/2.206. Full grid: tables_vs1.0.md T2.

## 3. Treasury: years to reach the 2.5M unit (~$300k) cap (20% of all fees, mean revenue constant, mix)
| r | D=1M | D=5M | D=20M | (churn 1, q 2%, ICR 250) |
| 0% | 21.6 | 4.3 | 1.1 |
| 2% | 16.6 | 3.3 | 0.8 |
| 5% | 12.4 | 2.5 | 0.6 |
Churn 0.5 / 2 at D=5M, r=2%: 3.7 / 2.7 years. By regime at D=5M, r=2%: calm 5.9, bull 5.7, sideways 3.2, slow bear 1.8 years (bear is fast only because borrowers are being liquidated). The stability fee shortens the time by ~25-40% at r=2-5% for D=5M; at D=1M the cap needs 12-22 years in every cell.

## 4. Borrower all-in cost vs holding the KAS
Setup: borrower locks C KAS, mints D, invests D at return y, versus keeping the C KAS unlevered. Delta = (end wealth with vault) - (hold). Non-liquidated: -fees_in_KAS x P_end + D*y. Liquidated: residual cash after 4% + debt, loses later KAS exposure, keeps D*(1+y). y* = break-even y = -(E[Delta0] - 2% x churn) / D (mint fee added analytically; redemption and stability fee inside the simulation).
Direct annual fee cost (certain part) = r + 2% x churn + 1% x redemption rate: at churn 1, q 2%: 2.02% (r=0), 4.02% (r=2%), 7.02% (r=5%) of debt per year.
y* (% of debt per year) including the liquidation/exit effect, churn 1, q 2%, mix of regimes:
| ICR | r=0 | r=2% | r=5% |
| 200% | 12.2 | 14.0 | 16.9 |
| 250% | 5.0 | 7.1 | 10.4 |
| 300% | 2.6 | 4.8 | 8.0 |
The fee-attributable increment y*(r)-y*(0) is ~2.1-2.2 pts at r=2% and ~5.4 pts at r=5% (ICR 250-300), i.e. slightly more than r because fee KAS is valued at end price and it lowers ICR.
Regime dependence is large and is NOT a fee effect: bull/sideways y* at r=0, ICR 250 = 14.7 / 19.4 (a vault that is liquidated on a dip misses the later rebound compared with holding); slow bear y* = -18.1 (liquidation exits a falling asset: the vault "beats" holding). At ICR 200% bull y* = 32.5 and sideways 33.8 at r=0. So "what must the borrowed funds earn": at ICR >= 250% in calm markets about fees + 2-4 pts (calm: 3.8% at r=0, 6.0% at r=2%, 9.1% at r=5%); in a market where KAS rises or whipsaws it is far higher because the liquidation threshold ejects the borrower from the position. Liquidation-prone borrowers (ICR 200%) need very high expected returns, which is evidence the product at 200% opening ICR is unattractive for leverage uses and mainly suits borrowers who want liquidity without selling.
Unmodeled borrower side: tax, alternative cost of capital, borrowing in other venues.
Liquidated share of vaults in one year (r=0 -> r=5%, q 2%): calm ICR200 29.1 -> 31.9%, ICR250 12.0 -> 13.4%, ICR300 3.7 -> 4.2%; sideways ICR250 35.6 -> 36.7%; slow bear ICR250 75.6 -> 76.7%; bull ICR250 10.6 -> 11.1%. Effect of the fee on ICR: it removes r/ICR0 of the collateral per year (r=5%, ICR 200%: 2.5% of collateral, ICR 200 -> ~195%); in the simulation this adds 0.2-2.8 percentage points of liquidated vaults, larger where vaults sit near 150% (calm ICR200 +2.8). Vol x1.4 raises liquidated shares a lot (calm ICR250 27.6% at r=0).

## 5. Junior (kFIAT) gross yield, % of junior notional per year (mix, churn 1, q 2%, ICR 250; net of bad debt = 0)
Rules: D1 = 100% of fee KAS to junior pro rata; D2 = 20% treasury until cap (yield x0.8), then 100% (= D1); D3 = fees to a reserve counted as collateral, nothing to junior (yield 0). Yield = (share x total fee % of debt)/s.
| r | s=15% D1 / D2pre | s=30% D1 / D2pre | s=50% D1 / D2pre |
| 0% | 46.4 / 37.1 | 23.2 / 18.6 | 13.9 / 11.1 |
| 2% | 60.2 / 48.2 | 30.1 / 24.1 | 18.1 / 14.5 |
| 5% | 80.9 / 64.7 | 40.5 / 32.4 | 24.3 / 19.4 |
These look high because the equal-regime mix contains large liquidation-fee income and zero junior loss in normal time; in calm markets alone (D1, s=30%) the yield is 10.1% at r=0, 16.9% at r=2%, 27.1% at r=5%. Junior also carries the crash risk (out of scope here), which is the real reason a hurdle above the fee yield is needed.
Wrong-way exposure (fees are paid in KAS): the stability fee is fixed in USD, so its USD value at receipt does not fall with the price; the exposure arises if the junior keeps the KAS. Held-in-KAS and marked at year end, D1 s=30% r=2%: bull 29.6 vs 17.7 at receipt (gain), sideways 37.9 vs 31.7, calm 17.9 vs 16.9, slow bear 38.0 vs 54.2 (the junior loses ~16 pts of yield, and p10 fee paid in KAS in mark-to-market terms is 2.6% of debt). Correlation between annual USD fee income and the KAS annual return is -0.2 to -0.5 (liquidation fees are larger when price falls), so USD fee income is a hedge in the receipt view, while the KAS-held stock of fee is a long-KAS position that falls in a bear. Both views are model outputs; whether the junior sells the KAS immediately is a behaviour the data cannot give.

## 6. Hurdle: largest voluntary junior share s* with net yield >= h (1% grid; 100 = cap not binding, i.e. even a fully junior book clears)
Columns D1 | D2 pre-cap | D1 held-in-KAS (marked at year end) | D3 (always 0; D3 clears no s>0 at any h>0). churn 1, q 2%, ICR 250.
mix: h=10%: r=0 69|55|68; r=1% 79|63|80; r=2% 90|72|92; r=3% 100|80|100; r=5% 100|97|100.  h=20%: r=0 34|27|34; r=2% 45|36|46; r=5% 60|48|64.  h=5%: 100 for every r in D1/D2.
calm only: h=10%: r=0 30|24|31; r=2% 50|40|53; r=5% 81|65|86.  h=20%: r=0 15|12|15; r=2% 25|20|26; r=5% 40|32|43.
bull only: h=10% r=0 32; r=2% 52; r=5% 83. sideways only: h=10% r=0 74, r=2% 95. slow bear: h>=10% -> 100 (D1) but h=20%: 70 (r=0), 81 (r=2%), 97 (r=5%); held in KAS 49 / 57 / 67.
Churn effect (mix, h=10%, D1): c=0.5 r=0 59, r=2% 80; c=1 69 / 90; c=2 89 / 100. Vol x1.4 (mix, h=10%): D1 100 for all r; D2pre 87 (r=0), 96 (r=1%), 100 beyond.
Logic: s* = (share x total fee % of debt)/h. Each +1 pt of r raises s* by roughly 10 pts of debt at h=10% and 5 pts at h=20%; at r=0 the calm market supports only 15-30% junior at h=10-20%, which is about the 30% cap already frozen; a recurring fee of 2-3% lets a calm-market junior reach the 30% cap at h=20% only for r>=3% (calm h=20%: s*=25% at r=2%, 30% at r=3%, 40% at r=5%). D3 gives the junior nothing, so the junior must be paid from elsewhere (not modelled).

## 7. What the data cannot tell (and sensitivity shown)
- Demand for credit, churn, redemption rate, regime weights, the vault ICR distribution and borrower top-up behaviour are not in any data: churn and redemption are shown over the grid; ICR 200/250/300 shown; regime weights are equal by assumption and results differ by x3-5 between calm and slow bear.
- KAS history here is one 3.5-year, bear-heavy, survivorship-biased sample; the regime drifts/vols are ASSUMED. Vol x1.4 roughly raises liquidation fee income by 80% (mix 4.93 -> 8.93% at r=0).
- Liquidation income is the largest and most volatile part of revenue in sideways/bear; it is a transfer from borrowers, depends on ICR cushion, assumes liquidators clear at the daily price with no slippage, and is zero bad debt by construction.
- Mint-fee income assumes churn is independent of r; in reality a higher r should lower demand/churn (elasticity unknown).
- Fee KAS is never burned in any of D1-D3 (junior / treasury then junior / reserve). The model does not rank them: D3 keeps KAS as collateral but pays the junior nothing; D1/D2 pay the yields tabulated.
- Out of scope: crash/tail losses to junior, the peg-unit vs USD difference (1 unit ~ $0.12 from FROZEN s6 only used for the cap), KAS price impact of selling the fee KAS, fee on treasury beyond the cap, tax.
