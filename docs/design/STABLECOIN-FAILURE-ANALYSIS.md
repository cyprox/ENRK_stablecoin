# Anatomy of Stablecoin Collapses

*Applied economic analysis of failure mechanisms in DeFi protocols*

**Date:** September 3, 2026

> **Scope.** This document analyses why existing stablecoins failed and draws the
> design constraints that follow. It proposes no formula: the chosen formula is in
> [`PEG-FORMULA-RECOMMENDATION.md`](PEG-FORMULA-RECOMMENDATION.md), and the protocol
> parameters are in [`FROZEN_PARAMETERS.md`](FROZEN_PARAMETERS.md).

---

## I. Terra / LUNA — the collapse of the algorithmic dream (May 2022)

### The fatal structure: two circular tokens

Terra rested on an **illusion of circular value**:

- **UST** — an algorithmic stablecoin, supposedly stable at $1
- **LUNA** — a counterweight token whose value rested entirely on its capacity to be
  converted into UST

The assumed arbitrage mechanism:

```
UST < $1  ->  redeem 1 UST for $1 of freshly minted LUNA,
              sell the LUNA on the market
UST > $1  ->  create UST with LUNA to capture the premium
```

**The existential flaw:** LUNA's value was nothing but its optional capacity to
convert into UST. When that confidence wavered, **there was nothing underneath.**

### The three phases of the collapse

**Phase 1 — the liquidity attack (May 5–8).** A massive $285M withdrawal of UST from
Curve. UST falls to $0.98. The critical signal: if liquidity can vanish that fast,
in what sense is UST stable?

**Phase 2 — the redemption run (May 9–10).** Massive UST → LUNA conversion demand.
Redemption capacity was capped. LUNA collapses 48% in one day. Nobody wants to buy a
token in free fall.

**Phase 3 — the Minsky moment (May 11–14).** LUNA's market capitalisation falls
below UST's. **The mechanism inverts:** if LUNA is worth nothing, converting UST
into LUNA helps nobody. The proof-of-stake network collapses for want of validator
incentives. Terra halts the chain, which accelerates the disaster.

### The deeper roots

**1. No intrinsic value.** UST had no real backing. Its stability rested on
speculator confidence, the circular LUNA ↔ UST exchange, and Anchor's yields.

**2. Anchor Protocol — the yield mirage.** 20% annual, unsustainable, attracting 75%
of circulating UST. UST stopped being a currency and became a yield speculation
instrument. When the unsustainability became obvious, 75% of the liquidity looked
for the exit at once.

**3. Prohibitive fees at scale.** Fees made arbitrage impossible at size — the bots
meant to stabilise the system could not operate.

**4. Excessive dependence on Curve.** More than 80% of UST liquidity sat in a single
pool. A single point of failure: when the depeg began, LPs fled immediately.

---

## II. Inverse Finance / DOLA — the hybrid model

DOLA works differently from Terra: issued against deposited crypto collateral,
over-collateralised at around 150%, with no circular two-token loop. sDOLA yields
come from real lending activity, not from promises.

**Residual vulnerabilities:** dependence on volatile crypto collateral, with possible
liquidation cascades; protocol solvency risk in an exploit; and a structural
scalability limit, since every new DOLA requires new collateral.

---

## III. Curve — the limits of liquidity

Curve revolutionised stablecoin exchange with StableSwap: minimal slippage, deep
liquidity at low cost. **But Curve is only an exchange mechanism, not a mechanism
for creating stability.**

Depegs it has lived through: UST in May 2022 (Curve was the terrain of the failure),
USDC at $0.88 in March 2023, OUSD in 2023.

**The lesson:** even the best liquidity cannot save a fundamentally unstable
stablecoin.

**Impermanent loss makes it worse.** When two stablecoins depeg, LPs take losses and
therefore withdraw, which reduces liquidity **exactly when it is most needed.**

---

## IV. Central lessons

### A stablecoin is a function, not a commodity

A stablecoin must not be a **speculative commodity**. It is a **means of
circulation**. The stablecoins that fail forget this: UST was turned into a yield
asset, and lost its monetary function before it lost its peg.

**Design consequence:** the stablecoin must be backed by something **independent and
stable over time**, not by speculative demand for itself.

### The crypto collateral problem

Every crypto-over-collateralised stablecoin suffers the same defect: the collateral
is itself volatile, and a simultaneous crash bankrupts the protocol. This has
happened four or five times since 2021.

**What is needed:** a stable, decentralised index that does not depend on a central
authority and is not fiat.

**That constraint is what produces ENRK.** KAS remains volatile collateral, but it
has a production cost anchored in proof-of-work electricity consumption. If the
price falls below that cost, miners power down, difficulty adjusts, and cost
realigns. **The collateral and the unit of account are causally linked through the
consensus mechanism.** That link does not exist on a proof-of-stake chain.

---

## V. The three existing architectures

### 1. Off-chain collateralised — USDT, USDC, EURC

Backed by real assets held off-chain.

*For:* stable, liquid, simple.
*Against:* centralised, dependent on an authority, seizable.

**Not viable** for a decentralised stablecoin.

### 2. Over-collateralised — DAI, DOLA

The user locks $150 of crypto to create $100 of stablecoin.

*For:* decentralised, no trusted third party.
*Against:* capital-inefficient, liquidation cascades.

**Partially viable** — this is the architecture chosen, with its limits accepted.

### 3. Algorithmic / synthetic — Terra, Ethena

A combination of assets and derivative hedging.

*For:* potentially more capital-efficient.
*Against:* extreme complexity, derivative manipulation risk.

**Too risky** after the failures of Terra and Iron.

---

## What these failures impose on the design

| Observed failure | The constraint that follows | Where it is handled |
|---|---|---|
| LUNA with no value of its own | Collateral must have value exogenous to the protocol | KAS, PoW production cost |
| Anchor: unsustainable yield | The protocol promises no yield | The protocol pays nothing |
| Terra's capped redemption | Convertibility must be permanent, with no discretionary cap | [`REDEMPTION-ANALYSIS.md`](REDEMPTION-ANALYSIS.md) |
| Liquidity concentrated on Curve | Do not depend on a single pool | Redemption at par, independent of DEXs |
| Captured governance | No governance | [`Immutable-By-Design.md`](Immutable-By-Design.md) |
| Volatile collateral | Over-collateralisation, tranching, stress-tested liquidation | [`FROZEN_PARAMETERS.md`](FROZEN_PARAMETERS.md), [`STRESS-TEST-CRASH-RESULTS.md`](STRESS-TEST-CRASH-RESULTS.md) |

The common thread in these failures is that a protocol dies of the very mechanism it
believed was its protection: arbitrage at Terra, liquidity at Curve, governance at
MakerDAO. That is why the analysis in this repository is run against its own
conclusions — see [`STRESS-TEST-CRASH-RESULTS.md`](STRESS-TEST-CRASH-RESULTS.md),
where the model was wrong three times before it was right.
