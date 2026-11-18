#!/usr/bin/env python3
"""Why: measure, with ENRK's own thresholds, how much liquidation delay a KSD-style limit on how fast the
liquidation price may FALL (25 %/h in KSD) would add after a sudden drop (decision: owner "oui" 2026-11-15 to
point 1 of the KSD-derived list; the limit itself is NOT an ENRK design decision).

Analytic model, hourly resolution, standard library only, no randomness. It does not touch the W2 simulator
(whose step is one day and which has no oracle lag, so a per-hour limit cannot bind there; see the note).

Model: real price P drops at t=0 by D (gap) from P0 and then stays flat (or keeps falling at f per hour, a swept
ASSUMPTION). The price used for liquidation, l(t) = max(P(t), P0 * (1-r)**t), cannot fall faster than r per hour.
A vault with ratio ICR0 at P0 is liquidatable when its ratio at l(t) is below MCR (ENRK frozen doc: 1.50).
Run: python3 -I -B asym_limit_lag.py
"""
import math

MCR = 1.50          # ENRK liquidation threshold (FROZEN_PARAMETERS.md, 2026-09-03)
AUCTION_MIN = 120   # ENRK Dutch auction duration in minutes (same document)

def delay_hours(icr0: float, drop: float, r: float, fall_per_h: float = 0.0) -> float | None:
    """Hours until the lagged price makes the vault liquidatable, or None if it is never needed."""
    p = lambda t: (1 - drop) * (1 - fall_per_h) ** t           # real price / P0 (after the gap)
    lag = lambda t: max(p(t), (1 - r) ** t)                    # liquidation price / P0
    if icr0 * p(0) >= MCR and fall_per_h == 0.0:
        return None                                            # not liquidatable at the real price
    t = 0.0
    while t < 48.0:                                            # 1-minute grid, 48 h horizon
        if icr0 * lag(t) < MCR:
            return t
        t += 1.0 / 60.0
    return None

def ratio_at_trigger(icr0: float, drop: float, t: float, fall_per_h: float) -> float:
    """Real ratio of the vault at the time the lagged price lets it be liquidated."""
    return icr0 * (1 - drop) * (1 - fall_per_h) ** t

def main() -> None:
    r = 0.25
    print("Closed form check: hours for a -D gap to be fully reflected at 25 %/h: ln(1/(1-D))/ln(1/0.75)")
    for d in (0.20, 0.40, 0.50):
        print(f"  D={d:.0%}: {math.log(1/(1-d))/math.log(1/(1-r)):.3f} h = {60*math.log(1/(1-d))/math.log(1/(1-r)):.0f} min")
    print("\nLiquidation delay added by the limit (minutes), real price flat after the gap")
    print("  vault ICR at P0 ->   1.55   1.75   2.00   2.50")
    for d in (0.20, 0.30, 0.40, 0.50, 0.60):
        row = []
        for icr in (1.55, 1.75, 2.00, 2.50):
            h = delay_hours(icr, d, r)
            row.append("   -- " if h is None else f"{60*h:6.0f}")
        print(f"  gap {d:.0%}:        " + " ".join(row))
    print("  ('--' = not liquidatable even at the real price)")
    print("\nReal ratio of a 200% vault at the moment it becomes liquidatable, by gap and continued fall per hour")
    print("(continued fall = swept ASSUMPTION, not measured). Below 100% = bad debt before any auction starts.")
    print("  gap \\ fall/h ->    0%     5%    10%")
    for d in (0.30, 0.40, 0.50):
        row = []
        for f in (0.0, 0.05, 0.10):
            h = delay_hours(2.00, d, r, f)
            row.append("   -- " if h is None else f"{ratio_at_trigger(2.00, d, h, f):6.2f}")
        print(f"  {d:.0%}:             " + " ".join(row))
    print("\nWithout the limit the same vault is liquidatable at once (delay 0) at ratio 2.00*(1-D).")
    print("ENRK's auction itself lasts up to", AUCTION_MIN, "min after trigger (frozen doc), a separate latency.")
    print("\nDaily-step view: a 25 %/h limit allows a daily fall of", f"{1-(1-r)**24:.4%}", "so it cannot bind at daily steps.")

if __name__ == "__main__":
    main()
