"""Why: experiment catalogue for ECON-V1 (architecture re-verification on adverse index bases), owner brief 2026-11-11.
A cell = (key, kwargs for stress_fee.Scenario).  All cells of one experiment are run on the same paths (path i = SEED+i): paired.
Adverse bases (frozen: floor 75%, redemption on, ICR 200%, 1000 vaults, 365-day calm pre-year, stress 0.18, impact .08, capacity 5%/day):
  flat85/flat70 (I=1), d85_x1.5/x2, d70_x1.5/x2 (index ramps to the multiple by day 60), ep2024 (KAS -50%, 97 d, I +52%), orig85 = cushioned reference."""
import sys
import t3_scen as T

SCEN8 = ("orig85", "flat85", "d85_x1.5", "d85_x2", "flat70", "d70_x1.5", "d70_x2", "ep2024_kas-50_I+52")
SHORT = {"orig85": "orig85(ref)", "flat85": "flat85", "d85_x1.5": "x1.5@85", "d85_x2": "x2@85", "flat70": "flat70",
         "d70_x1.5": "x1.5@70", "d70_x2": "x2@70", "ep2024_kas-50_I+52": "ep2024"}
FROZEN = dict(auction_end_price=0.75, enable_redemption=True)

def scen_kw(sc):
    kw, dd, days, _ = T.SCEN[sc]
    return dict(total_drawdown=dd, crash_days=days, **kw)

def arch(r, s, D="D1", S="S1", **extra):
    """architecture: fee r (fraction), junior share s (fraction), distribution rule, surplus rule"""
    d = dict(stability_fee=r, kfiat_share=s, dist_rule=D, surplus_rule=S)
    if S.startswith("SP"):
        _, pj, pr = S.split("_"); d.update(surplus_rule="SP", phi_j=float(pj), phi_r=float(pr))
    d.update(extra); return d

def cell(sc, name, a, **extra):
    return ((sc, name), {**scen_kw(sc), **a, **extra})

def e1():
    """P1/P2/P5: fee x junior share x distribution x surplus on the 8 bases"""
    out = []
    for sc in SCEN8:
        for r in (0.0, .01, .02, .03, .05):
            for s in (0.0, .15, .30, .50):
                out.append(cell(sc, f"r{r*100:g}_s{s*100:g}_D1_S1", arch(r, s)))
        for r in (.01, .03, .05):
            for s in (0.0, .15, .30, .50):
                for D in ("D2", "D3"):
                    out.append(cell(sc, f"r{r*100:g}_s{s*100:g}_{D}_S1", arch(r, s, D)))
        for r in (0.0, .03):
            for s in (0.0, .15, .30, .50):
                out.append(cell(sc, f"r{r*100:g}_s{s*100:g}_D1_S3", arch(r, s, "D1", "S3")))
        for r in (0.0, .03):
            for s in (.15, .30, .50):
                for pr in (.25, .5):
                    out.append(cell(sc, f"r{r*100:g}_s{s*100:g}_D1_SP_0_{pr}", arch(r, s, "D1", f"SP_0_{pr}")))
        # check cells for phi_j linearity
        out.append(cell(sc, "r3_s30_D1_SP_0.5_0.5", arch(.03, .30, "D1", "SP_0.5_0.5")))
        out.append(cell(sc, "r3_s30_D1_S2", arch(.03, .30, "D1", "S2")))
    return out

POLICIES = [("waterfall", None, "opening", "waterfall"),
            ("borrowers_first", None, "opening", "BF_uncapped"),
            ("borrowers_first", .02, "opening", "BF_cap2"), ("borrowers_first", .05, "opening", "BF_cap5"),
            ("borrowers_first", .10, "opening", "BF_cap10"), ("borrowers_first", .15, "opening", "BF_cap15"),
            ("kfiat_then_borrowers", None, "opening", "KB_uncapped"),
            ("kfiat_then_borrowers", .02, "opening", "KB_cap2"), ("kfiat_then_borrowers", .05, "opening", "KB_cap5"),
            ("kfiat_then_borrowers", .10, "opening", "KB_cap10"), ("kfiat_then_borrowers", .15, "opening", "KB_cap15"),
            ("borrowers_first", .05, "legacy", "BF_cap5_LEGACY"), ("kfiat_then_borrowers", .10, "legacy", "KB_cap10_LEGACY")]

def e2():
    """P4: loss rule on the 8 bases for two architectures; capacity sensitivity on 2 bases"""
    out = []
    for sc in SCEN8:
        for (r, s) in ((.03, .30), (0.0, .0)):
            for (pol, cap, basis, nm) in POLICIES:
                out.append(cell(sc, f"r{r*100:g}_s{s*100:g}_{nm}", arch(r, s), policy=pol, soc_cap=cap, soc_basis=basis))
    for sc in ("flat85", "d85_x2"):
        for capd in (.025, .10):
            for (pol, cap, basis, nm) in POLICIES:
                if nm in ("waterfall", "BF_uncapped", "BF_cap5", "KB_uncapped", "KB_cap5", "BF_cap5_LEGACY"):
                    out.append(cell(sc, f"cap{capd*100:g}_r3_s30_{nm}", arch(.03, .30), policy=pol, soc_cap=cap, soc_basis=basis,
                                    daily_liquidation_capacity=capd))
    return out

def e3():
    """P13: liquidator capital = adv_frac x ADV x price (USD-valued), convex impact, debt ceiling sweep via size_scale"""
    out = []
    for sc in ("flat85", "d85_x2", "d70_x2", "ep2024_kas-50_I+52"):
        for (r, s) in ((.03, .30), (0.0, 0.0)):
            for adv in (70e6, 150e6, 230e6):
                for scale in (.05, .1, .2, .4, .7, 1.0, 1.5):
                    for af in (.005, .01, .02):
                        out.append(cell(sc, f"r{r*100:g}_s{s*100:g}_adv{adv/1e6:g}_sc{scale}_af{af*100:g}", arch(r, s),
                                        size_scale=scale, daily_volume_kas=adv, capacity_mode="adv", adv_frac=af, convex_impact=True))
    # reference: the as-coded model (units capacity 5%, ADV 40M, sqrt impact) at the same scales
    for sc in ("flat85", "d85_x2"):
        for (r, s) in ((.03, .30), (0.0, 0.0)):
            for scale in (.1, .4, 1.0):
                out.append(cell(sc, f"r{r*100:g}_s{s*100:g}_ASCODED_sc{scale}", arch(r, s), size_scale=scale))
    return out

C1V = {"none": {}, "C2": dict(subpar_redemption=True),
       "C1a_g0": dict(c1_days=3, c1_step=.05, c1_min=.5, bidder_greed=0.0), "C1a_g.5": dict(c1_days=3, c1_step=.05, c1_min=.5, bidder_greed=.5),
       "C1a_g1": dict(c1_days=3, c1_step=.05, c1_min=.5, bidder_greed=1.0),
       "C1b_g0": dict(c1_days=2, c1_step=.10, c1_min=.4, bidder_greed=0.0), "C1b_g1": dict(c1_days=2, c1_step=.10, c1_min=.4, bidder_greed=1.0),
       "C1a_g0+C2": dict(c1_days=3, c1_step=.05, c1_min=.5, bidder_greed=0.0, subpar_redemption=True),
       "C1a_g1+C2": dict(c1_days=3, c1_step=.05, c1_min=.5, bidder_greed=1.0, subpar_redemption=True),
       "C1b_g0+C2": dict(c1_days=2, c1_step=.10, c1_min=.4, bidder_greed=0.0, subpar_redemption=True)}

def e4():
    """P14: C1/C2 where the freeze exists (stress >= 0.25) and at base stress; two capacities"""
    out = []
    for sc in ("flat85", "d85_x2", "d70_x2", "ep2024_kas-50_I+52"):
        for st in (.18, .28, .32):
            for capd in (.05, .025):
                for nm, mech in C1V.items():
                    out.append(cell(sc, f"r3_s30_st{st}_cap{capd*100:g}_{nm}", arch(.03, .30), stress_sensitivity=st,
                                    daily_liquidation_capacity=capd, **mech))
    return out

HEAD = {"A0_r0_s0": arch(0.0, 0.0), "A1_r0_s30": arch(0.0, .30), "A2_r3_s0": arch(.03, 0.0),
        "A3_r3_s30_D1_S1": arch(.03, .30), "A4_r3_s30_D3": arch(.03, .30, "D3"), "A5_r3_s30_S3": arch(.03, .30, "D1", "S3"),
        "A6_r3_s30_KBcap5": dict(**arch(.03, .30), policy="kfiat_then_borrowers", soc_cap=.05),
        "A7_r3_s30_C1a+C2": dict(**arch(.03, .30), **C1V["C1a_g0+C2"]),
        "A8_r3_s50": arch(.03, .50), "A9_r1_s30": arch(.01, .30)}

def e5():
    """sensitivity impact x capacity on headline architectures"""
    out = []
    for sc in ("flat85", "d85_x2", "ep2024_kas-50_I+52"):
        for nm, a in HEAD.items():
            for imp in (.04, .08, .16):
                for capd in (.025, .05, .10):
                    out.append(cell(sc, f"{nm}_imp{imp}_cap{capd*100:g}", a, impact_coefficient=imp, daily_liquidation_capacity=capd))
    return out

def e6():
    """headline architecture table: HEAD x 8 bases at base parameters"""
    return [cell(sc, nm, a) for sc in SCEN8 for nm, a in HEAD.items()]

STACK = {"B1_r3_s50_S3": arch(.03, .50, "D1", "S3"),
         "B2_r3_s50_S3_C1a+C2": dict(**arch(.03, .50, "D1", "S3"), **C1V["C1a_g0+C2"]),
         "B3_r3_s50_S3_C1a+C2_KB5": dict(**arch(.03, .50, "D1", "S3"), **C1V["C1a_g0+C2"], policy="kfiat_then_borrowers", soc_cap=.05),
         "B4_r3_s70_S3_C1a+C2": dict(**arch(.03, .70, "D1", "S3"), **C1V["C1a_g0+C2"]),
         "B5_r5_s50_S3_C1a+C2": dict(**arch(.05, .50, "D1", "S3"), **C1V["C1a_g0+C2"]),
         "B6_r3_s50_D1_C1a+C2": dict(**arch(.03, .50), **C1V["C1a_g0+C2"]),
         "B7_r0_s50_S3_C1a+C2": dict(**arch(0.0, .50, "D1", "S3"), **C1V["C1a_g0+C2"])}

def e7():
    """EXPLORATION (not requested levers combined): stacks of the tested levers, 8 bases"""
    return [cell(sc, nm, a) for sc in SCEN8 for nm, a in STACK.items()]

EXPS = {"E7": e7, "E1": e1, "E2": e2, "E3": e3, "E4": e4, "E5": e5, "E6": e6}
if __name__ == "__main__":
    for k, f in EXPS.items(): print(k, len(f()))
