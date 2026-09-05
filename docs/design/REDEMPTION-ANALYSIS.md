# Redemption — Equilibrium Mechanism #1

**Date:** September 3, 2026
**Script:** `tests/backtesting/stress_test_crash.py` (`enable_redemption`)

---

## The gap that prompted this

Redemption — burning ENRK to receive KAS at peg — is equilibrium mechanism #1 and
was described as the protocol's strongest peg defence.

A search of the codebase found it exists only as four error variants, one fee
parameter (`redemption_fee_bps: 100`) and some comments in module headers.
**No implementation, no logic, no test, no model.**

Of the five equilibrium mechanisms, three live in code:

| | State |
|---|---|
| 1. Redemption / convertibility | **Never built** |
| 2. Miner arbitrage | External, not code |
| 3. Stability Pool buyback | **Built but defective** — it burns rather than bids |
| 4. Dutch auction | Built, tested, fixed (floor 75%) |
| 5. PoW difficulty adjustment | External, not code |

One works, one is broken, one was never written.

This mattered urgently because the crash stress test's central finding — the
protocol freezes because liquidators run out of capital — was produced by a model
that **omitted the one mechanism needing no liquidator capital at all**. A redeemer
uses ENRK they already hold. Redemption should therefore work precisely when
auctions fail.

## The structural limit, before any simulation

With `a` the collateral value, `b` the debt value and `r` the amount redeemed at
face value:

```
new ratio = (a − r) / (b − r)
```

- healthy vault (`a > b`) → the ratio **improves**
- underwater vault (`a < b`) → the ratio **degrades**
- if `a < r`, the collateral to honour face value simply does not exist

**Redemption at face value only functions while a vault is over-collateralised.**
This is modelled as `redemption_min_icr = 1.00`.

## Result 1 — redemption reduces the freeze but hits its wall

```
KAS -85%                        latent med   latent p95   redeemed   blocked
floor 85, no redemption             9%          46%          —          —
floor 85, WITH redemption           4%          32%         20%         4%

KAS -95%
floor 85, no redemption            30%          60%          —          —
floor 85, WITH redemption          17%          44%         24%        26%
```

It removes roughly a third of the freeze. It does not remove the freeze.

At −95%, **26% of redemption demand finds no eligible vault** — the structural
limit above, reached exactly when the mechanism is most needed.

**The freeze finding stands. It was not an artefact of omitting redemption.**

## Result 2 — but the cost of the fix was overstated by half

```
KAS -85%                        ENRK med   ENRK p95   kFIAT
floor 75, no redemption           1.0%      11.2%      14%
floor 75, WITH redemption         0.0%       5.0%       2%

KAS -95%
floor 75, no redemption           5.1%      19.8%      30%
floor 75, WITH redemption         0.5%      10.7%      16%
```

The "11.2% ENRK p95 is the price of a 75% floor" figure reported earlier was
pessimistic: with mechanism #1 present it is **5.0%**. kFIAT falls from 14% to 2%.

**Redemption roughly halves the losses.**

## Why the two mechanisms are complementary

They act at different moments.

**Redemption is preventive.** It drains the weakest vaults early, while they are
still above 100% ICR, stopping them from *becoming* bad debt.

**The deeper auction floor is curative.** It clears whatever redemption could not
reach.

This explains the collapse in kFIAT losses: redemption prevents vaults from
reaching the state where liquidation produces a shortfall at all, so the junior
tranche is protected indirectly, by prevention rather than by absorption.

## Design decisions taken to model it — these need owner confirmation

**Which vaults are redeemed against?** Liquity's choice was used: **lowest ICR
first**. It pays down the worst debt and improves system health. But those owners
are dispossessed of collateral at par, involuntarily, having done nothing wrong
beyond being the least collateralised. This is harsh and deliberate.

**Where redemption stops.** `redemption_min_icr = 1.00`. Below that, face value is
fiction. This threshold is a frozen parameter and determines where the mechanism
ceases to function.

**Seniority interaction, to be stated explicitly in documentation.** Only ENRK is
redeemable (`CannotRedeemKFIAT`). In a crisis ENRK holders can exit at par while
kFIAT holders cannot. The figures show kFIAT benefits indirectly — but in a deeper
scenario ENRK drains the collateral and kFIAT faces the remainder. That is
seniority working as designed, and it should be documented as a deliberate
property rather than discovered by a user.

## Modelling assumptions to distrust

- Redemption demand is modelled as `base + sensitivity × drawdown` of outstanding
  ENRK per day, because the model has no ENRK market price. Real demand is driven
  by the ENRK/peg discount, which is not simulated.
- Redeemed collateral is assumed **not** dumped on the market (the redeemer wanted
  KAS). If redeemers are arbitrageurs who immediately sell, add price impact and
  results worsen.

## Consequence for the parameter set

| Parameter | Value | Reason |
|---|---|---|
| Auction floor | **75%** | Removes the freeze; real cost half of the earlier estimate |
| Redemption | **Must be implemented** | Halves losses; currently does not exist |
| ICR minimum | **200%** unchanged | 250% buys nothing and costs 25% capital efficiency |
| MCR | **150%** unchanged | Raising it buys almost no protection |
