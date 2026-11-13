"""Why: transparent borrower-demand model for ENRK debt vs all-in cost (scratch modelling, decision ref: none known).

Every input is labelled MEASURED / SECONDARY / ASSUMED. Every output is a model result, not a forecast.
Pure python (math only). Usage: python3 -I t2_demand.py > tables.md ; also writes grid.csv next to it.
"""
import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- Inputs ----------------
RS = [0, 1, 2, 3, 4, 5, 7, 10]                 # % per year, requested sweep
XS = [0, 5, 10, 15]                            # extra borrower cost, pts of debt per year (surplus withholding)
ICRS = [200, 250, 300]

# MEASURED-in-model (econ-m1-normal-time.md s4, mix of 4 regimes, churn 1, q 2%): y* in % of debt/yr, includes the 2% mint fee at churn 1
YSTAR_MIX = {200: {0: 12.2, 2: 14.0, 5: 16.9}, 250: {0: 5.0, 2: 7.1, 5: 10.4}, 300: {0: 2.6, 2: 4.8, 5: 8.0}}
# calm-only view (econ-m1 s4 text, ICR 250): 3.8 / 6.0 / 9.1
YSTAR_CALM = {250: {0: 3.8, 2: 6.0, 5: 9.1}}
MINT_FEE = 2.0       # MEASURED (FROZEN_PARAMETERS s6), % of debt per borrow
# liquidation-fee income, % of average debt per yr, backed out of econ-m1 s2 (total at r=2%, minus 2 mint, minus 2 stab, minus 0.03 red):
# ICR 200/250/300 totals 14.84/9.03/6.82 (mix); calm ICR250 liq ~1.05
LIQ_MIX = {200: 10.81, 250: 5.00, 300: 2.79}
LIQ_CALM = {250: 1.05}
RED = 0.03


def ystar(r, icr, regime="mix"):
    """Piecewise-linear in r on the M1 points (0,2,5); beyond 5 extrapolated with the last slope (ASSUMED)."""
    tab = (YSTAR_MIX if regime == "mix" else YSTAR_CALM)[icr]
    if r <= 2:
        return tab[0] + (tab[2] - tab[0]) * r / 2
    if r <= 5:
        return tab[2] + (tab[5] - tab[2]) * (r - 2) / 3
    return tab[5] + (tab[5] - tab[2]) / 3 * (r - 5)


# horizon distributions (ASSUMED): list of (T years, weight)
def horizon(name):
    if name == "T1":
        return [(1.0, 1.0)]
    n = 40
    from statistics import NormalDist
    nd = NormalDist()
    med, sg = {"Tmix": (0.5, 1.0), "Tshort": (0.25, 1.0)}[name]
    out = []
    for i in range(n):
        q = (i + 0.5) / n
        t = med * math.exp(sg * nd.inv_cdf(q))
        out.append((min(max(t, 1 / 12), 5.0), 1.0 / n))
    return out


def ystar_T(r, icr, T, X, regime):
    # M1 y* embeds mint fee 2% at churn 1 (T=1); replace by 2%/T; add surplus-withholding cost X
    return ystar(r, icr, regime) - MINT_FEE + MINT_FEE / T + X


# ---------------- Demand distributions: survival function S(x)=P(y>x), y in % per yr ----------------
def sf_normal(x, m, s):
    return 0.5 * math.erfc((x - m) / (s * math.sqrt(2)))


def make_set(kind, **p):
    if kind == "lognormal":
        return lambda x: 1.0 if x <= 0 else sf_normal(math.log(x), math.log(p["med"]), p["sig"])
    if kind == "exp":
        return lambda x: 1.0 if x <= 0 else math.exp(-x / p["mean"])
    if kind == "pareto":
        return lambda x: 1.0 if x <= p["xm"] else (p["xm"] / x) ** p["alpha"]
    if kind == "normal":
        return lambda x: sf_normal(x, p["m"], p["s"])
    raise ValueError(kind)


# ASSUMED parameter sets (no data exist for ENRK borrowers; chosen to span plausible stablecoin-use returns)
SETS = {
    "L8  lognormal med 8%, sig 0.9": make_set("lognormal", med=8, sig=0.9),
    "L4  lognormal med 4%, sig 0.9": make_set("lognormal", med=4, sig=0.9),
    "L12 lognormal med 12%, sig 0.9": make_set("lognormal", med=12, sig=0.9),
    "E8  exponential mean 8%": make_set("exp", mean=8),
    "P   Pareto xm 2.5% alpha 1.5 (mean 7.5%)": make_set("pareto", xm=2.5, alpha=1.5),
    "K15 long-KAS belief N(15%, 40%)": make_set("normal", m=15, s=40),
    "K0  long-KAS belief N(0%, 40%)": make_set("normal", m=0, s=40),
}


def demand(S, r, icr, X, hz, regime="mix"):
    d = 0.0
    inc = 0.0
    for T, w in hz:
        sv = S(ystar_T(r, icr, T, X, regime))
        d += w * sv
        liq = (LIQ_MIX if regime == "mix" else LIQ_CALM)[icr]
        inc += w * sv * (r + MINT_FEE / T + liq + RED + X)   # income per unit population debt, % per yr
    return d, inc


# ---------------- M2 junior equilibrium (econ-m2 s2, s=30, D1/S1, 'held' = sold on receipt) ----------------
M2_R = [0, 1, 2, 3, 5]
M2_CALM = [0.0, 3.3, 6.7, 10.0, 15.6]       # calm-year junior net, % of face
M2_CYC = [-10.0, -5.8, -2.4, 1.8, 8.6]       # pre-year + crash net, % of face
W = 0.10                                     # crash probability per year used by M2 T7 (w = 10%)


def interp_ext(xs, ys, x):
    if x <= xs[-1]:
        for i in range(len(xs) - 1):
            if xs[i] <= x <= xs[i + 1]:
                return ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i])
    sl = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])     # extrapolation beyond r=5: ASSUMED linear
    return ys[-1] + sl * (x - xs[-1])


def Ew(r, mint_extra=0.0):
    # mint_extra: junior share of mint fee income, pts of face per yr (M2 ignores mint fee; variant only)
    return (1 - W) * (interp_ext(M2_R, M2_CALM, r) + mint_extra) + W * interp_ext(M2_R, M2_CYC, r)


def r_clear(h, mint_extra=0.0):
    lo, hi = 0.0, 40.0
    if Ew(lo, mint_extra) >= h:
        return 0.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if Ew(mid, mint_extra) >= h:
            hi = mid
        else:
            lo = mid
    return hi


# tabulated s* crossings (linear interpolation of econ-m2 T7 on r at s*=30) for the S2 variant; None = not tabulated
RCLEAR_S2 = {5: None, 10: 1.5, 20: 3.4}      # h=5: s*=27 at r=0 (clears below ~1); h=20: upper-bound-ish, s*=25@3, >=50@5


def main():
    out = []
    P = out.append
    rows = []
    fine = [i * 0.05 for i in range(0, 201)]
    P("# T2 tables (generated by t2_demand.py; model results, not forecasts)\n")
    summary = {}
    for hzname in ["T1", "Tmix"]:
        hz = horizon(hzname)
        for regime in ["mix"]:
            for icr in ICRS:
                for X in XS:
                    for name, S in SETS.items():
                        d0, i0 = demand(S, 0, icr, X, hz, regime)
                        dref0, _ = demand(S, 0, icr, 0, hz, regime)
                        for r in RS:
                            d, inc = demand(S, r, icr, X, hz, regime)
                            rows.append([hzname, regime, icr, X, name, r, round(d, 5), round(d / dref0, 5), round(inc, 4)])
    # calm regime at ICR 250
    for X in XS:
        for name, S in SETS.items():
            dref0, _ = demand(S, 0, 250, 0, horizon("T1"), "calm")
            for r in RS:
                d, inc = demand(S, r, 250, X, horizon("T1"), "calm")
                rows.append(["T1", "calm", 250, X, name, r, round(d, 5), round(d / dref0, 5), round(inc, 4)])
    with open(os.path.join(HERE, "grid.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["horizon", "regime", "icr", "X_pts", "set", "r_pct", "D_abs", "D_rel_to_r0_X0", "income_pct_of_pop_debt"])
        w.writerows(rows)

    def key(hzname, regime, icr, X, name, r):
        for x in rows:
            if x[0] == hzname and x[1] == regime and x[2] == icr and x[3] == X and x[4] == name and x[5] == r:
                return x
        raise KeyError

    # ---- T-A demand tables
    for hzname, regime, icr in [("T1", "mix", 250), ("T1", "mix", 200), ("T1", "mix", 300), ("Tmix", "mix", 250), ("T1", "calm", 250)]:
        P(f"\n## TA. D(r) relative to D(r=0, X=0) of the same set; horizon {hzname}, regime {regime}, opening ICR {icr}\n")
        P("Rows: set, X (extra borrower cost, pts). Columns r = " + ", ".join(f"{r}%" for r in RS) + "   | D_abs(r=0,X=0) = fraction of the reference population that opens a vault\n")
        P("| set | X | " + " | ".join(f"r={r}" for r in RS) + " | D_abs(0) |")
        P("|---|---|" + "---|" * (len(RS) + 1))
        for name in SETS:
            for X in XS:
                vals = [key(hzname, regime, icr, X, name, r)[7] for r in RS]
                dabs = key(hzname, regime, icr, X, name, 0)[6]
                P(f"| {name.split('  ')[0].split(' ')[0]} | {X} | " + " | ".join(f"{v:.2f}" for v in vals) + f" | {dabs:.3f} |")

    # ---- T-B revenue / Laffer, cliff, semi-elasticity, junior clearing
    P("\n## TB. Laffer, cliff, junior yield and M2 intersection (horizon T1, mix, ICR 250 unless stated)\n")
    P("R(r) = income per unit of reference-population debt = sum over opening borrowers of (r + 2/T + liq(ICR) + 0.03 + X). 'argmax' on a 0.05 grid over 0..10%. 'r50' = r where D falls to 50% of D(r=0,X) ('>10' if not reached). 'semi' = % change in D per +1 pt of r around r=2 (D(3)-D(1))/2/D(2).\n")
    P("| set | ICR | X | argmax R (%) | R(argmax)/R(0) | R(10)/R(0) | argmax r*D (stab fee only) | r50 (%) | semi at r=2 | D(2)/D(0) |")
    P("|---|---|---|---|---|---|---|---|---|---|")
    hz = horizon("T1")
    laffer = {}
    for name, S in SETS.items():
        for icr in ICRS:
            for X in XS:
                best = max(fine, key=lambda r: demand(S, r, icr, X, hz)[1])
                rbest = demand(S, best, icr, X, hz)[1]
                r0 = demand(S, 0, icr, X, hz)[1]
                r10 = demand(S, 10, icr, X, hz)[1]
                d0 = demand(S, 0, icr, X, hz)[0]
                r50 = next((r for r in fine if demand(S, r, icr, X, hz)[0] < 0.5 * d0), None)
                d1, d2, d3 = (demand(S, r, icr, X, hz)[0] for r in (1, 2, 3))
                rs = max(fine, key=lambda r: r * demand(S, r, icr, X, hz)[0])
                semi = (d3 - d1) / 2 / d2 if d2 > 0 else float("nan")
                laffer[(name, icr, X)] = (best, r50)
                if icr == 250 or X == 0:
                    P(f"| {name.split(' ')[0]} | {icr} | {X} | {best:.2f} | {rbest / r0:.2f} | {r10 / r0:.2f} | {rs:.2f} | {('%.2f' % r50) if r50 is not None else '>10'} | {semi * 100:.0f}% | {d2 / d0:.2f} |")

    # junior
    P("\n## TC. Junior gross yield at s=30% (D1: all fees to junior), % of junior face per yr, stability fee only r/s and all fees (T=1, ICR 250, mix)\n")
    P("| r | r/s (stab only) | (r+2+5.0+0.03)/s (all fees, mix liq) | calm liq (1.05): all fees/s |")
    P("|---|---|---|---|")
    for r in RS:
        P(f"| {r} | {r / 0.3:.1f} | {(r + MINT_FEE + LIQ_MIX[250] + RED) / 0.3:.1f} | {(r + MINT_FEE + LIQ_CALM[250] + RED) / 0.3:.1f} |")
    P("\nFixed junior pool K sized so that s=30% at the r=0, X=0 demand of the set (K = 3/7 * D(0)), pool yield = income(r)/K, deployed = min(K, 3/7 D(r)); idle share = 1 - deployed/K. (T1, ICR 250, X=0)\n")
    P("| set | r | income(r)/income(0) | pool yield all fees (%) | idle share of pool | stab-only pool yield (r*D/K, %) |")
    P("|---|---|---|---|---|---|")
    for name, S in SETS.items():
        d00, i00 = demand(S, 0, 250, 0, hz)
        K = 3 / 7 * d00
        for r in [0, 2, 3, 5, 10]:
            d, inc = demand(S, r, 250, 0, hz)
            dep = min(K, 3 / 7 * d)
            P(f"| {name.split(' ')[0]} | {r} | {inc / i00:.2f} | {inc / K:.1f} | {1 - dep / K:.2f} | {r * d / K:.1f} |")

    P("\n## TD. r at which a 30% voluntary junior clears (M2, w=10%/yr crash probability), by h\n")
    P("D1/S1 and D1/S3 (junior income equal): from M2 cell values (s=30 junior net, calm year + cycle), E_w(r)=0.9*calm+0.1*cycle, linear in r, extrapolated beyond r=5 with the last slope (EXTRAPOLATED, M2 did not run r>5). Cross-check vs M2 s* table interpolation: h=5 1.67, h=10 3.06.\n")
    P("| h | r_clear D1/S1 | r_clear S1 + mint-fee income to junior (T=1, +6.7 pts face/yr in calm) | r_clear D1/S2 (M2 s* table) |")
    P("|---|---|---|---|")
    rc = {}
    for h in (5, 10, 20):
        a = r_clear(h)
        b = r_clear(h, mint_extra=MINT_FEE / 0.3)
        rc[h] = a
        s2 = RCLEAR_S2[h]
        P(f"| {h}% | {a:.2f} | {b:.2f} | {('<1 (s*=27 at r=0)' if s2 is None else '%.1f' % s2)} |")

    P("\n## TE. Is the clearing r inside the range where demand survives? D(r_clear)/D(0) and R(r_clear)/R(argmax) per set (T1, ICR 250, X as stated, S1 clearing r for X=0; S2 clearing r for X>0 shown second)\n")
    P("| set | X | h | r_clear (S1) | D/D0 at r_clear | R/Rmax | r_clear (S2) | D/D0 | R/Rmax |")
    P("|---|---|---|---|---|---|---|---|---|")
    for name, S in SETS.items():
        for X in XS:
            d0 = demand(S, 0, 250, X, hz)[0]
            rmax = max(demand(S, r, 250, X, hz)[1] for r in fine)
            for h in (5, 10, 20):
                r1 = rc[h]
                d1_, i1_ = demand(S, r1, 250, X, hz)
                s2 = RCLEAR_S2[h]
                if X == 0:
                    s2txt = "-"
                else:
                    r2 = 0.5 if s2 is None else s2   # h=5: placeholder 0.5 (M2: clears below ~1), flagged
                    d2_, i2_ = demand(S, r2, 250, X, hz)
                    s2txt = f"{r2:.1f}{'*' if s2 is None else ''} | {d2_ / d0:.2f} | {i2_ / rmax:.2f}"
                if X == 0:
                    s2txt = "- | - | -"
                P(f"| {name.split(' ')[0]} | {X} | {h} | {r1:.1f} | {d1_ / d0:.2f} | {i1_ / rmax:.2f} | {s2txt} |")
    P("\n(* = r=0.5 used as placeholder for the h=5 S2 case, M2 only says it clears at r=0 with s*=27.)")
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
