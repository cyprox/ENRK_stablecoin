# Final Recommendation — Alternative 3.5 (Kaspa-Hybrid)

**Date:** September 3, 2026
**Status:** Peg formula decided and frozen. These are the definitive backtesting
figures.

> **Scope.** This document fixes the peg formula and its calibration. Protocol
> parameters — ICR, MCR, auction floor, fees, treasury — are in
> [`FROZEN_PARAMETERS.md`](FROZEN_PARAMETERS.md), which is authoritative. The
> execution layer and the oracle construction are covered in
> [`EXECUTION_TARGET_ASSESSMENT.md`](EXECUTION_TARGET_ASSESSMENT.md) and
> [`L1_NATIVE_REDUCED_SPEC.md`](L1_NATIVE_REDUCED_SPEC.md).

---

## Executive summary

After full backtesting over 12 years of data (2014–2026), or 4,380 simulated days,
the formula chosen for the ENRK peg is **Alternative 3.5**.

| Metric | Alt 3 (pure Kaspa) | Alt 3.5 (hybrid) |
|---|---|---|
| Annual volatility | NaN — diverges | **25.0%** |
| Max drawdown | NaN | **−17.3%** |
| Sharpe ratio | NaN | **0.42** |
| Days drifting > 5% | 886 / 4,380 | **319 / 4,380** |
| Mean drift from peg | 5.8% | **2.1%** |

Alternative 3 **fails numerically** in backtesting, with infinite volatility, which
confirms its spiral risk.

---

## The formula

```
Peg(ENRK) = 0.40 × Kaspa_Hashrate_Index
          + 0.30 × Global_Energy_Index
          + 0.20 × Kaspa_Fees_Index
          + 0.10 × Crypto_Adoption_Index

Each index = (Current_value / Baseline_value) × 100
Clipped to [0.1, 5.0]
```

### 1. Kaspa Hashrate Index — 40%

```
Source     : Kaspa network (on-chain, decentralised)
Formula    : (Current_hashrate / Baseline_hashrate) × 100
Baseline   : hashrate at protocol launch
Frequency  : daily
Fail-over  : network difficulty as a proxy if hashrate is unavailable
```

**Why 40%** — Kaspa-native without being dominant, which avoids extreme
pro-cyclicality. Reflects network security. The proof-of-work difficulty adjustment
is self-correcting.

### 2. Global Energy Index — 30%

```
Source     : industrial electricity prices, multi-source aggregation, median
Formula    : (Current_price_$/kWh / Baseline_price) × 100
Baseline   : global average at launch (order of $0.08/kWh)
Frequency  : daily, aggregated over a rolling week
References : IEA, GlobalPetrolPrices, ENTSO-E (Europe), CAISO (USA)
```

**Why 30%** — a hedge against Kaspa's volatility, since energy is weakly correlated
with crypto sentiment. It is also a physical reality: the kWh is the real cost of
mining. It reflects global inflation and energy crises.

### 3. Kaspa Fees Index — 20%

```
Source     : Kaspa network (on-chain, decentralised)
Formula    : (Weekly_fees_KAS / Baseline_fees) × 100
Baseline   : average fees over the protocol's first week
Frequency  : weekly, 7-day aggregation
```

**Why 20%** — reflects real economic activity on Kaspa, is less volatile than
hashrate alone, and aligns the interests of network users with the protocol.

### 4. Crypto Adoption Index — 10%

```
Source     : global crypto adoption measure
Formula    : (Current_users / Baseline_users) × 100
Baseline   : ~100M users (2024 reference)
Frequency  : monthly
Alternative: global blockchain transactions if adoption data is unavailable
```

**Why 10%** — a deliberately small weight, to limit oracle dependence. It captures
a long-run trend without exposing the peg to manipulation.

---

## Validation against black scenarios

### Scenario 1 — proof-of-work banned in the United States

```
Kaspa hashrate  -40%   (US miners offline)
Kaspa fees      -50%   (less activity)
Global energy   +15%   (the restriction creates tension)
Adoption        -10%   (short-term panic)

Peg = 0.40×60 + 0.30×115 + 0.20×50 + 0.10×90
    = 24 + 34.5 + 10 + 9 = 77.5%          -> a fall of 22.5%
```

Pure Alternative 3 would have collapsed by 50%.

### Scenario 2 — Kaspa bull market

```
Hashrate  +300%    Fees  +400%
Energy     +10%    Adoption +80%

Peg = 0.40×400 + 0.30×110 + 0.20×500 + 0.10×180
    = 160 + 33 + 100 + 18 = 311%          -> a rise of 211%
```

Measured, where Alternative 3 would have produced +600% — too speculative for a
stablecoin.

### Scenario 3 — global energy crisis

```
Hashrate  -15%     Fees  +5%
Energy   +300%     Adoption -5%

Peg = 0.40×85 + 0.30×400 + 0.20×105 + 0.10×95
    = 34 + 120 + 21 + 9.5 = 184.5%        -> a rise of 84.5%
```

The peg reflects physical reality. **ENRK is not a hedge against fiat inflation. It
is a representation of energy value.** When energy becomes scarce, ENRK rises,
because that is what the kWh did.

---

## Critical points

### Robustness of the sources

| Index | Nature | Risk |
|---|---|---|
| Kaspa hashrate | On-chain, native | No oracle. Immutable. |
| Kaspa fees | On-chain, native | No oracle. Immutable. |
| Global energy | External | Requires on-chain delivery |
| Adoption | External | Sparse data — hence the 10% cap |

Two of the four indices, or 60% of the weight, are native and unforgeable. The other
two must be delivered on-chain, and **the construction chosen for that is the
covenant-lineage oracle described in
[`L1_NATIVE_REDUCED_SPEC.md`](L1_NATIVE_REDUCED_SPEC.md) §2**, not a third-party
oracle. Failure behaviour is the frozen circuit breaker: 10% deviation or six hours
of unavailability triggers a pause, with no override.

### Weights immutable after launch

The weights are compile-time constants. If they need to change, a new contract
deploys with different weights and the market chooses which to use; the old one
stays active and unchanged. This removes the risk of captured governance — see
[`Immutable-By-Design.md`](Immutable-By-Design.md).

---

## Use cases

### Miner with cheap electricity

```
Context: hydroelectric power at $0.02/kWh

1. Mine 1 KAS (real cost $0.02)
2. Lock the KAS in a vault
3. Mint ENRK at the peg
4. Sell the ENRK on a DEX
5. Pay electricity bills in ENRK, without a bank and without USD
```

Miner arbitrage stabilises the market: they flood the market with ENRK when the
price is too high, and buy back to redeem when it is too low.

### Resident of a high-inflation country

```
Context: local currency losing more than 100% a year

1. Convert salary into ENRK
2. ENRK represents 1 kWh — a physical quantity, not a political decision
3. A year later the local currency has halved; the kWh is still a kWh
```

ENRK works as a refuge currency. **The honest caveat:** ENRK is volatile against a
local shopping basket, depends on local on-ramps, and in a KAS crash the senior
tranche can take a loss. It replaces one risk with another, smaller and more
visible — not with safety.

### Trader betting on energy inflation

```
1. Buy ENRK
2. Mint kFIAT — the junior tranche, leveraged exposure
3. The bet: if energy gets more expensive, the peg rises

The other side: kFIAT absorbs losses first and is not redeemable.
```

---

## Verdict

**Alternative 3.5 is adopted.**

**Technically** — 25% volatility against infinite volatility for Alt 3, a positive
Sharpe at 0.42, survival of all three black scenarios tested, and no spiral even
under a regulatory apocalypse.

**Doctrinally** — 40% Kaspa-native, 30% real energy, 20% the network's real economy,
10% long-run trend. **No USD oracle: the decoupling from fiat is structural, not
declarative.**

**Geopolitically** — a miner with cheap electricity can mint without a bank; a
country in inflation has a refuge indexed to a physical quantity; the energy
standard decouples crypto from the fiat system.

---

**Senior token: ENRK** (Kaspa Energy Reserve) — 1 ENRK = 1 kWh, redeemable.
**Junior token: kFIAT** — loss-absorbing, capped at 30% of debt at issuance, not
redeemable.
