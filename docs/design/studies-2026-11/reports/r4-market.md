# R4 - Market data for the two unmeasured parameters (impact_coefficient, daily_liquidation_capacity)
Date of fetch: 2026-11-10 ~16:40 UTC. Public GET only. Raw data: scratchpad/raw/ (ob_*.json order books, t_*.json tickers, kc_*.json KuCoin daily candles, cg365.json CoinGecko 365d, hr/sup/dag/fee.json Kaspa REST). Script: scratchpad/ob_analyze.py, output ob_result.txt.

## 1. Repo assumptions read (tests/backtesting/stress_test_crash.py)
daily_volume_kas 40,000,000; impact_coefficient 0.08 (impact = k*sqrt(dumped/ADV), applied as a multiplicative price factor); daily_liquidation_capacity 0.05 of opening debt/day; jump 4%/day of -25%; crash 60 days, drawdowns up to -85%. "~100M KAS in system" is not a literal constant in this file (grep found none) - taken from the task brief.

## 2. Price, supply (VERIFIED unless noted)
- Price 0.02951 USD, mcap 820.5M USD, 24h volume 6.74M USD (CoinGecko /coins/kaspa, 2026-11-10). ATH 0.2074 (2024-07-31).
- Circulating 27.80B KAS (CoinGecko 27,802,072,679; Kaspa REST api.kaspa.org/info/coinsupply 27,803,180,266; max 28.70B). 100M KAS = 0.36% of supply = ~2.95M USD.
- Daily series: CoinGecko 365d (cg365.json) has glitches (e.g. 2026-03-12 -45%, 2026-03-13 +94%, 2026-02-10 -34%/02-12 +53%) that KuCoin candles do not show -> treat CoinGecko daily returns as SECONDARY/unreliable for tails. Use KuCoin KAS-USDT daily candles (1285 days, 2023-05-06..2026-11-10) as the drawdown source.
- KuCoin KAS-USDT drawdowns (VERIFIED, api.kucoin.com/api/v1/market/candles):
  - Max drawdown -87.7% (peak 2024-07-31 -> trough 2026-08-13, ~25 months). Close ATH 0.2056, close min 0.01359 (2023-05-23).
  - Episodes >30%: 13 since 2023-05; deepest: -66.7% (2025-07-21 -> 2025-11-22, 124d), -53.5% (2025-11-27 -> 2026-02-05, 70d), -49.5% (2024-07-31 -> 2024-11-04), -48.7% (2023-05-06 -> 05-23, 17d), -48.4% (2025-05-13 -> 06-22), -46.4% (2025-02-16 -> 03-10, 22d), -46.1% (2025-01-17 -> 02-06, 20d). Latest: -40.1% (2026-09-26 -> 2026-11-08, 43d, ongoing).
  - Worst rolling peak-to-close: 7d -37.0% (to 2025-02-06), 14d -40.0% (to 2023-05-23), 30d -47.3% (to 2026-02-05), 60d -62.1% (to 2025-03-10).
  - Only one daily close-to-close fall below -20% in 1285 days: -24.9% on 2025-10-10. Daily sd (close-to-close) 4.9%.
- Intraday gaps are larger than close-to-close; not measured (UNVERIFIED).

## 3. Analog small/mid-cap PoW (KuCoin USDT daily, window 2022-10-03..2026-11-10, 1500 days; RVN had no KuCoin data)
Max drawdown / worst 60d / worst day / daily sd: ETC -84.1% / -46.9% / -23.9% / 3.9%; ERG -93.3% / -64.7% / -25.5% / 4.5%; ZEC -71.8% (2025-11-16 -> 2026-03-07, 111d) / -62.1% / -26.4% / 5.6%; DOGE -85.6% / -62.9% / -22.1% / 4.5%; LTC -70.1% / -48.7% / -22.8% / 3.7%; BCH -72.6% / -59.1% / -15.3% / 4.2%. KAS own: -87.7% / -62.1% / -24.9% / 4.9%.
Reading: in ~4 years, no analog fell more than ~-65% in any 60-day window or more than ~-26% in a day (daily closes). A -85% crash in 60 days is outside the observed sample (a severe stress, not a historical replay). Long-run decay of -85..-93% over 1-2 years IS observed (KAS, ETC, ERG, DOGE).
Limit: survivorship bias (coins still listed); delisted/dead PoW coins are absent, so tails are understated.

## 4. Volume and wash trading
- CoinGecko KAS volume last 365d (USD/day, SECONDARY): p10 7.2M, median 16.0M, p90 33.0M; last-30d mean 11.9M; now 6.7M (~228M KAS). Repo's 40M KAS/day = ~1.2M USD/day.
- Top-6 venues (Bybit, KuCoin, Kraken, Gate, Bitget, MEXC) = 2.81M of 6.7M USD = 42% of aggregator volume (CoinGecko /coins/kaspa/tickers, 2026-11-10). The remaining ~58% is spread over ~15+ small venues with trust score null, each 0.1-0.4M USD/day - the part most exposed to inflation.
- 24h KAS volume from venue APIs (VERIFIED, same time): Kraken 15.6M, KuCoin 26.7M, Bybit 29.8M, Gate 10.6M, MEXC 6.2M (Bitget not fetched) = ~89M KAS (~2.6M USD). Kraken (regulated) volume matches CoinGecko's Kraken row (0.46M USD) -> not inflated there.
- Wash-trading estimates: no KAS-specific study found. SECONDARY: Cong, Li, Tang, Yang, "Crypto Wash Trading" (Management Science 2023; nber.org/papers/w30783): unregulated exchanges average >70% wash volume, regulated ~none. Applying this as a bound (my arithmetic, UNVERIFIED for KAS): real ADV between ~30% (if all non-top-6 volume and a large part of top-6 is fake) and ~100% of reported -> roughly 70M-230M KAS/day now, i.e. 1.75x-5.7x the repo's 40M. A conservative design value is ~90M KAS/day (the sum of the five venue-API volumes above plus Bitget), which excludes the long tail.

## 5. Order books, snapshot 2026-11-10T16:40:53Z (VERIFIED; Kraken KASUSD, KuCoin, Gate, MEXC, Bybit, Bitget KAS/USDT; best bid ~0.0296)
Bid depth in KAS (USD) within 1% / 2% / 5% of best bid:
- Kraken 4.55M / 8.21M / 9.21M (134k/241k/269k USD)
- Bybit 0.90M / 1.42M / 2.03M (27k/42k/59k)
- KuCoin 0.65M / 0.99M / 1.35M (19k/29k/39k)
- Gate 0.24M / 0.75M / 1.43M (7k/22k/42k)
- Bitget 0.45M / 0.50M / 1.22M (13k/15k/35k)
- MEXC 0.13M / 0.49M / 0.94M (4k/14k/27k)
- Combined (6 venues): ~6.9M / ~11.9M / ~16.2M KAS = ~0.2M / 0.35M / 0.48M USD.
Per venue, selling f of that venue's own 24h volume into its own book: average slippage (k = slippage/sqrt(f)):
| venue | 0.1% | 1% | 5% |
| Kraken | 0.00% | 0.05% (k .005) | 0.07% (k .003) | (Kraken has large resting bids; its book is deep relative to its volume)
| KuCoin | 0.00% | 0.08% (k .007) | 1.23% (k .055) |
| Gate | 0.06% (k .019) | 0.39% (k .039) | 1.04% (k .047) |
| MEXC | 0.04% (k .013) | 0.11% (k .011) | 0.70% (k .031) |
| Bybit | 0.05% (k .015) | 0.30% (k .030) | 0.99% (k .044) |
Aggregate (all 6 books merged, sell market order; ADV taken as CoinGecko 228M KAS): 
| order (KAS) | % of 228M ADV | average slippage | last fill below best bid |
| 0.1M | 0.04% | 0.08% | -0.1% |
| 1M | 0.44% | 0.22% | -0.3% |
| 2.28M | 1% | 0.28% (k_avg 0.028) | -0.4% (k_marginal 0.04) |
| 5M | 2.2% | 0.43% | -0.7% |
| 11.4M | 5% | 0.94% (k_avg 0.042) | -1.7% (k_marginal 0.076) |
| 20M | 8.8% | 2.33% | -5.7% |
| 40M | 17.5% | book exhausted at 36.8M: 9.4% avg, -32.5% at last level | |
| 100M | 44% | 63M unfilled | |
(Cost for 0.1%/1%/5% of ADV: 0.1% = 228k KAS = ~6.7k USD at ~0.1% slippage; 1% = 2.3M KAS = 67k USD at 0.28%; 5% = 11.4M KAS = 338k USD at 0.94%.)
Implied coefficient from the merged book, calm hour: average-price k ~0.03-0.04; marginal-price k ~0.04 (1%) to ~0.076 (5%); beyond ~9% of ADV the book is no longer sqrt-like (convex: -5.7% at 8.8%, -32% at 17.5%).
Caveats: single snapshot, calm (price -1.2% 24h), displayed (not hidden) liquidity, top-of-book only to the API depth (KuCoin 100 levels, Gate 100, Bybit 200, Bitget 150; Kraken/MEXC contain stub bids at 1e-5, excluded). Merging ignores that it is a single seller crossing six venues at once, and ignores DEX/Kaspa-native liquidity (not measured).

## 6. Chain data relevant to the peg index (VERIFIED, api.kaspa.org, 2026-11-10)
- Hashrate 335 PH/s (info/hashrate); difficulty 1.68e16; largest recorded hashrate in the API "max" field 1,592 PH/s (block 2025-01-31) -> current is ~-79% from that recorded peak. Unit and the "max" semantics rely on the API doc; SECONDARY. Price relation not computed.
- Block reward 1.9445 KAS; next halving-step 2026-12-05 to 1.8354 KAS (info/halving). Emission is deterministic.
- Fee estimate: all buckets at the floor, feerate 100, ~0.003s -> fees are minimal; no fee-market signal. Energy-proxy data (electricity price, ASIC efficiency) NOT fetched: not available from public keyless APIs I used (UNVERIFIED / gap).
- No KAS hashrate time series fetched (the keyless endpoint gives point values); history needs periodic collection (see section 9).

## 7. Verdicts vs repo assumptions
| parameter | repo | data | verdict |
| daily_volume_kas | 40M KAS | reported 228M now; 12m median ~16M USD (~400-540M KAS); plausible real 70-230M | PESSIMISTIC in ADV by ~2-6x (if wash discount is large); note shrinking trend (median 16M -> now 6.7M USD) and that USD volume matters more than KAS. Range to test: 40M-230M. Large ADV helps only if depth tracks it - see k. |
| impact_coefficient 0.08 | 0.08 | calm average k 0.03-0.04, marginal k 0.04-0.08 up to 5% ADV; much worse beyond 9% ADV | PLAUSIBLE for calm marginal impact; OPTIMISTIC for stress if depth falls 50-90% (my arithmetic: slippage ~ 1/depth => k 0.08-0.4; no stressed measurement). Test 0.04 / 0.08 / 0.16 / 0.30. Also the model applies sqrt only to participation and has no convex blow-up past ~10% ADV; with its own ADV 40M, a 40M dump = k*1 = 8%, while the live book shows -32% for 37M KAS. So the functional form is OPTIMISTIC for large dumps in absolute size. |
| daily_liquidation_capacity 5%/day | 5% debt/day | Market side: debt of 100M KAS at ICR 200% ~1.5M USD; 5%/day = 74k USD = 2.5M KAS = 1.1% of ADV, 0.3% slippage, ~15-35% of the <=1% book -> market depth is NOT binding at 5%. 50%/day = 25M KAS exceeds the whole visible 5% book. | Market-depth-wise PLAUSIBLE/not binding up to ~10-20%/day; the real constraint is liquidator capital/competition, which this data cannot measure (UNVERIFIED). Range: 1-20%/day. |
| ~100M KAS in system | 100M KAS (2.95M USD, 0.36% supply) | = 44% of ADV; 6x the combined 5% visible book (16M KAS) | Small vs market cap but LARGE vs book: full-system liquidation in a few days is impossible without >10% impact; scale matters, model should scale with system size / ADV. |
| jump 4%/day of -25% | | 1 day < -20% in 1285 KAS days (0.08%); worst day -24.9%; analogs worst -15..-26% | jump size right, frequency ~50x the empirical (per-day) rate: PESSIMISTIC as a rate, used as a proxy for gaps (intraday not measured). |
| total drawdown -85% in 60d | | worst 60d: KAS -62%, ERG -65%, DOGE -63%, ZEC -62%; -85% over 12-25 months seen (KAS -88%) | severe-tail stress beyond observed 60d; plausible only as multi-quarter bleed compressed. |

## 8. Limits
- One calm snapshot cannot measure stressed depth, hidden/iceberg orders, market-maker withdrawal, cross-venue arbitrage latency, or DEX/bridge liquidity. Displayed depth is cancelable; in a crash it typically thins (SECONDARY, not measured here).
- CoinGecko free API limits history to 365 days; days=max failed (error 10012). KuCoin is one venue's price (USDT pair; USDT depeg risk ignored).
- Wash-trade share is inferred, not measured. No hashrate/energy history; no electricity data.
- k from displayed book vs same-day ADV mixes a book snapshot with a 24h flow; indicative only.

## 9. Data-collection plan (no persistent process; each run is a manual or owner-launched one-shot)
- What: (a) order-book snapshots (levels to >=5% depth) for Kraken, KuCoin, Bybit, Gate, MEXC, Bitget + 24h ticker volume; (b) daily KAS price/volume from CoinGecko 365d and KuCoin candles; (c) Kaspa REST hashrate, difficulty, supply, fee estimate; (d) same snapshots for 2-3 analog coins (ETC, ERG, ZEC) to calibrate k; (e) optional: ETH/BTC-style stress dates: record depth on days when |daily move| > 8%.
- How often: one-shot snapshot per day for 2 weeks at 3 fixed UTC times (00, 08, 16) = ~42 runs, started by the owner by hand or by a launchctl job ONLY with a separate owner go (no job created here); plus an extra manual run whenever KAS moves >8% intraday, to capture depth under stress - the only way to measure the k stressed/calm ratio. After the 2 weeks: weekly.
- Where: new folder under the repo's data area chosen by the owner, e.g. data/market/YYYY-MM-DD/<venue>_<utc>.json with the raw JSON + a CSV index (timestamp, venue, mid, depth1/2/5%, 24h vol, k at 0.1/1/5% ADV). Raw files read-only after write. Script: the existing ob_analyze.py logic would become a repo script only after owner validation (rule: no code change without go).
- Then: fit k distribution (calm and stress), feed Monte-Carlo ranges (k 0.04-0.30, ADV 40-230M KAS, capacity 1-20%), and add a convex term beyond ~10% ADV.

## Sources
api.coingecko.com/api/v3/coins/kaspa (+market_chart, tickers); api.kucoin.com (candles, orderbook, stats); api.kraken.com Depth/Ticker; api.gateio.ws; api.mexc.com; api.bybit.com; api.bitget.com; api.kaspa.org/info/{hashrate,coinsupply,blockdag,halving,blockreward,fee-estimate}; nber.org/papers/w30783 (SECONDARY, web search result).
