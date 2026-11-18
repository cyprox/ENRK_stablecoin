#!/usr/bin/env python3
"""Why: tabulate what a per-sweep price bound (MOVE per GAP) really allows per hour and how long it takes to reflect
a real crash, to support the owner's decision on the oracle bound (audit I26; decision: owner go 2026-11-15,
decision itself NOT taken). Candidate values are a grid to read, not proposals.

Pure arithmetic, standard library only. Assumes ~10 DAA/s (measured 9.6 blocks/s on 2026-11-15, see
kaspadollar/evidence/03) so 600 DAA is about 1 minute (as in econ-v4 P20). Run: python3 -I -B oracle_bound_grid.py
"""
import math

def per_hour(move: float, gap_min: float) -> tuple[float, float]:
    n = 60.0 / gap_min
    return (1 + move) ** n, (1 - move) ** n

def minutes_to_reflect(real_drop: float, move: float, gap_min: float) -> float:
    return gap_min * math.log(1 - real_drop) / math.log(1 - move)

def main() -> None:
    print("A. What a per-sweep bound allows per hour if sweeps may be chained at the minimum gap")
    print("   move/sweep  gap(min)   max up x/h     max down x/h")
    for m, g in ((0.10, 1), (0.10, 10), (0.02, 1), (0.02, 10), (0.01, 1), (0.01, 10), (0.002, 1)):
        up, dn = per_hour(m, g)
        print(f"   {m:>8.1%}   {g:>6}     {up:>12,.2f}   {dn:>14.6f}")
    print("\nB. Minutes for the published price to reflect a REAL fall (bound caps each sweep, sweeps at the minimum gap)")
    print("   move/sweep  gap(min)    -25% day   -50% fall")
    for m, g in ((0.10, 1), (0.10, 10), (0.02, 1), (0.02, 10), (0.01, 1), (0.01, 10)):
        print(f"   {m:>8.1%}   {g:>6}     {minutes_to_reflect(0.25, m, g):>7.0f}   {minutes_to_reflect(0.50, m, g):>9.0f}")
    print("\nC. Reaction time given to vault owners if a compromised publisher key pushes the price to -50% as fast as allowed")
    print("   (equal to column B, last column: owners can add collateral or repay during that time; nobody can pause)")
    print("\nD. Per-hour limit equivalents (KSD uses 25 %/h down, 10 %/h up): per-sweep move giving that hourly rate")
    for rate_h, up in ((0.25, False), (0.10, True)):
        for g in (1, 10):
            n = 60 / g
            m = (1 + rate_h) ** (1 / n) - 1 if up else 1 - (1 - rate_h) ** (1 / n)
            print(f"   {'up' if up else 'down'} {rate_h:.0%}/h with a sweep every {g} min -> {m:.3%} per sweep")

if __name__ == "__main__":
    main()
