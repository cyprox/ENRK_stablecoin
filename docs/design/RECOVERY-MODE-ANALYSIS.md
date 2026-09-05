# Recovery Mode vs Static Parameterisation

**Script:** `tests/backtesting/recovery_mode_analysis.py`
**Date:** September 3, 2026
**Question:** Kaspa L1 cannot express Recovery Mode (it needs system-wide aggregate
state). What static parameterisation buys equivalent protection, and what does it
cost in calm markets?

---

## Result 1 — Recovery Mode buys nothing here

```
                                       latent hole p95 (crash -85%)
baseline   MCR 150 / floor 85                    46%
RECOVERY MODE  150 -> MCR 200                    46%    (active 47 of 60 days)
static     MCR 175 / floor 85                    45%
static     MCR 200 / floor 85                    44%
```

Recovery Mode triggered on 47 of 60 days and improved the p95 latent hole by
**zero points**.

**Why:** Recovery Mode makes more vaults *eligible* for liquidation. The failure
is not in eligibility, it is in *execution* — nothing clears because the auction
cannot descend far enough to meet what liquidators demand. Adding vaults to a
queue that is not moving changes nothing.

**The deeper reason:** in Liquity, Recovery Mode works because a Stability Pool
absorbs liquidations instantly without needing an auction bidder. The two are a
pair. ENRK's Stability Pool cannot buy — it only burns ENRK it already holds — so
Recovery Mode has nothing to execute against.

This corrects an earlier claim in `L1_NATIVE_REDUCED_SPEC` that losing Recovery
Mode was "a genuine loss" and the most significant cost of the L1 path. It is not.
Its absence costs essentially nothing.

## Result 2 — the auction floor is the real lever

```
                     latent p95   ENRK   kFIAT   calm-market cost
floor 85 (current)       46%       0%      5%       baseline
floor 75                  0%       1%     14%        +2.4%
floor 70                  0%       1%     14%        +2.4%
floor 60                  0%       1%     14%        +2.4%
```

Moving the floor from 85% to 75% **eliminates the freeze entirely**: the p95 latent
hole goes from 46% to zero, and all 1000 vaults liquidate.

This is the crossover the original stress test identified. Modelled liquidator
demand is `4% + 18% × drawdown`; at a 95% drawdown they require 21%. A floor of 85%
offers only 15%, so nothing clears. A floor of 75% offers 25%, so everything does.

**75, 70 and 60 give identical results.** A Dutch auction clears at the first
acceptable price, not at the floor. Once the floor is deep enough to cover maximum
demand, going deeper costs nothing and adds nothing. **The floor is a safety valve,
not a price.**

## Result 3 — the cost is modest, and cheaper than the alternative

In calm markets a 75% floor costs **+2.4%** in additional discount — less than
raising the MCR to 175% (+3.8%) or 200% (+5.2%), both of which buy almost no
protection.

Under stress the freeze converts into realised losses: ENRK 0% → 1%, kFIAT 5% → 14%.
Compare the totals:

```
frozen    :  0% + 5%  realised,  but 46% unbacked debt circulating
clearing  :  1% + 14% realised,  and  0% hole
```

**Clearing early recovers more than freezing.** A system that unfreezes takes less
total damage, because it avoids the reflexive spiral and sells while depth remains.

## Modelling correction made during this analysis

The original code filled every auction at the floor price. A Dutch auction clears
at the first price a bidder accepts. Fixed to `fill = max(1 − required_discount,
floor)`, which massively reduced the apparent cost of a deeper floor in calm
markets. All figures above are post-correction.

## Consequence for the layer decision

The recommended fix — **auction floor 75% instead of 85%** — is a static constant
frozen at compile time. It requires no global state, no governance, and no
aggregate read. **It works identically on Kaspa L1 and on Igra EVM.**

The only serious technical disadvantage of the Kaspa L1 path has therefore
disappeared. What remains against L1 is non-technical: no prior art, and almost no
auditors with covenant experience.
