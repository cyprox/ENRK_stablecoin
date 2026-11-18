# Source sheets for a KAS/USD oracle (three-oracle median)

**Date:** 2026-11-17. **Status:** study sheet for the owner, nothing decided, no value proposed as a rule. Written for the project owner who must decide who reads what.
**Basis:** `docs/design/studies-2026-11/reports/r4-market.md` (order books, 2026-11-10, calm snapshot, displayed depth only; raw data in `~/ENRK_market_data/`), a ticker snapshot taken today (`sources_snapshot_2026-11-17.txt`), the KSD review in this folder, `econ-v3-enrk-oracle.md`. Tags: **MEASURED** (data above), **SECOND-HAND**, **UNVERIFIED**, **ANALYSIS** (my reading).

## 1. Sheet per candidate source

| Source | Quote | 24h volume (KAS) 2026-11-17 | Bid depth within 1% / 2% / 5% (USD, 2026-11-10) | What it is good for | Weak points |
|---|---|---|---|---|---|
| **Kraken** | USD (fiat) | 19.96 M | 134k / 241k / 269k | Deepest book by far; regulated venue; its volume matched the aggregator's row (not inflated, r4); the only candidate not quoted in USDT | Single venue; availability and terms of its public API UNVERIFIED |
| **KuCoin** | USDT | 17.95 M | 19k / 29k / 39k | Large volume; also the source of the 1,285-day daily series used for the drawdown studies | Thin depth for its volume; USDT-quoted |
| **Bybit** | USDT | 19.13 M | 27k / 42k / 59k | Large volume and depth second after Kraken | USDT-quoted; access limits by country UNVERIFIED |
| **Gate** | USDT | 15.96 M | 7k / 22k / 42k | Large volume | Thin depth |
| **Bitget** | USDT | 7.12 M | 13k / 15k / 35k | Another independent venue | Smaller volume, thin depth |
| **MEXC** | USDT | no answer today | 4k / 14k / 27k | Another venue | Thinnest book; unreachable on the one attempt today (reason UNVERIFIED) |
| **CoinGecko** (aggregator) | USD | 9.15 M USD | n/a | Easy to read; already merges many venues | **Secondary**: its daily history had glitches (-45% then +94% on consecutive days, r4) that KuCoin candles did not show; about 58% of its volume comes from small venues exposed to wash trading (r4, estimate); depends on the same venues, so adds little independence |
| **Miners' vote (KSD style)** | n/a | n/a | n/a | No publisher key | **Not available**: KSD has no public code or testnet; votes are written by pool operators; see the KSD review |
| **On-chain Kaspa exchange** | n/a | n/a | n/a | Would be the cleanest source | **Not available**: no exchange with a price curve on the L1 today (`econ-v3`; the one example found is fixed-rate) |
| **Kaspa chain data** (hashrate, fees) | n/a | n/a | n/a | Useful for the **peg index**, not for a dollar price | Not a source for the collateral price |

Market context, MEASURED today: five venues answered with prices within 0.29% of each other (0.02714 to 0.02722); price is 8% lower than on 2026-11-10 (0.02951).

## 2. How independent are these sources? (ANALYSIS)
- **Quote currency.** Five of the six venues quote KAS in USDT; only Kraken quotes in USD. A USDT scare would move five sources together and the median of three USDT venues would not detect it. At least one source should be USD-quoted.
- **Common market.** All venues are tied together by arbitrage: a real KAS crash moves all of them. That is correct behaviour (the oracle should follow the real market), not a flaw.
- **What independence protects against.** A venue-specific glitch, outage, or a local manipulation. It does not protect against a common error such as a shared wrong data feed or an operator who copies the same data into three oracles.
- **Aggregators** read the same venues and add small ones: as a third "independent" source they are weaker than they look.

## 3. What would it cost to push a source? (ANALYSIS, order of magnitude only)
Displayed bid depth within 5% of the best bid, 2026-11-10: Kraken 269k USD, Bybit 59k, Gate 42k, KuCoin 39k, Bitget 35k, MEXC 27k. A median of three needs **two** venues moved. Cheapest pair among the six: MEXC + Bitget, about 62k USD of displayed depth to push both about 5%. Among {Kraken, KuCoin, Bybit}: KuCoin + Bybit, about 98k. Among {Kraken, Bybit, Gate}: about 101k.
Cautions: (i) calm snapshot, depth can vanish in a crash; (ii) displayed liquidity only; (iii) depth beyond 5% was not captured, so a 25% push cannot be priced from this data; (iv) arbitrageurs refill a pushed venue quickly, so a short push costs less and lasts less; an oracle that averages over time (not studied here) raises the cost; (v) the attacker's gain depends on the system's total debt, which does not exist yet. The comparison between source sets stays valid even if the absolute figures do not.

## 4. Candidate arrangements (illustrations to read, not proposals)
Each publisher is a separate operator, key and server, reading its own source set and publishing its own median.
- **Arrangement 1 (deep venues spread out):** Publisher A reads Kraken and Bybit; B reads KuCoin and Gate; C reads Bitget and one more source of its choice. Cheapest-pair cost is set by the thinnest pair read; C is the weak link.
- **Arrangement 2 (each reads the same top venues by different methods):** all three read Kraken, Bybit, KuCoin with different aggregation (spot, volume-weighted, time-averaged). More robust to a single venue, but less independent: one venue-wide outage hits all three.
- **Arrangement 3 (mix of regions and quotes):** one publisher on USD only (Kraken), one on the USDT venues, one on an aggregator plus on-chain data when it exists. Best fit for the "independence" criterion; the aggregator part is the weakest.
My reading: the choice depends on criteria the owner sets (see section 6), not on the data alone.

## 5. What this sheet cannot tell
- Rate limits, terms of use, geographical blocking, uptime history of each API: UNVERIFIED.
- Depth in a stressed market, depth beyond 5%, hidden orders: not measured (r4 §8).
- Whether venue volumes are inflated, except Kraken (r4 estimate only).
- Who would run the three publishers, and their incentives and costs: not studied.
- Cost of reading three prices in each vault on the L1: not measured.
- MEXC was unreachable once; one attempt proves nothing.
- Quotes beyond calm times: the 2026-11-10 depth is a week old and the price has moved 8% since. Refreshing it (collection script already in the repository, manual one-shot) is cheap and would remove the age caveat; I did not run it because the collection routine is the owner's.

## 6. Decisions asked of the owner
1. Which independence criteria must the three publishers meet (different quote currency, different venue sets, different operators, different jurisdictions)?
2. Must at least one source be USD-quoted (Kraken is the only candidate today)?
3. Is an aggregator acceptable as one of the three, given it adds little independence?
4. Should depth be refreshed (one-shot collection, ideally on a day KAS moves more than 8%) before choosing venues?
5. Who operates the publishers? This sheet gives no answer and the median protects only if they are truly independent.
