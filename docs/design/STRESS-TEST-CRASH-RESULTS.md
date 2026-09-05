# Crash Stress Test — Method and Results

**Script:** `tests/backtesting/stress_test_crash.py` (standard library only, fixed seed)
**Date:** September 3, 2026

This is the most consequential analysis produced for ENRK so far. It models the
whole protocol under a severe KAS drawdown — not just the peg formula — and it
changed the design.

---

## What it models

A population of 1000 vaults with log-normal sizes and log-normal opening ICRs;
peg computation from the four indices; ICR collapse; Dutch-auction liquidation
with realistic bidder scarcity; the ENRK/kFIAT seniority waterfall; the reflexive
loop where liquidated collateral is dumped and pushes KAS lower; gap risk
(Black-Thursday-class jumps); and a liquidator capital constraint.

**The model was wrong three times before it was right.** Each fix reversed a
conclusion:

1. A failed auction destroyed the collateral — wrong. A failed auction destroys
   nothing; the vault stays open and is re-auctioned. Fixed.
2. Linear market impact turned a −50% exogenous crash into −85% actual, which
   flattened every comparison. Replaced with the square-root impact law.
3. Liquidator capital was unlimited, so the system always cleared. Added a daily
   liquidation capacity constraint — which is what actually broke on Black Thursday.

Before those fixes the model reported "everything is fine" for entirely wrong
reasons.

---

## Headline results (200 Monte Carlo paths per drawdown, opening ICR 200%)

```
                    median      p95     worst
KAS -85%
  ENRK loss              0%       0%       0%
  kFIAT loss             5%      12%      15%
  latent hole           16%      45%      63%

KAS -95%
  ENRK loss              0%       0%       0%
  kFIAT loss             3%       7%       9%
  latent hole           30%      57%      72%
```

## The central finding: the protocol freezes, it does not explode

kFIAT realised losses **fall** as the crash deepens — 5% at −85%, 3% at −95%.
That is not resilience. Losses fall because **liquidations stop happening**: at
−95%, 591 of 1000 vaults stay open and underwater, never liquidated. Liquidators
run out of capital, the auction floor is 15% while the market demands 21%, and
nothing clears.

The debt does not disappear. It becomes **latent** — 30% of total debt at the
median, 57% at p95, uncovered, with the tokens still circulating. Zero "realised"
loss because nothing is realised at all.

For an immutable protocol this is the critical property: **there is nobody to
unfreeze it.** No DAO to raise the MCR in an emergency, no admin key to inject
capital. The frozen state persists until the market recovers on its own, or until
someone forks.

## The kFIAT buffer covers the median and breaks in the tail

kFIAT is 30% of debt. At −85% the hole is 16% at the median — comfortably
covered. At p95 it is 45% — the buffer is exceeded, and ENRK is structurally
exposed to roughly 21% loss that simply has not crystallised.

## Minimum opening ICR for zero ENRK loss

```
KAS -70%  ->  233%
KAS -85%  ->  245%
KAS -95%  ->  237%
```

Raising the minimum from 200% to **250%** removes the exposure across the whole
tested range — without any custodian, reserve or trusted third party.

## Where the Dutch auction stops clearing

The auction floor is 85% of market, a 15% discount. Modelled liquidator demand is
`4% + 18% × drawdown`. The crossover:

```
required > 15%  when  drawdown > 61%
```

Past a 61% drawdown, no auction fills at any point in its descent.

## Secondary findings

**Peg formula.** Alt 3 (pure Kaspa) leaves a 10% latent hole at −85% where the
deployed Alt 3.5 leaves 17%. The uncorrelated energy hedge costs roughly 7 points
of solvency: a peg that holds firm while collateral collapses maximises the fall
in ICR. This is the MakerDAO Black Thursday dynamic. Not a reason to change 3.5 —
peg purchasing-power stability is worth it — but it must be documented before the
parameter is frozen.

**Energy crisis scenario** (2022 pattern, energy +60% during the crash): latent
hole 17% → 19%. Real but far milder than predicted verbally beforehand.

## What to distrust

Two parameters dominate everything: `impact_coefficient` (0.08, square-root law)
and `daily_liquidation_capacity` (5% of opening debt per day). These are
**assumptions, not measurements**. Vary them and re-run before trusting any
number here.

## What this changed in the design

- The Stability Pool was found to be non-functional: it burns ENRK it already
  holds rather than bidding, and its ammunition is denominated in the asset it
  defends. Losing it in the L1 design therefore costs less than it appears.
- Recovery Mode (Liquity-style, automatic and governance-free) became the
  identified fix for the freeze — and its unavailability on Kaspa L1 is the most
  significant loss in that path.
- The 250% ICR result is what made an uncorrelated gold reserve unnecessary:
  the same protection, with no trusted party.
