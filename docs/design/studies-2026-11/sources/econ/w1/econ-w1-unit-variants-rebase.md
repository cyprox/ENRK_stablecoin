# ECON-W1 Unit of account as a variable (U0-U6 plus U3b USD/CNY/RUB basket): history, crash simulation, re-base of the older conclusions
Date 2026-11-11. TEST only, no design decision. Every number is a data or model output; ASSUMED items are labelled. Repo untouched, nothing read under scratchpad/tn10, no secrets, no process left (max 3 used).
SP = /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad ; work dir SP/econ/w1 (history/data scripts at the root, simulator and runs in SP/econ/w1/sim).
Owner question: why USD as the index unit when the yuan is a safe value. The USD in earlier tests was a modelling numeraire. Here the unit is a variable.

## 0. Variants, definitions, validation
Unit value u(t) = USD value of one unit of account. Debt is fixed in units, so debt value in USD = D x u(t); in the simulator u(t) is the index I(t) that multiplies debt value everywhere (ICR, auctions, redemption, ledger, latent hole). A vault opened at 200%: ICR(t) = 200% x (KAS_usd(t)/KAS_usd(0)) / (u(t)/u(0)). "Up" = unit revalues against USD (raises debt value in USD: adverse for the system); "down" = unit loses USD value (adverse for ENRK holders measured in USD).
| id | unit | series used (all keyless GET, fetched 2026-11-11) |
|---|---|---|
| U0 | coded index (hash rate / energy / fees / adoption) WITHOUT the cushion | v6 bases: flat, stochastic p_base (vol 22%, jumps), deterministic x1.5 / x2 ramps; history = v6 coded index (hindsight baseline "HE", and the noisy-proxy version) |
| U1 | 1 USD | none |
| U2 | 1 CNY | FRED DEXCHUS (Fed H.10 onshore CNY per USD, 1981-2026-11-06); cross-check ECB eurofxref-hist.csv (USD/EUR over CNY/EUR) |
| U3 | basket 1/3 USD, 1/3 EUR, 1/3 CNY (fixed quantities) | DEXCHUS, FRED DEXUSEU |
| U3b | basket USD / CNY / RUB: equal 1/3 each; alternative 50% USD / 30% CNY / 20% RUB (labelled); also logged U3c = USD/EUR/CNY/RUB 1/4 each (history only) | RUB = Central Bank of Russia (CBR) OFFICIAL USD/RUB, XML_dynamic.asp?VAL_NM_RQ=R01235, 2005-01-01..2026-11-11, 5409 observations, one per CBR rate-setting day including weekends set in advance; max gap 13 days |
| U4 | electricity only | FRED APU000072610 (US retail electricity, monthly; 45-day publication lag variant in history) |
| U5 | slow-up / immediate-down bounded index, up-limit 0.25%/day | applied to the U0 bases (history: to the coded index) |
| U6 | gold | Yahoo chart API GC=F (COMEX gold futures, daily 2000-08..2026-11; UNOFFICIAL, continuous futures contract). FRED LBMA gold series return 404 now; stooq needs JavaScript. So U6 is available but with an unofficial source |
KAS = a4 dataset daily.csv 2023-03-21..2026-11-10 (3.6 years: one bear/bull cycle, F=A=1 proxies in U0). KAS annualised vol 97%.
Validation (all re-run this session, 0 differences): ECON-V1 simulator checks (check_v1: 17280 + 60 + 56 + 200 + 180 comparisons, on the MODIFIED simulator); ECON-V6 simulator checks in SP/econ/w1/v6chk (check 6300x2 + 90, check_t3, check_v6 7848); new check_w1 on the two options added here (index_mode "path" = USD-value path of the unit; idx_max_up_step = slow-up bound): 14590 field comparisons, 0 differences (features off == V1; path with the det ramp == det mode; path of ones == flat; up-limit inert when large, binds exactly at 1.0025^60, falls unlimited; cached pre-year == full run). Reproduction of old cells: U1 flat85 A3 13.8 [11.2,15.5] / kFIAT 25.7 / net -15.5 / unbacked 10.2; x1.5 17.3, x2 20.0; A5 12.5/8.5/+1.7; A8 5.4; A0 25.4: identical to ECON-V1/V5 (same seeds, 500 paths).
Simulation set-up = ECON-V1 frozen set-up: floor 75%, redemption on, ICR 200%, 1000 vaults, 365 calm days at I=1 then 60-day crash, stress 0.18, impact 0.08, capacity 5% of opening debt/day, ADV 40M KAS, D1. Architectures: A0 r0 s0 | A3 r3 s30 S1 | A5 A3 with S3 | A8 r3 s50 | STACK r3 s70 S3 + C1a(g=0) + C2. 500 paired paths per cell (path i = SEED+i in every cell; unit paths use per-path RNGs shared across units). Headline CIs are paired-bootstrap 95%.
Unit paths in the crash: s0 = lognormal diffusion with the MEASURED 2023-03..2026-11 vol and drift (CNY 3.0% / +0.8%, basket 2.9% / +0.6%, RUB eq 4.5% / -0.2%, RUB 50/30/20 2.7% / -0.1%, electricity 4.4% / +3.7%, monthly steps on crash days 10 and 40 ASSUMED, gold 20.6% / +20.4%); s+X / s-X = same plus a log-linear ramp of the unit by X% over the 60 crash days (+: unit revalues = adverse for the system); j+20 / j-20 = a step of 20% on crash day 5 (ASSUMED timing); boot = a random historical 60-day window of 2005-2026 (same start for all units on a path; windows overlap, ~100 independent); worst+ / worst- = replay of the worst historical 60-day window of that unit (deterministic path; KAS randomness only). Unit path independent of the KAS path (measured correlation daily/30d -0.1..+0.14, 3.6 years).

## 1. HISTORY (a): the unit as seen from KAS (2023-03-21..2026-11-06, 1327 days; SP/econ/w1/units_hist_out.md, units_hist.json)
Opening ICR 200%, MCR 150%. touch = share of start dates whose ICR touches 150% within the horizon; KAS in USD only = 48 / 63 / 74% (90/180/365 d), ICR<100% in 180 d = 29%.
| unit | vol/yr | drift/yr | corr with KAS daily / 30d | worst 30d up / down | 365d unit return p5 / med / p95 | touch 90/180/365 | ICR<100% 180d |
|---|---|---|---|---|---|---|---|
| U1 USD | 0 | 0 | n/a | 0 | 0 | 48/63/74 | 29% |
| U2 CNY (FRED) | 3.0% | +0.8% | +0.05 / +0.14 | +2.6% / -3.0% | -4 / +1 / +7% | 48/64/74 | 28% |
| U2 CNY (ECB cross) | 3.1% | +0.8% | +0.02 / +0.13 | +2.7% / -2.9% | same | 48/64/74 | 28% |
| U3 USD/EUR/CNY | 2.9% | +0.6% | +0.11 / +0.15 | +2.3% / -2.0% | -2 / +2 / +6% | 48/63/74 | 28% |
| U3b USD/CNY/RUB eq | 4.5% | -0.2% | +0.06 / -0.10 | +4.2% / -4.4% | -6 / +3 / +10% | 48/62/74 | 29% |
| U3b 50/30/20 | 2.7% | -0.1% | +0.07 / -0.08 | +2.6% / -2.7% | -4 / +2 / +6% | 47/62/74 | 29% |
| U3c USD/EUR/CNY/RUB 1/4 | 3.9% | +0.1% | +0.11 / -0.04 | +4.4% / -3.6% | -5 / +3 / +11% | 47/62/74 | 29% |
| RUB alone (info) | 13.9% | -1.6% | +0.05 / -0.14 | +13.8% / -12.2% | -13 / +6 / +29% | 47/61/75 | 31% |
| U4 US electricity | 4.4% | +3.7% | +0.04 / -0.10 | +4.4% / -3.1% | +3 / +5 / +7% | 49/65/75 | 30% |
| U6 gold (GC=F) | 20.6% | +20.4% | +0.07 / -0.18 | +22.1% / -15.5% | +12 / +37 / +71% | 50/66/81 | 39% |
| U0 coded index (HE) | 25.0% | +11.9% | -0.02 / +0.14 | +31.9% / -22.8% | -46 / +16 / +145% | 51/67/83 | 31% |
| U0 coded, noisy proxies | 81% | +11% | +0.02 / +0.01 | +181% / -64% | -57 / +40 / +237% | 62/80/92 | 58% |
| U5 coded + up-limit 0.25%/d | 12.4% | +11.8% | +0.00 / +0.12 | +7.8% / -19.1% | -39 / +17 / +107% | 50/65/82 | 32% |
Reading: KAS-in-unit vol is 97% in every FX/electricity unit (97-98%); the touch and ICR<100% shares differ from USD by at most 1 point for CNY, baskets and electricity, by -1 for the RUB baskets, by +3 (touch 180 d) and +10 (ICR<100%) for gold (its +20%/yr bull drift in this sample), +4 and +2 for the coded index (hindsight baseline) and +17 / +29 for the noisy-proxy coded index. Unit vs KAS correlation is small in every unit (|corr| <= 0.18, 3.6 years only).
ICR of a 200% vault opened on the date shown, minimum / at day 180 (full table H2): 2024-07-31: USD 101/125, CNY 99/126, basket 100/127, RUB-eq 104/130, 50/30/20 103/128, electricity 102/124, gold 89/111, coded 66/76; 2025-08-01: USD 90/94, CNY 89/91, basket 90/92, RUB-eq 89/91, gold 60/60, coded 99/117. Differences among USD, CNY, baskets and electricity are within +-5 ICR points; gold and the coded index differ by 10-35 points.
Stress episodes, long history 2005-07-25..2026-11-06 (H4/H5). Change over 60 days of the unit's USD value: worst UP / worst DOWN: CNY +6.8% (2023-01) / -7.1% (2018-08); EUR +13.0% / -15.2% (2008); basket USD/EUR/CNY +5.2% / -5.1%; RUB alone +80.6% (2022-05) / -39.4% (2014-12); basket USD/CNY/RUB eq +24.8% / -13.6%; 50/30/20 +14.3% / -8.3%; gold +33.3% / -22.7%; electricity +9.2% / -6.8%. P(60d up > 5/10/20%): CNY 0.5/0/0%, basket 0/0/0, RUB-eq 2.8/0.7/0.2, 50/30/20 1.0/0.3/0, gold 32/12/0.8, electricity 6.5/0/0. P(60d down < -5/-10/-20%): CNY 1.3/0/0, RUB-eq 4.3/0.3/0, gold 14/3.4/0.1.
Named episodes (change of USD value between dates): CNY 2015-08-07..09-07 (fixing reform) -2.3%; CNY 2015-08-10..2016-12-30 -10.6%; CNY 2018-04-17..10-31 -9.9%; CNY 2019-08-01..09-03 (breach of 7) -3.9%; CNY 2022-03-31..11-04 -13.2%; CNY 2005-07..2008-07 +19.0%; 2017-01..09 +7.4%; 2020-05..2021-05 +12.6%. RUB 2014-07-01..2015-01-30 -50.8% (week of 2014-12-10..18: -20.0%); RUB 2022-02-22..03-10 -33.9%; RUB official 2022-03-10..06-24 +117.6%. Basket USD/CNY/RUB eq: -17.2% (2014 crisis), -11.3% (2022-02-22..03-10), +37.4% (2022-03-10..06-24); 50/30/20: -10.4%, -6.8%, +21.9%. USD/EUR/CNY basket: -6.1% (2014), -8.0% (CNY 2022 devaluation window). The CNY devaluations (2015-16, 2018, 2022) are DOWN moves of the unit: they lower the debt value in USD (help the CDP) and cost ENRK holders measured in USD; the CNY revaluations (2005-08, 2017, 2020-21) are the adverse direction for the CDP, up to +12.6% in 13 months, never more than +6.8% in 60 days since 2005. RUB includes both a -50% and a +118% (official rate) in ~8 months.
Source facts (data): FRED vs ECB CNY series agree: level ratio 0.998..1.008, daily-return difference sd 0.10%, max 0.82%, so the series choice moves vol by 0.1 pt. Yahoo spot 2026-11-11: onshore CNY=X 6.6591, offshore CNH=X 6.6688 (offshore 0.15% weaker; ONE observation: no keyless CNH history was obtainable, Yahoo returns a single point and stooq needs JavaScript; onshore vs offshore divergence therefore NOT quantifiable in history here; H.10 and ECB are onshore-rate based). FRED DEXCHUS last observation 2026-11-06 when fetched on 2026-11-11 (publication lag 3-5 days; gaps since 2020: median 1 day, max 5).

## 1b. RUB data handling (U3b)
Source: CBR official rate (an administrative daily rate set by the Bank of Russia, not a tick market rate; XML keyless). Gaps: the file has records for weekend dates (rates set in advance), so there are few missing days; the largest gap between records is 13 days. Official vs market quote (Yahoo RUB=X, unofficial, contains bad ticks, e.g. 5.0 on 2023-03-16): 2014-12-10..24: median -0.09%, p95 |dev| 10.6%, max 10.9% on 2014-12-16 (CBR 58.3 vs market 65.5); 2022-02-22..04-15: median -1.58%, p95 |dev| 13.6%, max 16.3% on 2022-03-10 (CBR 116.1 vs market 138.7); 2023-2026 calm: median -0.03%, p95 |dev| 1.7% (outliers excluded by using the median). The official rate was therefore up to 11-16% below the quoted market rate on stress days; the official series is what the history and simulation use (U3b), and a market-rate version would show larger 2022 moves than reported here. 2022 closure: the Moscow Exchange stock market was shut by decision of the authorities in late Feb-March 2022 (Wikipedia "Russian ruble", secondary) while the CBR kept publishing official rates every day (see the file: 2022-03-01 93.6, 03-04 111.8, 03-10 116.1, 03-11 120.4, 03-25 96.0). Largest 1-record moves of the official rate: +12.5% (2022-03-03), -12.1% (2014-12-19), +12.0% (2022-03-01), +11.6% (2015-01-13). ECB: reference rate for EUR/RUB last published 2022-03-01 and suspended "until further notice" (ECB page text; the eurofxref file ends there too: 4333 RUB observations 2005-04-01..2022-03-01).
Effect of adding RUB to the basket: vol 2.9% (USD/EUR/CNY) -> 4.5% (USD/CNY/RUB equal) or 2.7% (50/30/20); worst 60-day UP 5.2% -> 24.8% / 14.3%; worst DOWN -5.1% -> -13.6% / -8.3%; 365d return p5/p95 -2/+6% -> -6/+10% (eq). ICR history: touch 63 -> 62 / 62%, ICR<100% 28 -> 29 / 29%; ICR minima for the vaults tabulated above moved by +-4 points. Crash simulation: see section 2 (typical windows no effect; worst-window replay raises A3 unbacked 10.2 -> 14.9 (eq) / 13.0 (50/30/20) vs 11.6 for the USD/EUR/CNY basket).

## 2. CRASH SIMULATION (b): unit variant x architecture x scenario
KAS -85%, 60 d. Cell = ENRK p95 (% of ENRK) / unbacked mean (% opening debt value) / kFIAT mean loss (% face). 500 paired paths.
| unit variant | scenario (unit path) | A0 r0 s0 | A3 r3 s30 | A5 r3 s30 S3 | A8 r3 s50 | STACK r3 s70 S3 C1a+C2 |
|---|---|---|---|---|---|---|
| U1 | flat | 25.4 / 9.0 / 0 | 13.8 / 10.2 / 26 | 12.5 / 4.3 / 8 | 5.4 / 11.6 / 22 | 0.0 / 5.4 / 8 |
| U0 | p_base | 26.2 / 9.8 / 0 | 14.1 / 10.4 / 26 | 12.7 / 4.5 / 9 | 5.7 / 11.9 / 22 | 0.1 / 5.7 / 8 |
| U0 | x1.5 | 28.9 / 14.1 / 0 | 17.3 / 15.3 / 33 | 16.2 / 6.7 / 11 | 8.2 / 17.1 / 28 | 0.5 / 8.1 / 10 |
| U0 | x2 | 31.5 / 18.5 / 0 | 20.0 / 19.6 / 37 | 18.4 / 9.0 / 13 | 10.5 / 21.6 / 32 | 0.9 / 11.5 / 13 |
| U5 | p_base | 25.3 / 8.9 / 0 | 13.3 / 9.6 / 25 | 12.3 / 4.1 / 8 | 5.1 / 11.0 / 21 | 0.0 / 5.3 / 7 |
| U5 | x1.5 | 26.5 / 10.7 / 0 | 15.1 / 12.0 / 29 | 13.8 / 5.1 / 9 | 6.3 / 13.5 / 24 | 0.2 / 6.3 / 9 |
| U2 | s0 | 26.1 / 9.4 / 0 | 13.7 / 10.2 / 26 | 12.5 / 4.3 / 8 | 5.6 / 11.6 / 22 | 0.0 / 5.4 / 8 |
| U2 | boot | 25.5 / 9.3 / 0 | 13.7 / 10.2 / 26 | 12.6 / 4.3 / 9 | 5.4 / 11.7 / 22 | 0.0 / 5.5 / 8 |
| U2 | s+10 | 26.7 / 10.2 / 0 | 14.6 / 11.3 / 28 | 13.3 / 4.8 / 9 | 6.1 / 12.8 / 23 | 0.1 / 6.0 / 8 |
| U2 | s+20 | 27.2 / 11.1 / 0 | 15.4 / 12.4 / 29 | 14.2 / 5.3 / 10 | 6.7 / 13.9 / 25 | 0.2 / 6.6 / 9 |
| U2 | s-20 | 24.0 / 7.4 / 0 | 11.9 / 7.7 / 21 | 10.7 / 3.3 / 7 | 4.2 / 9.0 / 18 | 0.0 / 4.3 / 6 |
| U2 | j+20 | 34.1 / 20.1 / 0 | 21.5 / 20.5 / 40 | 19.8 / 10.7 / 17 | 10.7 / 22.2 / 34 | 0.7 / 13.8 / 16 |
| U2 | j-20 | 18.7 / 4.9 / 0 | 7.6 / 5.3 / 18 | 6.4 / 1.7 / 4 | 1.9 / 6.7 / 16 | 0.0 / 2.5 / 4 |
| U3 | boot | 25.9 / 9.3 / 0 | 13.7 / 10.2 / 26 | 12.4 / 4.3 / 9 | 5.5 / 11.7 / 22 | 0.0 / 5.5 / 8 |
| U3 | s+20 | 27.2 / 11.1 / 0 | 15.5 / 12.4 / 29 | 14.2 / 5.3 / 10 | 6.7 / 13.9 / 25 | 0.2 / 6.5 / 9 |
| U3b_eq | s0 | 26.0 / 9.4 / 0 | 13.7 / 10.1 / 26 | 12.4 / 4.3 / 8 | 5.6 / 11.6 / 22 | 0.0 / 5.4 / 8 |
| U3b_eq | boot | 25.4 / 9.3 / 0 | 13.9 / 10.2 / 26 | 12.7 / 4.3 / 9 | 5.5 / 11.7 / 22 | 0.1 / 5.5 / 8 |
| U3b_eq | s+20 | 27.6 / 11.2 / 0 | 15.4 / 12.3 / 29 | 14.2 / 5.3 / 10 | 6.6 / 13.9 / 25 | 0.2 / 6.5 / 9 |
| U3b_532 | boot | 25.2 / 9.3 / 0 | 13.8 / 10.2 / 26 | 12.6 / 4.3 / 9 | 5.5 / 11.6 / 22 | 0.1 / 5.5 / 8 |
| U3b_532 | s+20 | 27.1 / 11.1 / 0 | 15.4 / 12.3 / 29 | 14.2 / 5.3 / 10 | 6.5 / 13.9 / 25 | 0.2 / 6.5 / 9 |
| U4 | s0 | 26.0 / 9.1 / 0 | 14.3 / 10.3 / 26 | 12.7 / 4.4 / 9 | 5.6 / 11.8 / 22 | 0.1 / 5.5 / 8 |
| U4 | boot | 25.5 / 9.0 / 0 | 14.5 / 10.2 / 26 | 13.4 / 4.3 / 9 | 5.5 / 11.7 / 22 | 0.0 / 5.5 / 8 |
| U6 | s0 | 26.3 / 9.9 / 0 | 14.0 / 10.5 / 26 | 12.6 / 4.5 / 9 | 6.0 / 12.0 / 22 | 0.0 / 5.7 / 8 |
| U6 | boot | 26.1 / 9.8 / 0 | 14.3 / 10.7 / 26 | 13.6 / 4.6 / 9 | 6.1 / 12.1 / 22 | 0.0 / 5.8 / 8 |
| U6 | s+20 | 27.6 / 11.9 / 0 | 15.4 / 12.7 / 29 | 14.5 / 5.5 / 10 | 7.3 / 14.3 / 25 | 0.2 / 6.9 / 9 |
| U2 | worst+ (worst historical 60d window) | 25.6 / 9.5 / 0 | 14.0 / 10.7 / 26 | 12.8 / 4.5 / 9 | 5.8 / 12.2 / 22 | 0.1 / 5.7 / 8 |
| U2 | worst- (worst historical 60d window) | 23.9 / 7.7 / 0 | 12.9 / 8.9 / 23 | 11.6 / 3.8 / 8 | 4.9 / 10.3 / 20 | 0.0 / 4.8 / 7 |
| U3 | worst+ (worst historical 60d window) | 26.5 / 10.3 / 0 | 14.8 / 11.6 / 28 | 13.6 / 4.9 / 9 | 6.1 / 13.1 / 24 | 0.1 / 6.1 / 8 |
| U3 | worst- (worst historical 60d window) | 24.9 / 8.4 / 0 | 13.3 / 9.6 / 25 | 12.1 / 4.0 / 8 | 5.2 / 11.1 / 21 | 0.0 / 5.2 / 7 |
| U3b_eq | worst+ (worst historical 60d window) | 28.6 / 13.7 / 0 | 17.2 / 14.9 / 32 | 15.9 / 6.4 / 11 | 8.2 / 16.6 / 28 | 0.5 / 7.9 / 10 |
| U3b_eq | worst- (worst historical 60d window) | 24.6 / 8.4 / 0 | 13.4 / 9.6 / 25 | 12.1 / 4.0 / 8 | 5.2 / 11.0 / 21 | 0.0 / 5.1 / 7 |
| U3b_532 | worst+ (worst historical 60d window) | 27.5 / 11.7 / 0 | 15.8 / 13.0 / 30 | 14.8 / 5.5 / 10 | 7.1 / 14.6 / 25 | 0.2 / 6.8 / 9 |
| U3b_532 | worst- (worst historical 60d window) | 25.1 / 8.7 / 0 | 13.5 / 9.9 / 25 | 12.2 / 4.2 / 8 | 5.3 / 11.3 / 21 | 0.0 / 5.3 / 7 |
| U4 | worst+ (worst historical 60d window) | 25.4 / 9.0 / 0 | 13.8 / 10.2 / 26 | 12.5 / 4.3 / 8 | 5.4 / 11.7 / 22 | 0.0 / 5.5 / 8 |
| U4 | worst- (worst historical 60d window) | 25.4 / 8.9 / 0 | 13.8 / 10.1 / 26 | 12.5 / 4.3 / 8 | 5.4 / 11.6 / 22 | 0.0 / 5.4 / 8 |
| U6 | worst+ (worst historical 60d window) | 26.8 / 11.4 / 0 | 15.4 / 12.7 / 29 | 14.6 / 5.5 / 10 | 6.9 / 14.3 / 25 | 0.2 / 6.8 / 9 |
| U6 | worst- (worst historical 60d window) | 23.7 / 7.4 / 0 | 12.6 / 8.6 / 23 | 11.5 / 3.7 / 8 | 4.7 / 9.9 / 19 | 0.0 / 4.7 / 7 |

KAS -70%, 60 d, same cell format.
| unit variant | scenario | A0 | A3 | A5 | A8 | STACK |
|---|---|---|---|---|---|---|
| U1 | flat | 21.2 / 5.6 / 0 | 8.0 / 5.3 / 14 | 7.4 / 2.1 / 4 | 1.9 / 6.1 / 11 | 0.0 / 2.8 / 4 |
| U0 | p_base | 21.1 / 6.1 / 0 | 9.3 / 6.1 / 16 | 7.9 / 2.7 / 6 | 2.7 / 7.0 / 13 | 0.0 / 3.6 / 5 |
| U0 | x1.5 | 23.9 / 9.0 / 0 | 11.3 / 9.0 / 21 | 10.3 / 3.7 / 7 | 3.6 / 10.3 / 17 | 0.0 / 4.7 / 6 |
| U0 | x2 | 25.9 / 11.7 / 0 | 14.0 / 12.8 / 26 | 12.6 / 5.3 / 8 | 5.5 / 14.3 / 22 | 0.1 / 6.4 / 7 |
| U5 | p_base | 21.6 / 5.8 / 0 | 8.5 / 5.6 / 15 | 7.6 / 2.4 / 5 | 2.3 / 6.4 / 12 | 0.0 / 3.2 / 5 |
| U5 | x1.5 | 21.6 / 6.2 / 0 | 9.2 / 6.3 / 16 | 8.4 / 2.6 / 5 | 2.5 / 7.4 / 13 | 0.0 / 3.4 / 5 |
| U2 | s0 | 21.3 / 5.6 / 0 | 8.0 / 5.3 / 14 | 7.2 / 2.1 / 4 | 1.8 / 6.1 / 12 | 0.0 / 2.8 / 4 |
| U2 | boot | 21.2 / 5.7 / 0 | 7.9 / 5.3 / 14 | 7.3 / 2.1 / 4 | 1.9 / 6.1 / 12 | 0.0 / 2.8 / 4 |
| U2 | s+10 | 21.5 / 6.0 / 0 | 8.7 / 5.9 / 15 | 8.0 / 2.4 / 5 | 2.2 / 6.9 / 13 | 0.0 / 3.2 / 4 |
| U2 | s+20 | 21.9 / 6.6 / 0 | 9.2 / 6.6 / 16 | 8.5 / 2.7 / 5 | 2.6 / 7.7 / 14 | 0.0 / 3.6 / 5 |
| U2 | s-20 | 20.6 / 5.1 / 0 | 7.2 / 4.4 / 13 | 5.8 / 1.6 / 3 | 1.1 / 5.0 / 10 | 0.0 / 2.1 / 3 |
| U3 | boot | 21.2 / 5.6 / 0 | 7.9 / 5.3 / 14 | 7.6 / 2.1 / 4 | 1.8 / 6.1 / 12 | 0.0 / 2.8 / 4 |
| U3b_eq | boot | 21.2 / 5.7 / 0 | 8.2 / 5.4 / 14 | 7.4 / 2.1 / 4 | 2.0 / 6.2 / 12 | 0.0 / 2.9 / 4 |
| U3b_eq | s+20 | 22.0 / 6.6 / 0 | 9.0 / 6.6 / 16 | 8.5 / 2.7 / 5 | 2.6 / 7.7 / 14 | 0.0 / 3.6 / 5 |
| U3b_532 | boot | 21.1 / 5.7 / 0 | 8.2 / 5.3 / 14 | 7.4 / 2.1 / 4 | 2.0 / 6.1 / 12 | 0.0 / 2.8 / 4 |
| U4 | boot | 21.3 / 5.7 / 0 | 8.2 / 5.3 / 14 | 7.4 / 2.1 / 4 | 1.8 / 6.1 / 12 | 0.0 / 2.8 / 4 |
| U6 | boot | 21.2 / 6.1 / 0 | 8.8 / 5.9 / 15 | 7.8 / 2.4 / 5 | 2.1 / 6.8 / 13 | 0.0 / 3.2 / 4 |
| U6 | s+20 | 22.9 / 7.3 / 0 | 10.6 / 7.3 / 18 | 9.4 / 3.1 / 6 | 3.1 / 8.4 / 15 | 0.0 / 4.0 / 5 |


Full per-cell tables (ENRK p95 [CI] / p99, kFIAT mean / p95, latent p95 with the share of paths with a latent hole, unbacked mean, junior net, holder returns): SP/econ/w1/sim/tables_w1.txt (T1-T10). Pickles WB.pkl (395 cells), WC.pkl (373), WD.pkl (60), 500 paths each.
Paired differences vs U1 (USD), architecture A3, KAS -85% (T3; 95% CI; unbacked mean in points of opening debt value): CNY s0 +0.00 [-0.02,+0.03], CNY boot +0.05 [+0.02,+0.07], USD/EUR/CNY boot +0.04 [+0.01,+0.07], USD/CNY/RUB eq s0 -0.03 [-0.07,+0.01] and boot +0.04 [-0.01,+0.09], 50/30/20 boot +0.03 [-0.00,+0.06], electricity s0 +0.15 [+0.11,+0.20], gold s0 +0.34 [+0.19,+0.53] and boot +0.50 [+0.36,+0.65]; U0 p_base +0.26 [+0.06,+0.48], U0 x1.5 +5.17, U0 x2 +9.47; U5 p_base -0.58 [-0.73,-0.43], U5 x1.5 = x2 +1.79 (the 0.25%/day limit reaches 1.0025^60 = 1.162 in both ramps). ENRK p95 differences vs U1 for all stochastic/boot FX and basket variants: -0.1..+0.1 with CIs containing 0 (A3 CNY s0 -0.1 [-0.2,+0.4]).
Unit shock ramp, A3: +5 / +10 / +20% -> unbacked +0.5 / +1.1 / +2.2 (CI +-0.05), ENRK p95 +0.4 / +0.8 / +1.6; -20% -> -2.4 and -1.9. About +0.11 unbacked points per 1% of final revaluation when the move is spread over the 60 days. The same +20% as a STEP on crash day 5 (j+20): unbacked +10.3 [+10.1,+10.5], ENRK p95 21.5 vs 13.8, kFIAT mean 39.8 vs 25.7 (about 4.7 times the ramp effect), and -20% step: -4.9. In every row the effect scales the same way for A0, A5, A8, STACK (paired deltas in T3).
Worst historical 60-day window replay (WD), A3 unbacked / ENRK p95 (USD reference 10.2 / 13.8): CNY up (+6.8%) 10.7 / 14.0, CNY down (-7.1%) 8.9 / 12.9; USD/EUR/CNY up (+5.2%) 11.6 / 14.8; USD/CNY/RUB eq up (+24.8%, the 2022 official-rate rebound) 14.9 / 17.2 / latent p95 4.3, kFIAT mean 32.2; 50/30/20 up (+14.3%) 13.0 / 15.8; the down windows (-13.6% / -8.3%) 9.6 / 13.4 and 9.9 / 13.5; gold up (+33.3%) 12.7 / 15.4, down (-22.7%) 8.6 / 12.6; electricity worst windows 10.2 / 13.8 (the monthly step falls on the last day of the window: no effect).

## 3. What depends on the unit and what does not (model outputs)
Unit-independent (differences within the paired CIs or below 0.5 point): (1) the ordering of architectures in ENRK p95 at -85%: A0 25-26 > A3 13.7-14.5 > A5 12.4-13.6 > A8 5.4-6.1 > STACK 0.0-0.1 for every stochastic, bootstrap and typical-window unit (CNY, both baskets, electricity, gold); (2) no architecture reaches the v1 SURVIVE label (ENRK p95 <= 2, latent p95 <= 1, unbacked <= 3) at -85% on any unit (best STACK: unbacked 5.4); (3) the redemption-schedule cushion: A3 -85% with redemption OFF gives ENRK p95 / unbacked / kFIAT 20.0 / 15.6 / 35.0 (U1), 20.1 / 15.9 / 35.3 (U0 p_base), 20.0 / 15.7 / 35.1 (CNY boot), 19.8 / 15.7 / 35.1 (USD/CNY/RUB eq boot), 20.5 / 16.2 / 35.7 (gold boot) vs 13.8 / 10.2 / 25.7 (U1, on): the ~5.4-point cushion is unit-blind and still present; (4) the fee cliff: 0 calm-year liquidations at r <= 3 for every unit (the calm year is simulated at I=1), r > 3 not simulated, so the 153% opening-ICR artefact does not enter any figure here; (5) KAS vol 97% dominates: a unit with 3% vol (CNY, baskets) has 1/30 of it.
Unit-dependent: (a) DRIFT/SHOCK direction and SPEED inside the 60-day crash: ramps of 5-20% move unbacked by +-0.5..2.4 points, a 20% step on day 5 by +10 / -5; (b) the fat tail of the unit: a 2022-type RUB rebound inside the basket moves A3 unbacked +4.7 (equal weights) or +2.8 (50/30/20) vs +0.5 for the CNY-only and +1.4 for the USD/EUR/CNY worst windows, while typical RUB-basket windows (boot) move nothing measurable (+0.04 [-0.01,+0.09]); (c) gold: its 20%/yr drift and 21% vol add +0.34..+0.50 unbacked and +0.2..+1.1 ENRK p95 in the plain crash (CIs include 0), +2.5 in the worst up-window; (d) U0 (coded index) is a different order of magnitude: p_base +0.26, x1.5 +5.2, x2 +9.5, and the SIGN of the ENRK holder's USD outcome follows the index (x2: +86% mean); (e) U5 (slow-up) limits the rise inside 60 days to +16.2%: unbacked +1.8 instead of +5.2 / +9.5, and p_base -0.58; its cost is the lagged USD value to holders (ENRK holder USD mean +11.7% instead of +42% / +87%) and, in history, an 8% 1-day drop still passes through (worst 1-day down -7.7%); (f) the labels at the edge: at -70% STACK is unbacked 2.8 (U1, CNY s0, USD/EUR/CNY boot, electricity boot; 2.8-2.9 for the RUB baskets boot) vs the 3.0 limit, and 3.2 at CNY +10, 3.6 at +20, 3.2 gold boot, 3.6 U0 p_base: the SURVIVE label at -70% flips with a unit revaluation of about +10% or with the coded index.
Summary for the owner's question, as model output only: with the unit's own measured behaviour (vol 3-4.5%, drift within +-1%/yr, 60-day moves within +-7% for CNY, +-5% for USD/EUR/CNY), the crash outcome of the CDP is the same as with a USD unit within simulation noise. The unit changes the outcome only through a large, fast revaluation of the unit against USD inside the crash (RUB-type moves, gold-type drift, the coded index), and it moves the USD value of what an ENRK holder owns one-for-one.

## 4. RE-BASE (c) of the older conclusions, no hidden cushion (WC: r in {0,1,2,3}% x s in {0,15,30,50}% D1/S1, KAS -85%, per unit; SP/econ/w1/sim/tables_w1.txt T5-T9)
Calm-year junior income is the same for every unit (the calm year is at I=1; income is in units): per r=0/1/2/3 and s=30: 0 / 3.3 / 6.7 / 10.0 % of face.
| unit scenario | E_w (w=10%, s=30) at r=0 / 1 / 2 / 3 (% of face) | ENRK p95 at s = 0/15/30/50, r=3 |
|---|---|---|
| U1 USD | -2.7 / +0.6 / +3.9 / +7.4 | 24.0 / 19.2 / 13.8 / 5.4 |
| U0 p_base | -2.8 / +0.5 / +3.9 / +7.4 | 24.4 / 19.7 / 14.1 / 5.7 |
| U0 x1.5 | -3.5 / -0.2 / +3.1 / +6.7 | 27.2 / 22.6 / 17.3 / 8.2 |
| U5 p_base / x1.5 | -2.7 / +0.7 / +4.0 / +7.6 ; -3.0 / +0.3 / +3.6 / +7.2 | 23.7 / 18.6 / 13.3 / 5.1 ; - / - / 15.1 / 6.3 |
| U2 CNY s0 / boot / s+10 | -2.8 / +0.6 / +3.9 / +7.4 ; same ; -2.9 / +0.4 / +3.7 / +7.3 | 13.7 / 5.6 at s=30/50 (s0); s+10: 14.6 / 6.1 |
| U3 USD/EUR/CNY, U3b eq and 50/30/20 (s0 / boot) | -2.8 / +0.6 / +3.9 / +7.4..7.5 | s=30: 13.7-13.9; s=50: 5.5-5.6 |
| U4 electricity s0 / boot | -2.7 / +0.6 / +3.9 / +7.4 | s=30: 14.3 / 14.5 |
| U6 gold s0 / boot / s+10 | -2.9 / +0.5 / +3.8 / +7.4 ; -2.8 / +0.5 / +3.8 / +7.4 ; -3.0 / +0.3 / +3.7 / +7.2 | s=30: 14.0 / 14.3 / 14.9 |
Voluntary equilibrium junior share s* (% of debt; D1/S1; crash probability w ASSUMED; interpolation on s in 15/30/50; "none" = even s=15 fails the hurdle):
| r, w | hurdle h=5% | h=10% | h=20% |
|---|---|---|---|
| r=3, w=5% | 50 | 28 | none |
| r=3, w=10% | 44 (U0 x1.5: 40) | 26 (25) | none |
| r=3, w=20% | 30 (27) | 22 (19) | none |
| r=2, w=10% | 27 (26) | 16 (U0 x1.5: none) | none |
| r=1, any w | none (16 at w=5%) | none | none |
All CNY, basket, RUB-basket, electricity and gold rows are within +-1 point of the U1 values (e.g. r=3, w=10%, h=10%: 26 for U1, 25-26 elsewhere). Self-consistency (v1): the voluntary s* of 22-28% at h=10% delivers ENRK p95 about 14-19 (A3, s=15..30) against 5.4 at s=50: unchanged by the unit.
T2 intersection r_clear (fee at which a 30% voluntary junior clears the hurdle, w=10%; linear interpolation on r in 0..3; beyond 3 a linear EXTRAPOLATION of E_w, flagged because r > 3 sits beyond the tested range): h=5%: 2.31 (U1), 2.28-2.37 (every other unit, 2.52 for U0 x1.5); h=10%: ">3, extrapolated 3.7" (U1), 3.7-3.9; h=20%: ">3, extrapolated 6.5", 6.5-6.7. Cushioned values in T2: 1.8 / 3.3 / 6.8. Surviving borrower demand D(r)/D(0) at min(r_clear, 3%) (ICR 250, T=1, X=0, t2 sets): L8 0.76 / 0.70 / 0.70, L4 0.61 / 0.53 / 0.53, Pareto 0.55 / 0.48 / 0.48 (cushioned T2: L8 .81 / .68 / .45; the h=20 column is capped at r=3 and is therefore an upper bound). Demand parameters are ASSUMED (t2).
What this re-base shows: the neutral-index (hidden-cushion-free) levels reproduce v1/V5 on USD and are the same for CNY, baskets (including RUB), electricity and gold within +-0.3 points of E_w; only the coded-index ramp (U0 x1.5, x2) and a large unit revaluation shift them (E_w at r=3: 7.4 -> 6.7).

## 5. What an ENRK holder gets, per unit (model/data outputs)
(i) Without a crash, from history (365-day change of the unit's USD value, p5 / median / p95): USD 0; CNY -4 / +1 / +7%; USD/EUR/CNY -2 / +2 / +6%; USD/CNY/RUB eq -6 / +3 / +10%, 50/30/20 -4 / +2 / +6%; electricity +3 / +5 / +7%; gold +12 / +37 / +71% (sample drift); coded index -46 / +16 / +145%; with up-limit -39 / +17 / +107%. Long history 180 days (2005-2026), P(unit loses > 10% in 180 d): CNY 0.4%, USD/EUR/CNY basket 0, RUB-eq 2.6%, 50/30/20 0.0% (> 5%: 12.9% / 6.5%), gold 8.9%.
(ii) In the KAS -85% crash, architecture A3 (USD terms = final unit value x (1 - ENRK loss) - 1; unit terms = -ENRK loss); mean / p5 / p95: USD unit -3.2% / -13.6% / 0; CNY s0 -3.0% / -13.4% / +1.5%; USD/CNY/RUB eq boot -3.1% / -12.8% / +2.4%; gold boot -1.0% / -15.1% / +12.5%; coded p_base -3.3% / -18.6% / +15.4%. Unit terms identical to USD within 0.1 point for FX/basket units (-3.2% mean, p5 -13.7%). Adverse unit moves (CNY down 10%/20%): USD mean -12.4% / -21.8%, p5 -21.2% / -29.1%; P(USD loss > 20%) 6.6% / 70% (by construction, the unit loss alone). kFIAT holder, same crash: -25.6% mean / -54.5% p5 (USD, CNY s0); -20.2% mean with CNY +10% (the unit gain offsets); -31.1% with CNY -10%.
(iii) Borrower side is the mirror: a unit that rises raises the debt value in USD (CNY +10%: unbacked +1.1, ENRK p95 +0.8 pts) and a unit that falls helps the CDP.

## 6. FX oracle requirement and trust notes (facts with sources, no conclusion)
- Extra input: U1 needs the KAS/USD price only. U2-U6 need the unit's USD value as a second input (or KAS priced directly in the unit, a product of two off-chain numbers). The ENRK oracle in the reports v3/v4 is a signer-controlled sweep of price UTXOs: an FX value or a pre-multiplied price would be one more signed number from the same publisher set; no FX-specific staleness, error or manipulation case is modelled here.
- Keyless sources found and what they are (GET 2026-11-11): ECB euro reference rates (eurofxref-hist.csv; daily on TARGET days; includes USD and CNY; RUB suspended since 2022-03-01, ECB page text: "not in a position to set a reference rate that is representative of prevailing market conditions ... suspend ... until further notice"); FRED H.10 DEXCHUS / DEXUSEU (3-5 day publication lag observed); CBR official USD/RUB (see section 1b); US retail electricity (FRED APU000072610, monthly, BLS; lag 2-6 weeks ASSUMED); gold: no official keyless daily series found (FRED LBMA ids 404), only Yahoo GC=F (unofficial futures). Yahoo is unofficial and contains bad ticks (RUB=X 5.0 on 2023-03-16).
- Public oracle networks (listing only; whether any can be consumed by a Kaspa covenant is not assessed): Pyth Hermes (api GET, asset_type fx / metal): FX.USD/CNY, FX.USD/CNH, FX.EUR/USD, Metal.XAU/USD present; query "RUB" returns no feed. Chainlink reference-data directory: Ethereum mainnet CNY / USD, EUR / USD, XAU / USD; Polygon CNY / USD; no RUB or CNH feed in the lists that parsed (BSC file did not parse, Arbitrum list empty).
- CNY onshore vs offshore: 6.6591 vs 6.6688 (0.15%) on 2026-11-11 (one observation); no keyless CNH history; the H.10 and ECB series are the onshore rate; how a CNY fixing/band regime would affect a feed is not verified here.
- RUB leg: (a) feed availability: official CBR XML keyless and complete since 2005 (5409 records); the ECB series stops 2022-03-01; Pyth has no RUB feed; market quote and official rate differed by up to 10.9% (2014-12-16) and 16.3% (2022-03-10) in the stress windows measured. (b) Convertibility/market structure (secondary, Wikipedia "Russian ruble" extract fetched 2026-11-11): in March 2022 the authorities temporarily shut the Moscow Stock Exchange, required companies to sell 80% of FX reserves and prohibited foreigners from liquidating assets in Russia; on 2024-07-15 the CBR closed the statistics of the over-the-counter currency market; on 2024-11-27 the Bank of Russia halted foreign-currency purchases from 28 November to year-end. (c) Sanctions (primary page read): OFAC recent action 2022-02-28 "Issuance of Russia-related Directive 4 ... Treasury Prohibits Transactions with Central Bank of Russia" (ofac.treasury.gov/recent-actions/20220228). The EU regulation text (EUR-Lex CELEX 32014R0833) could not be retrieved (HTTP 202, empty body), so no EU statement is made. Whether publishing, signing or relying on a CBR-derived rate is covered by any sanctions rule or licence: NOT assessed (legal question; no source consulted); the existence of these measures is the only fact recorded.

## 7. Limits (what these results do not say)
- Unit path independent of the KAS path (measured correlations are small but from 3.6 years). Pre-year at I=1: unit vol in the calm year (opening-ICR drift, junior income in USD, calm-year liquidations) is not modelled; junior income is in unit terms. Liquidator capacity is in units (5% of opening debt units/day), not re-expressed in USD when the unit moves; the V1 "adv" capacity mode (USD-valued capital) was not used. Oracle lag, error, staleness and FX-feed manipulation are not modelled (V5 blind spot 3 persists). Passive borrowers, permanent sqrt impact, uncalibrated capacity 5%/day and ADV 40M: all V5 caveats apply; levels are uncalibrated, orderings stable.
- Shocks are scenarios, not forecasts; ramp and step timing (day 5, all 60 days) are ASSUMED; electricity steps on days 10 and 40 ASSUMED; Gaussian diffusion understates tails (hence boot and worst-window replays); boot windows overlap (~100 independent); the 2005-2026 sample contains one 2008 EUR, one 2014 and one 2022 RUB episode, two CNY regimes. Gold drift +20%/yr is a 3.6-year bull sample; GC=F is a futures continuation. RUB official rate understates the market move on stress days (section 1b). No CNH history.
- Latent p95 is a knife-edge quantile (V5): the share of paths with a latent hole (3-6% at A3 -85%) is printed next to it in T1/T2; labels use p95 as in v1. The U5 x1.5 / x2 rows coincide by construction. The kFIAT write-down form A1 (face) is assumed.
- Holder returns: USD outcome approximated at the final unit value; income is not included in section 5 (ii) (the junior side is in section 4). The crash probability w and hurdles h are assumed (v1 convention). Borrower demand D(r) is the ASSUMED t2 model.
- Not done: qgate, reviewer run, code map, handoff entry (scratch modelling); no re-implementation; no design decision made or implied.

## 8. Reproduction (cwd = SP/econ/w1 for data, SP/econ/w1/sim for the simulation; python3 -B, numpy; <=3 processes)
Data (public GETs 2026-11-11; saved in w1/data): FRED https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXCHUS (and DEXUSEU); https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip; https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1=01/01/2005&date_req2=11/11/2026&VAL_NM_RQ=R01235 (-> data/cbr_usdrub.csv: date, rate); https://query1.finance.yahoo.com/v8/finance/chart/GC=F?period1=946684800&period2=1794400000&interval=1d (also RUB=X, CNH=X, CNY=X); Pyth https://hermes.pyth.network/v2/price_feeds?asset_type=fx ; Chainlink https://reference-data-directory.vercel.app/feeds-mainnet.json ; ECB page https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html ; OFAC https://ofac.treasury.gov/recent-actions/20220228.
    cd SP/econ/w1 ; python3 -B units_data.py > units_hist_out.md          # history tables H1-H6 + units_hist.json
    python3 -B w1_boot.py                                                 # boot.npz (7715 historical 60-day windows per unit)
    python3 -I -B rub_divergence.py                                       # official vs market RUB
    cd sim ; python3 -B check_v1.py ; python3 -B check_w1.py              # "check_v1: OK", "check_w1: OK ... differences 0"  (v6: cd ../v6chk ; python3 -B check.py ; python3 -B check_t3.py ; python3 -B check_v6.py)
    python3 -B w1_run.py --exp WB --out WB.pkl --paths 500 --procs 3      # ~40 min; WC ~35 min; WD ~5 min
    python3 -B w1_run.py --exp WC --out WC.pkl --paths 500 --procs 3 ; python3 -B w1_run.py --exp WD --out WD.pkl --paths 500 --procs 3
    python3 -B analyze_w1.py > tables_w1.txt ; python3 -B table_main.py > table_main.md
Files: sim/stress_fee.py (V1 simulator + path mode + idx_max_up_step), w1_exp.py (cells), w1_run.py, analyze_w1.py, table_main.py, check_w1.py, v1ref/ (V1 simulator for the check), base0/, p3ref/, v6ref/; data/, web/ (oracle-listing GET outputs), units_data.py, w1_boot.py, rub_divergence.py(+_out.txt). No background process left.
