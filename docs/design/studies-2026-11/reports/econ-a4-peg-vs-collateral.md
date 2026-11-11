# ECON A4 - Peg index vs KAS collateral: how the index co-moves with the collateral, and what it means for CDP risk and "yield"

Date 2026-11-10. Scope: findings only, no design decisions. Read-only on the repo. Work dir:
`/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/a4` (scripts/, raw/, out/, daily.csv).
Tags: MEASURED (fetched, URL + date 2026-11-10) / DERIVED (computed from MEASURED or from code) / ASSUMED (my choice, flagged).
Every number below is a model or data output, not a forecast.

## 0. Headlines (10 lines)
1. ICR = C*P_KAS / (D*L*I) where I = peg index (code: `peg.rs`), D = debt in peg units, L = USD value of one index unit (undefined in docs/code, see 1.2). d ln ICR = r_KAS - r_I. A +33% index move is worth a -25% KAS move (200% -> 150% MCR). [DERIVED]
2. ENRK has no coupon and no interest. "Yield" from index drift is a mark-to-market gain/loss on a long position in a basket index (holder) matched by the opposite position (borrower). It is not a yield; it is a risk exposure with a zero-sum transfer between holders and borrowers (fees aside). [DERIVED from code/docs]
3. Reconstructed history (2023-03-21..2026-11-10, 1331 d): corr(KAS, index) of weekly returns is -0.13..+0.17 across 12 variants; 30-day returns -0.01..+0.30. Essentially uncorrelated on average, but the sign flips: rolling 13-week corr ranges -0.81..+0.82. [DERIVED]
4. Index and KAS moved in opposite directions in 42-58% of 30-day windows (hash-rate/energy variants), in 20-29% of windows the index rose while KAS fell. Real example: 2024-07-31 -> 2024-11-04 KAS -50%, index +52% (hash-rate component 2.54x its mean), so a vault opened at 200% on 2024-07-31 would have been at 101% KAS-only but 66% with the index (fullmean variant). [DERIVED]
5. Hash-rate lags price: KAS leads the index by 1-3 weeks (weekly cross-corr +0.13..+0.24 at lag +1..+3 in two variants; ~0 in the third). So a KAS crash is followed by an index rise before the hash-rate capitulates. [DERIVED, weak]
6. Baseline matters more than anything: Kaspa hash-rate grew 0.55 -> 337 PH/s (x615, MEASURED) so a launch-anchored hash-rate index sits at the 5.0 clip 90% of days. The code defines the baseline only loosely (`kaspa_adapter.rs`: "historical average"); the docs say "launch". [DERIVED]
7. The fees index as coded (avg fee / 0.1 KAS, clip 0.1) is pinned at the 0.1 floor: measured fee = 100-122 sompi per gram of mass = ~0.002 KAS per standard tx (7 txs, 0.0019-0.0096 KAS), i.e. 0.02-0.1 of baseline before clipping. [MEASURED+DERIVED]
8. In the joint vault model the index adds little to a 60-day KAS crash if it moves within about +-25%, but a lot beyond: at KAS -70%, mean unbacked debt is 1.1% of opening debt value with the index flat, 3.4% at I=1.5, 6.6% at I=2.0, 15% at I=3.0 (clip 5.0 binds only at I>=5). [DERIVED, model]
9. The circuit breaker as coded (|I-1| > 10% on the index value, never called by any module per AUDIT I12) interacts badly: if a trip halts liquidations, the hole at KAS -50% / I=1.5 goes from 1.6% to 34% of opening debt. The breaker trips from index noise alone in ~11% of 60-day paths (25% annual index vol). [DERIVED, model; the halting behaviour is ASSUMED]
10. Honest holder return: USD return of ENRK = change in I (if L fixed). Over 365-day windows of the reconstructed index it spans -62%..+145% (p5..p95, depending on variant), with median between -50% and +40%: sign not determined by the design. Calling this a yield would be wrong; call it index exposure.

## 1. How ENRK's USD value, vault debt and ICR depend on index and KAS (code/docs)
### 1.1 The index (MEASURED from code)
`contracts/igra/src/peg.rs`: `value = clip(0.40*H + 0.30*E + 0.20*F + 0.10*A, 0.1, 5.0)`; each input also validated to [0.1, 5.0] (an input outside raises an error, it is not clipped in `PegCalculator::calculate`; the clip in `oracle_feeds.rs`/`kaspa_adapter.rs` happens earlier).
What each component reads (`oracle_feeds.rs`, `kaspa_adapter.rs`):
- H = current hashrate (H/s) / baseline_hashrate_hps (constructor argument, "historical average", no value fixed); clip [0.1, 5].
- E = energy price USD/kWh from "Band Protocol" (mock in tests) / baseline, default 0.10 USD/kWh (doc: ~0.08); clip [0.1, 5]. No real feed, no aggregation code: the docs name IEA/GlobalPetrolPrices/ENTSO-E but nothing in the code reads them.
- F = avg fee in sompi / 10,000,000 (0.1 KAS); clip [0.1, 5]. (The doc says weekly fees vs first-week baseline: a different definition.)
- A = adoption metric / baseline (Chainlink "or on-chain source"; doc baseline 100M users); clip [0.1, 5].
- Index is dimensionless, 1.0 at baseline. 1 ENRK = 1 index unit of debt. The doc line "1 ENRK = 1 kWh" and "no USD oracle" cannot be literal: `types.rs::calculate_icr(kas_price, enrk_price, kfiat_price)` takes enrk_price as a parameter, and no module derives it from `PegPrice.value`. The stress simulator uses debt_value = units * peg, i.e. L = 1 USD per index unit at launch. [DERIVED] OPEN: the code fixes no L.
### 1.2 Formulas [DERIVED]
- ENRK USD price (par/redemption value) = L * I(t), L constant (ASSUMED L = 1 USD as in the simulator).
- Vault: collateral C KAS, debt D units (ENRK + kFIAT at face). **ICR = C * P_KAS / (D * L * I)**. With opening ICR0 at (P0, I0): ICR(t) = ICR0 * (P_t/P0) / (I_t/I0).
- Liquidation when ICR < 1.5: P_t/P0 < (1.5/ICR0) * (I_t/I0). From 200%: KAS can fall 25% with flat index, 0% if the index rises 33%, 50% if the index halves.
- Loss on collateral shortfall: unbacked = max(0, D*L*I - C*P*(1-discount)).
### 1.3 Who gains / loses when I moves [DERIVED from code and FROZEN_PARAMETERS §3,5; kFIAT denomination is undecided per AUDIT A1-A3]
| Party | I rises | I falls | Nature |
|---|---|---|---|
| ENRK holder | USD value up (he holds I*L USD per unit) | down | long the basket index, no cash flow |
| Borrower | debt in USD up, ICR down, closer to MCR; pays fees (2% mint, 1% redeem, 4% liquidation) | debt in USD down, ICR up | short the index, long KAS |
| Redeemer (burns ENRK, takes KAS at face, lowest ICR first) | gets more KAS per unit (redemption value follows I), vault owner loses more KAS | less KAS per unit | arbitrage floor: ENRK market price tends to >= L*I*(1-1%); sets who pays |
| kFIAT holder (junior, not redeemable) | if fixed face in peg units (A1): claim in USD grows with I but sits behind ENRK, first loss on holes; if A2/A3 undecided | claim shrinks | credit exposure + index; no yield mechanism defined (AUDIT E3 proposes fees paid in KAS) |
| Protocol / system | hole risk up (debt grows, collateral flat) | hole risk down | the system is exposed only through under-collateralised vaults |
Zero-sum: holders' index gain = borrowers' index loss (before fees and defaults). Index rises are paid for by borrowers, and when borrowers default the cost falls on ENRK holders/redeemers, then kFIAT.
### 1.4 What "yield" there is
- No interest, no coupon, no staking. STABLECOIN-FAILURE-ANALYSIS.md l.161: "The protocol promises no yield / pays nothing". Fees are 1-3% of debt/year (FROZEN_PARAMETERS §7) and go to treasury/reserve, not holders.
- The only return to ENRK holders is the change of I*L in USD. The only "return" to borrowers is the opposite sign on debt (a fall in I reduces debt in USD) plus the KAS leg.
- Verdict: a risk exposure with a documented zero-sum transfer. It is a gain only if I drifts up, a cost if it drifts down, and a risk (vol 19-26%/yr for the measurable legs) in both cases. FROZEN_PARAMETERS §1 already states "a peg that holds firm while collateral collapses maximises the fall in ICR"; this report shows the converse (an index that rises while collateral falls) happened in the data.

## 2. Data collected [MEASURED]
All public keyless GETs, fetched 2026-11-10; raw files in `raw/`.
| Component | Source (URL) | Coverage | Notes |
|---|---|---|---|
| KAS/USD daily | KuCoin `api.kucoin.com/api/v1/market/candles` (copied from scratchpad/raw/kc_KAS.json) + Gate `api.gateio.ws/api/v4/spot/candlesticks?currency_pair=KAS_USDT&interval=1d` | 2023-03-21..2026-11-10 (1331 d) | KuCoin overrides Gate on overlap. CoinGecko free tier limited to 365 d, not used. |
| Hash-rate daily | `api.kaspa.org/info/hashrate/history?resolution=1d` | 2021-11-08..2026-11-10 (1789 pts) | field hashrate_kh (kH/s) -> PH/s. 0.55 PH/s (2023-03-21) -> 337 (now); peak 1481 PH/s (Dec 2024). |
| Tx per day | `api.kaspa.org/transactions/count/{YYYY-MM}` (hourly rows, summed) | 2021-11..2026-11 | Spam bursts: single-day max 125M tx (Mar 2026). Not a usable fee proxy. |
| Active addresses | `api.kaspa.org/addresses/active/count/{YYYY-MM}` (hourly uniques, summed) | same | Hour-sum overcounts; level fell 145k -> 17k/day (method or real?). UNVERIFIED. |
| Kaspa fees history | **none**: `api.kaspa.org/openapi.json` lists no fee-history endpoint; only `/info/fee-estimate` (now: feerate 100 sompi/gram) | - | Spot check: 7 txs from `blocks-from-bluescore` + `transactions/search?resolve_previous_outpoints=light`: fee/mass = 100-122 sompi/gram (e.g. 274,200 sompi / mass 2742), 0.0019-0.0096 KAS. Coinbase outputs equal the base subsidy exactly (1.94454365 KAS): no measurable fee excess in the 48 sampled blocks. |
| Energy proxy A (commodity) | FRED `fred.stlouisfed.org/graph/fredgraph.csv?id=PNRGINDEXM` (IMF global energy price index, monthly, USD) | 2010-01..2026-09 | 186 (2023-03) -> 257 (2026-09); Aug 2022 peak 376. Oct 2026 missing -> forward-filled. |
| Energy proxy B (electricity, closest to code's USD/kWh) | FRED `id=APU000072610` (US avg retail electricity price, USD/kWh) | 2010-01..2026-10 | 0.166 -> 0.190. US retail, not global, not industrial: stand-in. Note: at the code's default baseline 0.10 this reads E = 1.9. |
| Brent daily | FRED `id=DCOILBRENTEU` | 2021.. | fetched, not used in the index (107 USD on 2026-11-03). |
Not obtainable keylessly: global industrial electricity (IEA/GlobalPetrolPrices need keys/licence); a real fee series; a clean adoption series.

## 3. Historical reconstruction (project formula) and comparison [DERIVED]
Method (`scripts/history.py`): daily index = clip(0.4 H + 0.3 E + 0.2 F + 0.1 A, 0.1, 5), components normalised by a baseline, clipped per component. Fees proxy F = 7-day mean of tx count; adoption proxy A = 30-day mean of hourly-summed active addresses (both ASSUMED stand-ins, both contaminated). Variants:
- baseline: `launch` (mean of first 7 days of the window), `fullmean` (full-sample mean, hindsight), `trail365` (trailing 365 d mean, my construction, window starts 2024-03-20, 966 d).
- energy: `idx` (commodity index) / `elec` (US retail electricity).
- proxies: `HE` (F = A = 1.0 held flat; only hashrate and energy move) / `full` (all four, noisy).
### 3.1 Volatility and correlation (weekly returns unless stated)
| Variant | vol index | vol KAS | corr wk | corr 30d | corr log-levels | rolling 13w corr min/med/max | idx outside 0.89..1.11 |
|---|---|---|---|---|---|---|---|
| launch/idx/HE | 19% | 98% | +0.11 | +0.30 | +0.45 | -0.41/+0.07/+0.76 | 99% |
| fullmean/idx/HE | 22% | 98% | +0.04 | +0.14 | +0.42 | -0.81/-0.06/+0.59 | 68% |
| trail365/idx/HE | 26% | 85% | -0.10 | +0.16 | +0.78 | -0.76/-0.08/+0.44 | 65% |
| fullmean/elec/HE | 19% | 98% | +0.03 | +0.09 | +0.43 | -0.81/-0.09/+0.80 | 76% |
| trail365/elec/HE | 22% | 85% | -0.13 | +0.14 | +0.84 | -0.76/-0.12/+0.48 | 79% |
| fullmean/idx/full | 104% | 98% | +0.07 | +0.01 | +0.27 | -0.73/+0.11/+0.60 | 87% |
| trail365/idx/full | 136% | 85% | +0.17 | +0.11 | +0.70 | -0.44/+0.09/+0.74 | 91% |
(Other variants in `out/history_summary.json`.) The project's published backtest vol (25%, PEG-FORMULA-RECOMMENDATION) matches the HE variants (19-26%); the `full` variants are inflated by spam in tx counts and are not evidence about the formula. Log-level correlations (+0.3..+0.8) are trend artefacts (both series trend) and say nothing about co-movement.
Component vols (weekly, annualised): hash-rate 74%, energy idx 30%, US electricity 4%, KAS 98%; corr of weekly returns with KAS: hash-rate +0.06, energy idx +0.03, electricity -0.03 (n~190).
### 3.2 Worst KAS drawdowns (peak -> trough), index change in the same window
| Window | KAS | index (fullmean/HE) | index (trail365/HE) | daily corr in window (fullmean) |
|---|---|---|---|---|
| 2024-07-31 -> 2026-08-13 | -87.7% | -14.6% | -54% | -0.05 |
| 2023-04-02 -> 2023-05-23 | -65.0% | -5.8% | n/a | +0.15 |
| 2024-02-19 -> 2024-05-02 | -41.8% | +8.5% | n/a | +0.04 |
Sub-window inside the first: 2024-07-31 -> 2024-11-04 KAS -50%, index +52% (hash-rate kept rising to a Dec 2024 peak 1481 PH/s, then fell -77% by 2026-11). Pro-cyclical fall only arrived 6-12 months later. Corr of daily returns inside drawdowns: -0.07..+0.15 ~ 0.
### 3.3 Direction, lead/lag
- Opposite sign: weekly 52-54% (fullmean/trail365 HE), 30-day windows 42-50%. Daily: 52% (of nonzero days). Under `launch` the weekly figure is 85% only because the index is nearly constant (clip-saturated hash-rate).
- 30-day windows with index up and KAS down: 20-29% (HE); index up >5% with KAS down >10%: 1-7% (HE) to 7-11% (full). Favourable (index down, KAS up): 16-24%.
- Lead/lag (weekly returns, positive lag = KAS leads): launch HE +0.16/+0.20/+0.24 at lags -1/+1/+2; fullmean HE +0.15 at -3, +0.13 at +1; trail365 HE +0.15 at +1; most other lags |r|<0.15. Weak, consistent with the 1-3 week hash-rate lag; not a stable predictor.
### 3.4 ICR history of a representative vault (open at 200%)
Vault opened 2024-07-31 (KAS ATH), ICR path: fullmean/HE index. [DERIVED]
| Date | KAS-only ICR | with index |
|---|---|---|
| 2024-11-04 | 101% | 66% |
| 2025-03-10 | 57% | 38% |
| 2025-07-21 | 111% | 94% |
| 2025-11-22 | 37% | 39% |
| 2026-08-13 | 25% | 29% |
Under trail365/HE the index helped (2025-07-21: 246% vs 111%) because the baseline absorbs the earlier hash-rate surge. So the sign of the effect depends on the baseline convention and on the phase of the hash-rate cycle.
All opening dates, 200% ICR, MCR 150% (share of start dates whose ICR touches <150%; KAS-only vs with index):
| Horizon | launch/HE | fullmean/HE | trail365/HE | fullmean/full |
|---|---|---|---|---|
| 90 d | 48 / 49% | 48 / 51% | 55 / 52% | 48 / 62% |
| 180 d | 63 / 65% | 63 / 67% | 79 / 73% | 63 / 80% |
| 365 d | 74 / 77% | 74 / 83% | 100 / 96% | - |
Share of start dates with ICR < 100% within 180 d: KAS-only 28% (fullmean) vs 31% HE, 58% full. Reading: with the measurable legs only, the index changes MCR-touch frequency by -6..+9 points and sometimes helps; with noisy proxies it adds up to +17 points. In all variants KAS alone already touches MCR in 48% of 90-day windows (this period is a bear market; not a base rate).

## 4. Joint scenarios and quantified CDP impact
### 4.1 Model (`scripts/jointsim.py`, seeded; 300 paths x 1200 vaults, 60 days) [DERIVED, ASSUMED parameters flagged]
- Vaults: opening ICR = 2.0 x lognormal(sigma 0.22), floor 1.53; debt weights lognormal(0.8). Liquidation at ICR < 1.5, whole-vault auctions, lowest ICR first, capacity 5%/day of opening debt (repo value; R4 flags it as uncalibrated); discount min(25%, 4% + 18% x drawdown from peak) (FROZEN_PARAMETERS §4). No redemption, no Stability Pool, no price impact feedback of liquidations on KAS (so unbacked debt is understated vs the full simulator; the model isolates the index effect).
- KAS path: 4.9%/day sd (MEASURED) + 2%/day jumps of -20% (ASSUMED), forced to a chosen terminal drawdown. Index path: bridge to a terminal multiplier I_T with noise 25%/yr (HE-variant history), correlation rho to KAS noise.
- Unbacked = realised shortfalls + latent shortfall of unliquidated vaults at the end, as % of opening debt value. "p>5%" = share of paths with unbacked > 5%.
### 4.2 Grid: mean unbacked debt (% of opening debt) by KAS drawdown (rows) and terminal index (columns), clip [0.1, 5.0]
| KAS | I=0.6 | 0.8 | 1.0 | 1.25 | 1.5 | 2.0 | 3.0 | 5.0 | raw 8.0 (clipped to 5.0) |
|---|---|---|---|---|---|---|---|---|---|
| -30% | 0.0 | 0.0 | 0.1 | 0.3 | 0.8 | 2.7 | 8.0 | 23 | 48 |
| -50% | 0.0 | 0.1 | 0.4 | 0.9 | 1.7 | 3.8 | 10 | 26 | 50 |
| -70% | 0.2 | 0.5 | 1.1 | 2.0 | 3.4 | 6.6 | 15 | 32 | 53 |
| -85% | 0.9 | 2.0 | 3.3 | 5.6 | 8.0 | 13 | 23 | 40 | 58 |
(The raw-8.0 column ends at I=5.0 after clipping like the 5.0 column, but its path is bridged to ln 8 before clipping, so it sits at the 5.0 cap for the whole second half; it shows how the clip bounds the damage only after it binds. Read the I<=3 columns for the main message.)
Extra unbacked debt caused by the index (vs I=1.0 column): at KAS -70%: +0.9 pt (I=1.25), +2.3 pt (1.5), +5.5 pt (2.0), +14 pt (3.0). Index falling (I=0.6) removes 0.9 pt. At KAS -85% the baseline is already 3.3%. P(unbacked > 5%) at KAS -70%: 3% (I=1.0), 29% (1.5), 50% (2.0), 89% (3.0).
### 4.3 Named joint scenarios (project formula applied to component multipliers) - mean unbacked % of opening debt, no breaker / index breaker halting liquidations (ASSUMED)
| Scenario | KAS | I_T | unbacked, no breaker | with halting breaker |
|---|---|---|---|---|
| N0 KAS-only (existing simulators) | -70% | 1.00 | 0.9 | 3.1 |
| N1 stress_test_crash elasticities (H r^.4, F r^.6, A r^.3, E=1) | -70% | 0.71 | 0.3 | 8.5 |
| N1b same | -85% | 0.61 | 0.8 | 20 |
| N2 energy x2, rest flat | -50% | 1.30 | 0.7 | 16 |
| N3 doc scenario 3 energy crisis (H .85, E x4, F 1.05, A .95) | -70% | 1.85 | **5.4** (p>5%: 40%) | 94 |
| N4 hash-rate collapse -70%, fees -50%, adoption -30% | -70% | 0.59 | 0.1 | 4.9 |
| N5 hash-rate -60%, energy x1.5, fees -50%, adoption -20% | -70% | 0.79 | 0.4 | 8.5 |
| N6 index up while KAS falls (H 1.5, E 1.3, F 2, A 1.3) | -60% | 1.52 | **2.0** (p>5%: 15%) | 48 |
| N7 doc scenario 2 bull (H 4, E 1.1, F 5, A 1.8) | x3 | 3.11 | 0.0 | 0.0 |
| N8 doc scenario 1 PoW ban | -60% | 0.78 | 0.1 | 3.0 |
| N9 favourable: hash-rate -50%, fees -50% | flat | 0.70 | 0.0 | 0.0 |
| N10 favourable: KAS +50%, index flat | +50% | 1.00 | 0.0 | 0.0 |
Reading: an energy shock coupled with a KAS crash is the worst realistic case (N3). A hash-rate collapse with a KAS crash (N4, the project's own PoW-ban story) lowers CDP risk but costs ENRK holders -41% to -22% in USD.
### 4.4 Statistical joint draws (index terminal conditional on KAS crash, conditional-mean shrink 0.5 ASSUMED), mean unbacked %
| index vol/yr | rho | KAS -30% | -50% | -70% | -85% |
|---|---|---|---|---|---|
| 25% | -0.5 | 0.2 | 0.8 | 2.3 | 5.0 |
| 25% | 0 | 0.1 | 0.4 | 1.3 | 4.0 |
| 25% | +0.3 | 0.1 | 0.3 | 0.7 | 2.4 |
| 25% | +0.6 | 0.1 | 0.2 | 0.7 | 1.5 |
| 55% | -0.5 | 0.7 | 1.7 | 4.4 | 8.8 |
| 55% | 0 | 0.3 | 1.0 | 1.7 | 4.8 |
| 55% | +0.6 | 0.0 | 0.1 | 0.4 | 0.9 |
Versus the KAS-only column at KAS -70% (1.1%, N0 0.9%): rho = -0.5 adds ~+1.2 pt (25% vol) / +3.3 pt (55% vol); rho 0 adds ~0.2/+0.6 pt; positive rho reduces it. Index noise alone is mildly harmful (consistent with convexity of debt value in the index; not separately tested).
### 4.5 Clip bounds [lo, hi] (KAS -50% / -70%, mean unbacked %)
| raw I_T | [0.1, 5.0] | [0.5, 2.0] | [0.8, 1.25] |
|---|---|---|---|
| 0.5 | 0.0 / 0.1 | 0.0 / 0.1 | 0.1 / 0.5 |
| 2.0 | 4.6 / 7.3 | 4.6 / 7.3 | 1.9 / 4.4 |
| 3.0 | 11.6 / 16.1 | 10.5 / 16.0 | 2.0 / 4.9 |
| 8.0 | 53 / 55 | 24 / 36 | 2.1 / 5.0 |
The frozen [0.1, 5.0] allows debt to grow 5x in index units; with all four components required to reach their individual cap simultaneously, the upper clip is far from binding in the history (max reconstructed 2.7 in the HE variants and 3.7 in the full variants, 0% of days at 5.0) but a hash-rate component can be pinned at 5.0 for 90% of days under a launch baseline. The clip protects the CDP side (caps debt growth) and exposes the holder side (floor 0.1 allows a -90% index with the stablecoin still "pegged"). Tighter bounds in the table are illustrations, ASSUMED, not recommendations. Note the interplay with the breaker: a 10% breaker on the index value makes everything above 1.11 or below 0.89 a pause, so the effective index range is [0.89, 1.11] if the breaker is wired to the index; the clip bounds then never bind. In the reconstructed history the index is outside [0.89, 1.11] on 65-99% of days (HE variants) - the breaker, if wired to the index value, would have paused the protocol almost permanently.
### 4.6 Circuit breaker (10% deviation, 6 h oracle downtime) - mean unbacked %, KAS -50% (-70%)
| terminal I | no breaker | index breaker halts liquidations | index breaker, liquidations continue | oracle outage 1%/day halts liq | oracle 5%/day halts liq |
|---|---|---|---|---|---|
| 0.8 | 0.1 (0.5) | 0.7 (8.6) | 0.1 (0.5) | 0.4 (5.6) | 1.2 (16) |
| 1.0 | 0.4 (1.0) | 0.8 (2.6) | 0.4 (1.0) | 2.6 (9.6) | 7.2 (27) |
| 1.5 | 1.6 (3.0) | 34 (52) | 1.6 (3.0) | 13 (20) | 34 (53) |
| 2.0 | 3.4 (6.3) | 83 (109) | 3.4 (6.3) | 23 (31) | 62 (79) |
Code facts: `circuit_breaker.rs::check_peg_deviation` computes |peg - 1.0| x 100 truncated to u8 and trips on > threshold (so >= 11%); it pauses mint/burn and "persists until manual resolution". It is called nowhere (AUDIT-2026-11-09 I12) and whether a pause halts liquidations is not specified (ASSUMED both ways above). The 6 h oracle clause: a daily-grid model cannot represent hours, so a daily hazard of 1% / 5% is ASSUMED. Finding: any pause that stops liquidation while the index or KAS keeps moving transfers the whole crash into unbacked debt; the breaker is the largest single lever in this table, larger than the clip bounds.

## 5. ENRK holders' real return from the design [DERIVED/ASSUMED]
- USD return of an ENRK unit = I(t)/I(0) - 1 (L fixed). 365-day windows of the reconstructed index (HE variants; `out/holder_returns.json`): trail365/idx: p5 -62%, median -42%, p95 +24% (80% of windows negative: dominated by the post-peak hash-rate decline); fullmean/idx: p5 -46%, median +16%, p95 +145% (48% negative); launch: ~0% median (hash-rate pinned at clip). With noisy proxies (`full`): p5 -57..-68%, p95 +51..+237%.
- Energy-only legs: 12-month change of the IMF energy index 2011-2026: p5 -45%, median -1%, p95 +104%, min -61%, max +169%, 52% negative; US retail electricity: p5 -2%, median +2.3%, p95 +10%, min -3.5%, max +17%. Drift (log, annual): energy index +2.2% (2010-2026), +10.9% since 2021; electricity +2.6% / +5.9%. Corr between the two monthly: +0.03, so which proxy the oracle reads changes the character of 30% of the index from near-stable to commodity-volatile.
- So the design gives holders: (a) 30% weight on a legit energy-price leg whose long-run nominal drift is ~inflation-like (+2..+6%/yr electricity) or commodity-like (30% vol, no reliable positive drift), (b) 40% on Kaspa hash-rate, a growth series that rose x615 in 3.7 years then fell -76% from its peak, (c) 30% on two Kaspa-activity legs with no clean measurement (fees pinned at the clip floor as coded; adoption metric undefined in code). Honest range for USD index return per year: roughly -60% to +140% across variants, centre unidentified; not a forecast. Add 40% hash-rate weight with an unidentified baseline and the whole level is a baseline choice.
- Can it be called a yield? No. There is no cash flow or counterparty paying it, it is a zero-sum mark between holders and borrowers, its expectation is not positive by construction, and its sign flips in the data. The accurate wording: "ENRK is a claim indexed to a weighted basket; its dollar value is volatile (19-26% a year for the measurable legs) and can fall." A defensible "benefit" is purchasing-power exposure to energy prices (30% weight), not yield. The project has so far documented the cost side for borrowers (index rising when collateral falls) only in the ICR sense and only with a flat index.

## 6. Parameters for other simulators (m1, m2) to add index dynamics
Per component (daily steps; v = annualised vol; corr to KAS = rho_i). All MEASURED-derived unless flagged:
| Item | Base | Range (stress) | Source |
|---|---|---|---|
| KAS daily sd | 4.9% | 3.9-5.6% (analogs, R4) | R4 |
| Index weights | .4/.3/.2/.1 | fixed | peg.rs |
| Index annual vol (hash-rate+energy legs only) | 22% | 19-26% | §3.1 |
| Index annual vol incl. noisy fees/adoption proxies | 55% | 55-136% | §3.1 (data artefact) |
| Hash-rate component vol (weekly ann.) | 74% | 55-80% | §3.1 |
| Energy idx vol / drift | 30% / +2.2% yr | 29-33% / +2..+11% | energy_stats.json |
| US retail electricity vol / drift | 5% / +2.6% | 4.5-5.5% / +2.6..+5.9% | energy_stats.json |
| corr(KAS, index) weekly returns | 0.0 | -0.13..+0.17 (rolling -0.8..+0.8) | §3.1 |
| corr in worst KAS drawdowns (daily) | 0.0 | -0.07..+0.15 | §3.2 |
| Lag: KAS leads hash-rate by | 1-3 weeks | 0-4 | §3.3 |
| Index change over a KAS -50% window | -6% .. +52% (hash-rate rose in 2024-H2) | -50% .. +60% | §3.2 |
| Monthly energy jump: P(|dm|>15%) | 8% / month | 4-12% | 16 of 201 months |
| Worst/best monthly energy move | -40% / +42% | - | energy_stats.json |
| Worst/best 12m energy move | -61% / +169% | - | holder_returns.json |
| Frequency, 30-day window: index up & KAS down | 24% | 20-29% | §3.3 |
| Frequency: index up >5% & KAS down >10% | 4% | 1-11% | §3.3 |
| Clip | [0.1, 5.0] | tighter variants as sensitivity | peg.rs |
| Breaker | trips if trunc(abs(I-1)*100) > 10 | none / halts liq / continues | circuit_breaker.rs |
| Liquidation capacity | 5% of opening debt/day | R4 | R4 |
Suggested adverse combos to include: (i) I x1.5..2.0 with KAS -60..-70% (N6/N3); (ii) energy x2 with KAS -50% (N2); (iii) hash-rate -60..-70% with KAS -70% (N4, favourable to CDP, adverse to holders); (iv) KAS +50% with I flat (favourable). Debt valuation rule: debt_USD(t) = units * L * I(t), I from the formula with the clip applied after weighting.

## 7. Limits / unverified
- 3.7 years of KAS history in one bear/bull cycle; no independent test of lead/lag. KAS/index correlations carry sampling error of about +-0.06 (n=190 weeks).
- Fees and adoption legs cannot be measured keylessly; their variants are noisy proxies. The fee spot check is 7 transactions.
- L (USD per index unit) and the baselines (hash-rate, energy, adoption) are not fixed by code; my baselines are assumptions. The sign of many results flips with them.
- The vault model omits redemption, Stability Pool, price impact of liquidations and kFIAT waterfall; unbacked debt levels are indicative and not comparable in absolute terms with `stress_test_crash.py`. Normalisation: % of opening debt value in USD, so columns with I >> 1 mean the debt value outgrew its opening value.
- The "conditional mean shrink 0.5" in 4.4 and the jump overlay are my assumptions; no secondary check of the model by another reviewer (qgate/done-check not run: out of scope, findings only, no repo change).

## 8. Reproduction (stdlib+numpy 2.2.6; from the a4 dir)
```
cd /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/a4
bash scripts/fetch_all.sh          # public GETs -> raw/ (KuCoin KAS daily is copied from scratchpad/raw/kc_KAS.json beforehand, see raw/kucoin_KAS_daily_scratch.json)
bash scripts/sample_fees.sh && bash scripts/fee_resolve.sh   # fee spot check (blocks sampled near the chain tip, results vary by run)
python3 scripts/build_dataset.py   # -> daily.csv
python3 scripts/history.py         # -> out/history_summary.json, out/index_*.csv
python3 scripts/energy_stats.py    # -> out/energy_stats.json
python3 scripts/holder_returns.py  # -> out/holder_returns.json
python3 scripts/jointsim.py 300 1200   # ~70 s -> out/jointsim_results.json
```
