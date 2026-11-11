"""Why: scenario and combo catalogue for ECON-V6 (index design fixes: L, breaker rewrite, clip/rate limit, kFIAT A1/A2), owner brief 2026-11-11.
Every parameter marked ASSUMED is a test value, not a recommendation. Base crash = ECON-T3 (KAS -85%/60 d, frozen floor 75%, redemption on, 1000 vaults, ICR 200%, D1, S1, stress 0.18)."""
import t3_scen as T
SCEN = dict(T.SCEN)
def add(name, dd, days, **kw): SCEN[name] = (kw, dd, days, "v6")
add("calm_flat", 0.0, 60, index_mode="flat")                                  # KAS median unchanged (jumps only), I = 1: false-positive reference
add("calm_p22", 0.0, 60, index_mode="proc", idx_vol=.22, idx_rho=0.0)
add("calm_p55", 0.0, 60, index_mode="proc", idx_vol=.55, idx_rho=0.0)
add("p_anch", .85, 60, index_mode="proc", idx_vol=.05, idx_rho=0.0, idx_jumps=False)   # USD-anchored electricity-like basket (a4: US retail 5% vol)
add("p_comm", .85, 60, index_mode="proc", idx_vol=.30, idx_rho=0.0)                     # commodity-energy-like (a4: 30% vol) with jumps
add("d85_x0.6", .85, 60, index_mode="det", idx_target=0.6)
TRIG = {   # label -> kwargs (brk_*)
    "none": {},
    "idx_latch_mint": dict(brk_trigger="idx", brk_action="mint", brk_latch=True),
    "idx_latch_red": dict(brk_trigger="idx", brk_action="red", brk_latch=True),
    "idx_latch_liq": dict(brk_trigger="idx", brk_action="liq", brk_latch=True),
    "idx_live_red": dict(brk_trigger="idx", brk_action="red", brk_latch=False),
    "idx_live_liq": dict(brk_trigger="idx", brk_action="liq", brk_latch=False),
    "hyst25_15_mint": dict(brk_trigger="hyst", brk_action="mint", brk_latch=False),
    "hyst25_15_red": dict(brk_trigger="hyst", brk_action="red", brk_latch=False),
    "hyst25_15_liq": dict(brk_trigger="hyst", brk_action="liq", brk_latch=False),
    "mkt5_live_mint": dict(brk_trigger="mkt", brk_action="mint", brk_latch=False),
    "mkt5_live_red": dict(brk_trigger="mkt", brk_action="red", brk_latch=False),
    "mkt5_live_liq": dict(brk_trigger="mkt", brk_action="liq", brk_latch=False),
    "mkt5_latch_liq": dict(brk_trigger="mkt", brk_action="liq", brk_latch=True),
    "mkt10_live_liq": dict(brk_trigger="mkt", brk_action="liq", brk_latch=False, brk_mkt_thr=.10),
    "fresh1_latch_red": dict(brk_trigger="fresh", brk_action="red", brk_latch=True),
    "fresh1_latch_liq": dict(brk_trigger="fresh", brk_action="liq", brk_latch=True),
    "fresh1_live_mint": dict(brk_trigger="fresh", brk_action="mint", brk_latch=False),
    "fresh1_live_liq": dict(brk_trigger="fresh", brk_action="liq", brk_latch=False),
    "fresh5_live_liq": dict(brk_trigger="fresh", brk_action="liq", brk_latch=False, fresh_hazard=.05),
}
SHAPE = {  # label -> kwargs (idx_*)
    "frozen": {},
    "hi2.0": dict(idx_clip_hi=2.0), "hi1.5": dict(idx_clip_hi=1.5), "hi1.25": dict(idx_clip_hi=1.25), "hi1.10": dict(idx_clip_hi=1.10),
    "lo.5_hi2": dict(idx_clip_lo=.5, idx_clip_hi=2.0), "lo.8_hi1.25": dict(idx_clip_lo=.8, idx_clip_hi=1.25),
    "slope.5": dict(idx_up_slope=.5), "slope.5_hi1.5": dict(idx_up_slope=.5, idx_clip_hi=1.5),
    "step1.0%": dict(idx_max_step=.010), "step.5%": dict(idx_max_step=.005), "step.25%": dict(idx_max_step=.0025),
    "step.5%_hi1.5": dict(idx_max_step=.005, idx_clip_hi=1.5),
}
S_BASE = ("orig85", "flat85", "p_base", "p_vol55", "p_anch", "p_comm", "d85_x0.6", "d85_x1.5", "d85_x2", "d85_x3", "ep2024_kas-50_I+52", "d70_x2", "flat70")
S_BRK = ("calm_flat", "calm_p22", "calm_p55", "flat85", "p_base", "d85_x1.5", "d85_x2", "ep2024_kas-50_I+52")
S_SHAPE = ("flat85", "p_vol55", "d85_x0.6", "d85_x1.5", "d85_x2", "d85_x3", "ep2024_kas-50_I+52")
S_KF = ("flat85", "d85_x1.5", "d85_x2", "p_base", "ep2024_kas-50_I+52")

def combos():
    """list of (label, group, scenario, kwargs, cells[(r,s,S)])"""
    out = []
    for sc in S_BASE: out.append((f"base|{sc}", "base", sc, {}, [(.03, 30, "S1"), (0.0, 0, "S1"), (.03, 0, "S1")]))
    for sc in S_BRK:
        for t, kw in TRIG.items(): out.append((f"brk|{sc}|{t}", "brk", sc, kw, [(.03, 30, "S1")]))
    for sc in S_SHAPE:
        for t, kw in SHAPE.items(): out.append((f"shape|{sc}|{t}", "shape", sc, kw, [(.03, 30, "S1")]))
    for sc in S_KF:
        for m in ("A1", "A2"): out.append((f"kf|{sc}|{m}", "kf", sc, dict(kfiat_mode=m), [(.03, 30, "S1"), (.03, 15, "S1"), (.03, 50, "S1"), (.03, 30, "S3")]))
    return out
