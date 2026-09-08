# Backtesting and Resilience — Selecting the Peg Formula

**Date:** September 3, 2026
**Status:** Selection closed. The chosen formula is **Alternative 3.5**.

> **How to read this.** This is the exploratory analysis that led to the choice of
> formula. The performance figures given here in Phase 4 and Phase 5 are
> intermediate estimates. **The definitive figures are in
> [`PEG-FORMULA-RECOMMENDATION.md`](PEG-FORMULA-RECOMMENDATION.md)** — volatility
> 25.0%, max drawdown −17.3%, Sharpe 0.42 — obtained from the full 4,380-day
> simulation. Where the two disagree, that document is right.
>
> Protocol parameters (ICR, MCR, auction floor, fees) are not here. They are in
> [`FROZEN_PARAMETERS.md`](FROZEN_PARAMETERS.md).

---

## Phase 0 — the three alternatives

The peg has to be computed from an index-based formula.

### Alternative 1 — "natural resources" basket

```
Peg = 0.50 × Energy_Index + 0.30 × Metals_Index + 0.20 × Agriculture_Index
```

**For:** real intrinsic value, uncorrelated with crypto, globally understood.

**Against:** requires three external oracles, depends on world market data, and is
open to manipulation in the price of gold or oil.

### Alternative 2 — "global infrastructure" basket

```
Peg = 0.40 × DataCenter + 0.30 × Telecom + 0.20 × RenewableEnergy + 0.10 × Logistics
```

**For:** long-term growth, less volatile than commodities.

**Against:** very hard to value in real time. There is no single market for "data
centres", so it requires complex valuation models.

### Alternative 3 — "Kaspa-based" basket (autopoietic)

```
Peg = 0.50 × Hashrate_Index + 0.30 × Fees_Index + 0.20 × Transactions_Index
```

**For:** fully decentralised, zero external oracles, native to Kaspa, complete
alignment of interests.

**Against:** pro-cyclical. If Kaspa crashes, hashrate, fees and transactions fall
together, and the peg falls with them.

---

## Phase 1 — method

**Data for Alt 1 and 2:** public sources — IEA, GlobalPetrolPrices, Statista, LME,
USGS, FAO, CBOT. Industrial electricity, metals and agricultural prices, 2010–2026.

**Data for Alt 3:** Bitcoin history as a proof-of-work proxy, since Kaspa has only
existed since 2021 — hashrate, fees and transactions, 2012–2026.

**Model:** for each day from 2014 to 2026, compute the composite index, simulate a
market price at ±10% normal volatility, and measure distance to peg, annualised
volatility, max drawdown in crisis, and the number of days the peg drifts more than
5%.

---

## Phase 2 — results

### 2.1 Alternative 1 — natural resources

| Metric | Value |
|---|---|
| Annualised volatility | ~12–15% |
| Max drawdown (COVID 2020) | −35% |
| Days drifting > 5% | ~45 / year |
| Post-crash recovery | 3–6 months |
| BTC correlation | −0.15 |

**Crises tested.** The 2014–2016 oil crisis (−60% oil): the peg would have fallen
roughly 25% through its energy component, but metals and agriculture rose in
counterbalance, leaving a final peg of −10%. COVID-19: −35% over two months, then
recovery to −5%. The 2022 European energy crisis (+300% electricity): +80% over six
months, which correctly reflects reality.

**Verdict:** very stable and faithful to the real economy, but **three external
oracles** and open to manipulation.

### 2.2 Alternative 2 — global infrastructure

No direct historical data. Modelled through proxies: cloud-giant CAPEX (~20%/year),
telecom revenue (~3–5%/year), renewable investment (~15%/year), world trade volume
(~4–6%/year).

| Metric | Value |
|---|---|
| Annualised volatility | ~8–10% |
| Max drawdown (2008 proxy) | −15% |
| Max drawdown (COVID 2020) | −5% |
| Days drifting > 5% | ~10 / year |
| Average annual growth | +6% |
| BTC correlation | −0.05 |

**Verdict:** the most stable of the three, with growth built in — but the data are
indirect, real-time valuation is hard, and **there is no link to Kaspa at all**.

### 2.3 Alternative 3 — pure Kaspa

| Metric | Value |
|---|---|
| Annualised volatility | **45–65%** |
| Max drawdown (2018 bear) | **−78%** |
| Max drawdown (2022 bear) | −65% |
| Days drifting > 5% | ~150–180 / year |
| Correlation with BTC price | **+0.92** |

**Crises tested.** 2018 bear (−80% BTC): hashrate −35%, fees −60%, transactions
−30%, giving **peg −50%** over six months and 18 months to recover. 2022
apocalypse: peg −45% over three months.

### The pro-cyclical problem, demonstrated

```
T0        Kaspa healthy, peg = 100
T+1 wk    US regulation against PoW -> miners offline -> hashrate -40%
T+2 wk    crypto sentiment collapses -> fees -50%, transactions -60%
          the peg automatically computes -50%
T+3 wk    vault collateral shrinks -> liquidations
          liquidations dump KAS in panic -> KAS price falls
          -> more liquidations -> spiral
```

**Even with a perfect protocol, the peg formula itself can be pro-cyclical.** That
is the finding that forced the hybrid formula.

---

## Phase 3 — comparison

| Criterion | Alt 1 | Alt 2 | Alt 3 |
|---|---|---|---|
| Volatility | 12–15% | 8–10% | **45–65%** |
| Max drawdown | −35% | −15% | **−78%** |
| Oracles required | 3 | 2–3 | **0** |
| Kaspa alignment | Low | Moderate | **Maximal** |
| Real underlying value | Yes | Yes | **No** |
| Pro-cyclical risk | Low | Very low | **Extreme** |

---

## Phase 4 — why Alt 3 fails, and the fix

Alternative 3 assumes that *Kaspa network health equals stable value*. That is
false. A network can be secure and fast while nobody uses it, and hashrate tracks
the price of electricity as much as it tracks utility. Bitcoin went from 50 EH/s in
2021 to 120 EH/s in 2024 without becoming twice as useful.

### The solution — Alternative 3.5 (hybrid)

```
Peg = 0.40 × Kaspa_Hashrate_Index
    + 0.30 × Global_Energy_Index
    + 0.20 × Kaspa_Fees_Index
    + 0.10 × Crypto_Adoption_Index
```

What the energy component buys: it is weakly correlated with Kaspa, so it damps
exactly the movement that made Alt 3 dangerous. If Kaspa falls 50% while energy
rises 20%, the peg moves −24% instead of −50%.

**Alt 3.5 against Alt 3** *(intermediate estimates — see the note at the top)*:

| Metric | Alt 3.5 | Alt 3 |
|---|---|---|
| Annualised volatility | ~22% | ~55% |
| Max drawdown 2018 | −35% | −78% |
| Max drawdown 2022 | −28% | −65% |
| Bitcoin correlation | +0.60 | +0.92 |
| Death-spiral risk | Low | Extreme |

---

## Phase 5 — 30-year black scenarios

### Scenario 1 — Kaspa stagnates (probability ~40%)

Kaspa stays a niche chain, hashrate plateaus, fees remain tiny.

- **Under Alt 3:** the peg stagnates then degrades, miners lose the incentive to
  mint, the token becomes worthless.
- **Under Alt 3.5:** the energy component supports the peg. Even with Kaspa
  stagnant, global energy grows 2–3% a year. The protocol stays viable.

### Scenario 2 — proof-of-work banned (probability ~30%)

Governments ban PoW; only offshore jurisdictions continue.

- **Under Alt 3:** hashrate −80%, peg −75%, complete failure.
- **Under Alt 3.5:** Kaspa component −50%, energy component +30% through scarcity,
  overall peg about −11%. Badly damaged, but alive.

### Scenario 3 — Kaspa explodes (probability ~10%)

Kaspa becomes the second chain after Bitcoin.

- **Under Alt 3:** peg +580%, and a bubble is likely.
- **Under Alt 3.5:** peg +386%. More sustainable growth, less volatile.

**The hybrid formula dominates in all three scenarios.**

---

## Phase 6 — index calibration

**Kaspa Hashrate Index** — network hashrate, sourced from a Kaspa node, fully
decentralised. `(Current / Baseline) × 100`.

**Global Energy Index** — weighted average of industrial electricity prices in
$/kWh. Sources: IEA, national statistics, multi-source aggregation with a median.
One of the two indices requiring an oracle.

**Kaspa Fees Index** — weekly total of fees collected on Kaspa, sourced from a Kaspa
node, on-chain.

**Crypto Adoption Index** — global active crypto users. The second index requiring
an oracle, which is why its weight is deliberately held at 10%.

> **On oracles:** this document predates the covenant oracle construction. How the
> two non-native indices reach the chain is specified in
> [`L1_NATIVE_REDUCED_SPEC.md`](L1_NATIVE_REDUCED_SPEC.md) §2 and is not decided
> here.

---

## Conclusion

**Chosen formula: Alternative 3.5 (Kaspa-hybrid)**, with weights 40 / 30 / 20 / 10
and clipping to [0.1, 5.0].

Two of the four indices are native to Kaspa and need no oracle. The other two are
oracle-fed, for a combined weight of 40%.

The cost of this choice is documented in
[`FROZEN_PARAMETERS.md`](FROZEN_PARAMETERS.md) §1: a peg that holds firm while
collateral collapses maximises the fall in ICR. The energy hedge costs roughly seven
points of solvency. That is not a reason to change the formula. It is a reason not
to claim the hedge is free.

---

**Data sources**

- Bitcoin hashrate — blockchain.com/charts/hash-rate
- Electricity prices — IEA, *Electricity 2026*
- Bitcoin transaction fees — Statista
- Global energy prices — MacroTrends
- Hashrate Index — hashrateindex.com
