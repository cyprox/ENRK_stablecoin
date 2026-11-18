# Point 1 of the KSD-derived list: limits on how fast the oracle price may move

**Date:** 2026-11-15. **Status:** analysis only. Owner go ("oui") covers measuring this idea; it is **not** a design decision. Script: `asym_limit_lag.py`, output `asym_limit_lag_output.txt` (reproduce: `python3 -I -B asym_limit_lag.py`, standard library, deterministic).

## What KSD does
Mint price may rise at most 10%/h; liquidation price may fall at most 25%/h (KSD whitepaper, checked in `kaspadollar/evidence/03`). ENRK's KAS collateral oracle as audited has **no bound on a single-round move** (`PROJECT-STATE.md`, items 1e and audit I26).

## Why the W2 simulator cannot answer this
W2 steps one day at a time, has no oracle lag and no oracle-manipulation scenario. A 25%/h limit allows a daily fall of 99.9% (script, last line), so it can never bind at daily resolution. A "simulation" there would be null by construction, so none was run and the simulator was not changed. The benefit of such a limit (protection against a false price) has no model in the repository either.

## What was measured (analytic, hourly, ENRK thresholds: MCR 150% from `FROZEN_PARAMETERS.md`)
Cost side only: how long the limit delays liquidation after a sudden drop, real price flat afterwards.
- A vault minted at 200% becomes liquidatable **60 min** after the gap, whatever the gap size (it is the time for the lagged price to fall 25%: `ln(ICR0/MCR)/ln(4/3)`). At 175%: 33 min. At 250%: 107 min (only if the gap is at least 50%). A vault at 155%: 7 min.
- The real ratio of that 200% vault when it can finally be liquidated: 1.40 after a −30% gap, 1.20 after −40%, 1.00 after −50% if the price stays flat; if it keeps falling 5%/h during that hour: 1.33, 1.14, 0.95; at 10%/h: 1.26, 1.08, 0.90. The continued-fall rates are swept assumptions, not measured.
- So the extra loss risk is the price move during that hour; it becomes bad debt before any auction starts only for gaps of about 50% or more combined with a continued fall. ENRK's own 120-min Dutch auction is a separate latency on top.
- Note the difference of definition: KSD's whitepaper quotes 36 min after −20% (time to profitability at 5% penalty); the table above uses time to trigger at MCR 150%.

## What this does and does not show
- The delay depends on the vault's ratio, not on the size of the gap, once the vault is liquidatable at the real price.
- KAS's worst single day in the repository's market study is −24.9% (`r4-market.md`). A 25%/h limit would therefore rarely bind on any observed daily move; as a market-move filter it is almost inert, and its value would be against oracle errors or manipulation (not modelled here). A tighter limit (for example 10%/h) would bind on real crashes and cost more delay. Intraday KAS data, which the repository does not hold, would be needed to calibrate.
- Nothing here is evidence that the limit helps ENRK; it bounds the cost of adding one.

## To go further (needs owner go)
1. An hourly or intraday price series for KAS, then an hourly crash model next to W2 (new stage, all options OFF equals the previous behaviour, as for W1/W2 checks).
2. An oracle-error / manipulation scenario, otherwise the benefit stays unmeasurable.
3. Decide first whether ENRK's collateral oracle should have a per-round bound at all (audit I26 is open).

Checks run: script exit 0, output identical on re-run; qgate reports only T201 (`print`, 13), the print-policy question already open for the simulators. No independent reviewer run yet.
