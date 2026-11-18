# ECON-T2 Borrower demand for ENRK debt vs all-in cost (TEST, no decision)

Status 2026-11-17: owner decisions since this report: execution layer is Kaspa L1, Igra not retained (2026-11-13); stability fee recurring, fees never burned (a burn option is excluded). Passages on Igra and on burning are kept as history.

Status 2026-11-17: headline values are for the cushioned index (original simulator, index falls with KAS to about 0.54 at -85 %); on a flat index ENRK p95 13.8 %, junior net -15.5 % (econ-t3, econ-v1). Not re-based except in part by econ-w1 section 4 (with the redemption schedule ON). See ECONOMICS-VERIFICATION-2026-11-11.md section 2.
Date 2026-11-10. Every output is a MODEL RESULT, not a forecast. Demand is NOT observable here (no ENRK borrower exists; no data on how Kaspa holders would use borrowed stablecoin). The reference rates in section 5 are the only external anchor; the demand-distribution parameters are ASSUMED and decide the answer.
Work dir: /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/t2 (t2_demand.py, tables.md = all tables, grid.csv = 1,568 rows, web/ = downloaded public data, fetch_refs.sh, ref_extract.py). Repo untouched; nothing read under scratchpad/tn10; no secrets.

## 1. Model (all in t2_demand.py, python stdlib only)
Borrower i has an expected return y_i (% per yr) on the borrowed stablecoin and a horizon T_i. He opens a vault iff y_i > y*(r, ICR, T) + X.
- y*(r, ICR) = MEASURED-in-model from econ-m1-normal-time.md s4 (mix of 4 regimes, churn 1): ICR 200: 12.2/14.0/16.9; 250: 5.0/7.1/10.4; 300: 2.6/4.8/8.0 at r=0/2/5% (calm-only ICR 250: 3.8/6.0/9.1). Linear between points; beyond r=5% extrapolated with the last slope (ASSUMED, +1.08 per pt). The table already contains the 2% mint fee at T=1.
- Horizon: mint fee 2% (MEASURED, FROZEN_PARAMETERS s6) is amortised: y*(T) = y*(M1) - 2 + 2/T. Main tables T=1 yr; variant "Tmix" lognormal median 0.5 yr, sigma 1, clipped [1/12, 5] (ASSUMED).
- X = extra borrower cost from surplus withholding, 0/5/10/15 pts of debt per yr (ASSUMED; M2 s1 measured-in-model: S2/S3 forfeit 15-18% of opening debt per crash cycle, S1 returns it). X=0 is S1.
- y distribution (ASSUMED, 7 sets): L8 lognormal median 8% sigma 0.9; L4 median 4%; L12 median 12%; E8 exponential mean 8%; P Pareto xm 2.5% alpha 1.5 (mean 7.5%); K15 and K0 = leveraged-long-KAS motive, y = own expected KAS return ~ Normal(15%, 40%) / Normal(0%, 40%) (dispersion of beliefs). Note y* from M1 is already "versus holding the KAS", so a long-KAS borrower's y is his excess belief; K sets are crude.
- D = P(y > y*) averaged over T. Reported as D_rel = D(r,X)/D(r=0,X=0) and D_abs = fraction of the reference population that opens a vault (all vaults equal size, ASSUMED).
- Revenue R(r) per unit of reference-population debt = sum over opening borrowers of (r + 2/T + liq(ICR) + 0.03 + X). liq = 5.0 (ICR 250 mix), 10.8 (ICR 200), 2.8 (ICR 300), backed out of M1 s2 (calm only: 1.05). Event fees are NOT zero-cost to borrowers (in y*) and I assume liq income is independent of r.
- Junior: M2 E_w(r) = 0.9*calm + 0.1*cycle at s=30, D1/S1 (M2 s2 cells), r_clear(h) = r with E_w = h. Cross-check vs M2 s* table: h=5 1.77 vs 1.67, h=10 3.29 vs 3.06 (OK). r>5 is EXTRAPOLATED (M2 stopped at 5%).

## 2. Demand D(r)/D(0), ICR 250, T=1, X=0 (full grid incl. ICR 200/300, Tmix, calm: tables.md TA)
| set | r=1 | 2 | 3 | 4 | 5 | 7 | 10 | D_abs(0) |
| L8 | .89 | .79 | .70 | .62 | .55 | .44 | .32 | 0.70 |
| L4 | .80 | .65 | .53 | .43 | .36 | .25 | .16 | 0.40 |
| L12 | .93 | .86 | .80 | .73 | .67 | .57 | .45 | 0.84 |
| E8 | .88 | .77 | .67 | .58 | .51 | .39 | .26 | 0.54 |
| P (heavy tail) | .75 | .59 | .48 | .39 | .33 | .25 | .18 | 0.35 |
| K15 long-KAS | .98 | .97 | .95 | .93 | .91 | .88 | .82 | 0.60 |
| K0 long-KAS | .98 | .95 | .93 | .91 | .88 | .84 | .77 | 0.45 |
Semi-elasticity at r=2: -9 to -12% of D per +1 pt of r for L/E sets (-21 to -23% for L4/P; -2% for K sets). Cost levels matter more than the slope: opening ICR 200 vs 250 vs 300 changes D_abs(0) of L8 from 0.32 (ICR 200) to 0.70 (250) to 0.89 (300); the opening-ICR choice shifts demand by more than 3 pts of r does (y* at ICR 200 is 12.2 at r=0).
Surplus withholding X (ICR 250, T=1), D_rel at r=2 / r=5: L8 X=0 .79/.55; X=5 .46/.33; X=10 .29/.21; X=15 .19/.14. L4 X=15: .07/.05. K15 X=15: .72/.66. E8 X=10: .22/.15. P X=10: .16/.12. So +5 pts of withheld surplus cuts the L/E/P demand by 40-60% at r=0, comparable to ~+5 pts of r; the long-KAS motive loses only 8% per +5 pts.

## 3. Revenue (Laffer) and cliff (ICR 250, T=1; tables.md TB)
- Stability-fee-only revenue r*D(r): argmax is at r=10 (end of grid) for L8, L12, K, and P at X>=5; interior for L4 (5.6%), E8 (7.3%), P X=0 (8.9%), L4 X=5/10/15 (7.0/8.3/9.6). With the 2% mint fee and ~5% liquidation income included (R), total revenue is NEARLY FLAT or falling in r for the L/E/P sets: argmax 0-1.5% (R(10)/R(0)= 0.77 L8, 0.38 L4, 0.62 E8, 0.43 P) because event fees (7% of debt) are lost when borrowers leave; it rises with r only for L12 (argmax 5.2%, +15%) and K sets (R(10)/R(0)=1.9-2.0). Result is an artefact of the ASSUMED 5% liquidation income per debt, itself regime dependent (M1: x3-5 across regimes; at calm liq=1.05 stab-fee revenue weighs more).
- "Cliff" (r where D falls to 50% of D(0), X=0, ICR 250): L8 5.9, L4 3.3, L12 8.8, E8 5.2, P 2.8, K >10. For ICR 300, L4 2.95 and P 1.4. There is no sharp cliff in this model (smooth tails); a real cliff would come from the M2 liquidation threshold: with the opening-ICR floor 153% vs MCR 150%, M2 s3 measures a wave of early liquidations once r > 3.0% (0 of 1000 vaults at r<=3.0, 111 at 3.05, 124 at 5%), for a population piled at the floor (11% at target ICR 200); not modelled here as a demand effect (borrowers who top up are not in M2).

## 4. Junior and the M2 intersection (tables.md TC, TD, TE)
Junior gross yield at s=30% (D1): r/s = 0/3.3/6.7/10/13/17/23/33 % for r=0/1/2/3/4/5/7/10; all fees/s = (r+2+5+0.03)/0.3 = 23/27/30/33/37/40/47/57 (mix liq), calm liq 10 to 44. It does not depend on D when s is held at 30%: D only scales USD income. If the junior pool K is fixed (sized for s=30% at r=0 demand), the pool's yield = income/K and the part of K deployed at s<=30% shrinks with D: idle share of K at r=5%: L8 0.45, L4 0.64, E8 0.49, P 0.67, L12 0.33, K 0.09-0.12 (at r=10: 0.55-0.84 / 0.18-0.23). Stab-fee-only pool yield rises to a plateau (L8 7.4% at r=10; L4 4.2% max at r=5; P 4%).
r at which a 30% voluntary junior clears (D1/S1 = S3 income; M2 w=10%, sold on receipt, mint-fee income NOT in M2):
| h | r_clear S1/S3 | with mint-fee income to junior added (T=1) | S2 (from M2 s* table) |
| 5% | 1.8 | 0.0 | <1 |
| 10% | 3.3 | 1.5 | 1.5 |
| 20% | 6.8 (extrapolated) | 4.7 | 3.4 |
Is r_clear inside the surviving-demand range (D/D0 at r_clear, ICR 250, T=1, X=0, h=5/10/20)? L8 .81/.68/.45; L4 .68/.50/.26; L12 .88/.78/.58; E8 .79/.64/.40; P .62/.45/.26; K15 .97/.94/.88; K0 .96/.92/.84. With X=10 and S2 clearing (r 0.5*/1.5/3.4): L8 .95/.86/.72; L4 .93/.80/.61; E8 .94/.82/.63; P .95/.86/.72; K15 .99/.97/.93 (*placeholder r=0.5, M2 only says it clears at r=0).
Which assumption decides: (a) h: at h=5-10% r_clear is 1.8-3.3% where 70-97% of demand survives in every set but L4/P at h=10 (45-50%); at h=20% r_clear 6.8% is beyond the 50%-survival point in L4, E8, P, L8 (.45) and inside it only for L12 and K. (b) the y-distribution location and tail (L4 vs L12: D at r=3 .53 vs .80) and whether the borrower motive is rate-insensitive (K). (c) the junior-income convention: counting the 2% mint fee as junior income moves r_clear(10%) from 3.3 to 1.5. (d) S2 vs S1/S3: S2 halves the r needed, but X>0 removes 40-60% of rate-sensitive demand at r=0, so the surplus variant trades junior clearing r against level of D. (e) the M2 junior returns are themselves sign-sensitive to the unmeasured impact/capacity (M2 s5), and sell-on-receipt is load bearing (held-in-KAS value ~15% of face).
Honest caveat: D is a share of an assumed population; nothing here says how large that population is.

## 5. Reference borrowing costs (SECONDARY unless stated; snapshots 2026-11-10 ~19:00 UTC, DeFiLlama /lendBorrow field apyBaseBorrow joined to /pools; downloaded in web/)
| protocol (collateral -> debt) | borrow cost | source |
| Liquity v1, ETH -> LUSD | 0% interest; one-time fee floor 0.5%, max 5%, rises with redemptions (MEASURED, primary docs) | https://github.com/liquity/dev (README "Fee Schedule", line 1275: BORROWING_FEE_FLOOR=0.5%, MAX_BORROWING_FEE=5%); https://docs.liquity.org/liquity-v1/faq/borrowing ("interest-free"); DeFiLlama row shows 0.50 |
| Liquity v2 -> BOLD | user-set rate; upfront fee = 7 days of average interest; observed branch averages: wstETH 1.0%, ETH 4.1%, rETH 7.6% | https://docs.liquity.org/faq/borrowing (primary: rule); https://yields.llama.fi/pools + /lendBorrow (SECONDARY: averages) |
| Sky (ex-Maker) vaults -> DAI/USDS | WETH 10.3-11.0%, wstETH 11.3-11.5%, WBTC 15.3-16.0%, SKY 7.7% | https://yields.llama.fi/lendBorrow (SECONDARY; not checked against Sky's own page: https://info.sky.money returned only a 1.8 kB script shell) |
| crvUSD | 7.6% (identical on all 8 collaterals in this snapshot) | same DeFiLlama files (SECONDARY) |
| Aave v3 Ethereum | USDC 4.5%, USDT 4.4%, DAI 4.6%, GHO 3.3-4.5% | same (SECONDARY) |
| Compound v3 Ethereum | USDC 3.9%, USDT 5.8% | same |
| SparkLend Ethereum | USDS 4.9%, DAI 5.0%, USDT 4.2%, USDC 4.8% | same |
| Kaskad on Igra (KAS lending) | borrow rates NOT published in the sources reachable by GET (not in DeFiLlama yields; the whitepaper PDF https://github.com/Kaskad-Lending/kaskad-public-docs was not parsed) | - |
KAS-lending market size: DeFiLlama https://api.llama.fi/protocol/kaskad (2026-11-10): Kaskad (Aave-v3 fork, Igra + Robinhood Chain) TVL total $0.66M; Igra side supply $0.30M, borrowed $0.09M (Robinhood Chain $0.36M / $0.06M); KSKD market cap $2.8M. No other KAS lending market found. So the observable on-chain KAS credit market is of order $0.1M of borrow, 2-3 orders of magnitude below ENRK's illustrative debt sizes in M1 ($1-20M).
Where the tested range sits: all-in direct cost to an ENRK borrower at T=1, churn 1 = r + 2% mint + 1% x redemption: 2.0% (r=0), 4.0 (r=2), 5.0 (3), 7.0 (5), 9.0 (7), 12.0 (10). Against references: r=0 equals Liquity v1's average-to-high fee band (0.5-5%) and is below all variable-rate stablecoin debt; r=2-3% lands at Aave/Compound/Spark stablecoin APR (3.3-5.8%); r=5% (7%) is at crvUSD (7.6%) and Liquity v2 rETH; r=7-10% (9-12%) reaches Sky ETH vault territory (10-11%). Those comparators lend against liquid ETH/BTC at LTV up to 80-90% and USDC pools without liquidation-by-collateral-ratio at 150-200%; ENRK's 200% opening ICR on a vol-93% collateral with y* 5-12% (M1) is a worse product at equal price, so equal-rate parity is not the relevant anchor (observation, no recommendation). The 15-pt variants of X (total 17-27% all-in) lie far above any listed rate.

## 6. What would change the answer / limits
- Population size, borrower motives and the y distribution are unobservable; the K sets (long-KAS motive) are nearly rate-insensitive, the L4/P sets (low-yield, heavy tail) lose half of demand by r=3%. The spread of D(r=5%) across sets is 0.33-0.91.
- y* is a regime-mix average; demand in a bear regime (y* negative at ICR 250 in M1) or a bull one (y* 15-33%) is different, and the borrower's regime view is not modelled. M1 y* does not include tax, alternative credit, or competing venues.
- Horizon enters only through the mint fee. Tmix lowers D_abs(0) (L8 0.52) but leaves D_rel almost unchanged (tables.md).
- Revenue results depend on the liq-income assumption (calm 1% vs mix 5%) and on liq income being independent of r. The leverage-long motive and a higher r raise liquidation probability (M1: +0.2-2.8 pts), not modelled in D.
- r>5% for y* and E_w are extrapolations. X is a flat extra cost, while true S2/S3 cost is a contingent loss on liquidation (borrowers who never get liquidated pay nothing).
- No design decision is made or implied.

## 7. Reproduction
  cd /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/t2
  python3 -I t2_demand.py > tables.md        # also rewrites grid.csv; <5 s
  sh fetch_refs.sh && python3 -I ref_extract.py   # public GETs; (cp lendborrow.json kaskad.json as named in fetch_refs.sh)
Inputs read: reports/econ-m1-normal-time.md, reports/econ-m2-crash-with-fees.md, docs/design/FROZEN_PARAMETERS.md (read only). Not done: qgate, reviewer run, code map (scratch work).
