"""Why: experiment catalogue for ECON-W1 (unit of account as a variable; crash grid WB and re-base WC), owner question 2026-11-11.
Unit scenario key = (unit, mode). Modes for FX-like units: s0 = stochastic with measured vol/drift (2023-03..2026-11, units_hist.json), s+X / s-X = same plus a log-linear
ramp of the unit's USD value by X% over the 60 crash days (+ = unit revalues vs USD = debt value up = adverse for the system; - = unit loses USD value = adverse for holders),
j+20/j-20 = step by 20% on crash day 5, boot = random historical 60-day window (2005-2026, same start for every unit on a path). U0/U5 reuse the v6/v1 index bases.
KAS drawdown, junior and fee architectures as v1 (E6): A0 r0 s0 | A3 r3 s30 S1 | A5 r3 s30 S3 | A8 r3 s50 S1 | STACK r3 s70 S3 + C1a(g=0) + C2."""
import v1_exp as X
FROZEN = X.FROZEN
FX = ("U2", "U3", "U3b_eq", "U3b_532", "U4", "U6")
ARCH = {"A0": X.arch(0.0, 0.0), "A3": X.arch(.03, .30), "A5": X.arch(.03, .30, "D1", "S3"), "A8": X.arch(.03, .50),
        "STACK": dict(**X.arch(.03, .70, "D1", "S3"), **X.C1V["C1a_g0+C2"])}
def unit_kw(unit, mode):
    """Scenario kwargs fixed by the unit variant (independent of path); path-dependent parts are built by build_path."""
    if unit == "U1": return dict(index_mode="flat")
    if unit in ("U0", "U5"):
        kw = dict(index_mode="proc", idx_vol=.22, idx_rho=0.0) if mode == "p_base" else dict(index_mode="det", idx_target=float(mode[1:]))
        if unit == "U5": kw["idx_max_up_step"] = .0025
        return kw
    return dict(index_mode="path")
def unit_scens(depth):
    out = [("U1", "flat")]
    out += [("U0", m) for m in ("p_base", "x1.5", "x2")] + [("U5", m) for m in ("p_base", "x1.5", "x2")]
    if depth == 85:
        out += [("U2", m) for m in ("s0", "s+5", "s-5", "s+10", "s-10", "s+20", "s-20", "boot", "j+20", "j-20")]
        for u in FX[1:]: out += [(u, m) for m in ("s0", "s+10", "s-10", "s+20", "s-20", "boot")]
    else:
        out += [("U2", m) for m in ("s0", "s+10", "s+20", "s-20", "boot")]
        for u in FX[1:]: out += [(u, m) for m in ("s0", "boot", "s+20", "s-20")]
    return out
def wb():
    """crash grid: unit x architecture x KAS drawdown"""
    cells = []
    for depth in (85, 70):
        for (u, m) in unit_scens(depth):
            for a, akw in ARCH.items():
                cells.append(((u, m, depth, a), dict(unit=u, mode=m, dd=depth / 100.0, kw=dict(akw))))
    return cells
def wc():
    """re-base: fee r x junior share s (D1/S1) on KAS -85%, per unit; plus redemption-off checks"""
    cells = []
    scs = [("U1", "flat"), ("U0", "p_base"), ("U0", "x1.5"), ("U5", "p_base"), ("U5", "x1.5")]
    for u in FX: scs += [(u, "s0"), (u, "boot"), (u, "s+10")]
    for (u, m) in scs:
        for r in (0.0, .01, .02, .03):
            for s in (0.0, .15, .30, .50):
                cells.append(((u, m, 85, f"r{r*100:g}_s{s*100:g}"), dict(unit=u, mode=m, dd=.85, kw=X.arch(r, s))))
    for (u, m) in (("U1", "flat"), ("U0", "p_base"), ("U2", "boot"), ("U3b_eq", "boot"), ("U6", "boot")):
        cells.append(((u, m, 85, "r3_s30_NOREDEMPTION"), dict(unit=u, mode=m, dd=.85, kw=dict(**X.arch(.03, .30), enable_redemption=False))))
    return cells
def wd():
    """replay of the worst historical 60-day window (2005-2026) of each unit: worst up (unit revalues) and worst down; KAS -85% and A0/A3/A5/A8/STACK"""
    cells = []
    for u in FX:
        for m in ("worst+", "worst-"):
            for a, akw in ARCH.items():
                cells.append(((u, m, 85, a), dict(unit=u, mode=m, dd=.85, kw=dict(akw))))
    return cells
EXPS = {"WB": wb, "WC": wc, "WD": wd}
