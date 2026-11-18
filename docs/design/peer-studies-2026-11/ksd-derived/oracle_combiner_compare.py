#!/usr/bin/env python3
"""Why: compare, on injected oracle errors and manipulations, how much of the error reaches the price used by the
vaults when three oracles are combined by a 30/30/40 weighted mean versus by the median (owner question 2026-11-15:
"plusieurs oracles a 30/30/40", then "la mediane"; decision itself NOT taken).

Illustration only: the honest-noise level (HONEST_SIGMA) and the shapes of the injected errors are ASSUMPTIONS, not
measurements of any real oracle. Normalised truth P = 1. Deterministic (fixed seed), standard library only.
Run: python3 -I -B oracle_combiner_compare.py
"""
import random
import statistics

W = (0.30, 0.30, 0.40)          # weights of oracles A, B, C (owner's example)
HONEST_SIGMA = 0.005            # ASSUMPTION: each honest oracle reads the truth with 0.5 % noise
MCR, ICR0 = 1.50, 2.00          # ENRK frozen doc: liquidation threshold; fresh vault ratio
WRONG_LIQ_BELOW = MCR / ICR0    # reported price under this wrongly liquidates a fresh 200 % vault (0.75)
OVERBORROW_ABOVE = 1.0 / 0.8    # reported price over this lets a vault borrow 25 % more than it should (illustrative)
SEED = 20261115

def mean_w(v):   return sum(w * x for w, x in zip(W, v))
def median3(v):  return sorted(v)[1]

def weighted_median(v):
    order = sorted(zip(v, W))
    acc = 0.0
    for x, w in order:
        acc += w
        if acc >= 0.5:
            return x
    return order[-1][0]

RULES = (("weighted mean 30/30/40", mean_w), ("median of 3", median3), ("weighted median 30/30/40", weighted_median))

def honest(rng):  return [1 + rng.gauss(0, HONEST_SIGMA) for _ in range(3)]

def calm_cost(n=200000):
    rng = random.Random(SEED)
    out = {}
    for name, f in RULES:
        errs = [f(honest(rng)) - 1 for _ in range(n)]
        out[name] = (statistics.pstdev(errs), max(abs(e) for e in errs))
    return out

def one_corrupted(who, k):
    rng = random.Random(SEED + who)
    v = honest(rng)
    v[who] *= k
    return v

def two_corrupted(a, b, k):
    rng = random.Random(SEED + 10 + a + b)
    v = honest(rng)
    v[a] *= k; v[b] *= k
    return v

def main() -> None:
    print(f"ASSUMPTION: honest noise {HONEST_SIGMA:.1%} per oracle; truth = 1.0. Wrong liquidation if price < {WRONG_LIQ_BELOW:.2f}.\n")
    print("1. Calm market, no attack (cost of using the median): std dev and worst error of the combined price")
    for name, (sd, mx) in calm_cost().items():
        print(f"   {name:<26} std {sd:.3%}   worst {mx:.2%}")
    print("\n2. One oracle reports k times the truth (others honest). Combined price, and the harm")
    print("   (WL = fresh 200% vaults wrongly liquidated; OB = vaults can borrow 25%+ too much)")
    print("   corrupted   k      weighted mean     median of 3     weighted median")
    for who, label in ((0, "A 30%"), (1, "B 30%"), (2, "C 40%")):
        for k in (0.0, 0.5, 2.0, 5.0):
            row = []
            for _, f in RULES:
                p = f(one_corrupted(who, k))
                tag = " WL" if p < WRONG_LIQ_BELOW else (" OB" if p > OVERBORROW_ABOVE else "   ")
                row.append(f"{p:6.3f}{tag}")
            print(f"   {label:<10} {k:>4}   " + "         ".join(row))
    print("\n3. Two oracles corrupted the same way (the median is no longer protected)")
    print("   corrupted      k      weighted mean     median of 3")
    for (a, b), label in (((0, 1), "A+B 60%"), ((0, 2), "A+C 70%"), ((1, 2), "B+C 70%")):
        for k in (0.0, 0.5, 2.0):
            pm = mean_w(two_corrupted(a, b, k)); pd = median3(two_corrupted(a, b, k))
            print(f"   {label:<12} {k:>4}   {pm:12.3f}      {pd:12.3f}")
    print("\n4. One oracle offline (value missing). A rule is needed; ASSUMED here: median/mean of the two that remain")
    rng = random.Random(SEED + 99)
    v = honest(rng)
    for dead in (0, 1, 2):
        rest = [x for i, x in enumerate(v) if i != dead]
        ws = [w for i, w in enumerate(W) if i != dead]
        wm = sum(w * x for w, x in zip(ws, rest)) / sum(ws)
        md = sum(rest) / 2
        print(f"   oracle {'ABC'[dead]} offline: weighted mean {wm:.3f}   median of the remaining two {md:.3f}")
    print("   One offline AND one corrupted to 0: with two values left, the 'median' is their average = 0.5; a rule for")
    print("   this case (stop, or use the more prudent value) must be decided in advance.")
    print("\n5. Reading: with k=0 (price 0, the I26 case) and a 30% oracle the weighted mean gives 0.70 -> WL; the")
    print("   median gives about 1.00. The weighted median of 30/30/40 is always the middle value, i.e. the plain median.")

if __name__ == "__main__":
    main()
