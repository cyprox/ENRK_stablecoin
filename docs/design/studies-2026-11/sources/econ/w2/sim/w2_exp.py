"""Why: experiment catalogue for ECON-W2 (reactive borrowers: behaviours swept, architectures re-run without the exogenous cushions) (decision: owner approval of plan 2026-11-13).
Cells = (key, kwargs for stress_fee.Scenario); all cells of one experiment run on the same paths (path i = SEED+i): paired.
Frozen set-up as ECON-V1/W1 (floor 75%, ICR 200%, 1000 vaults, 365 calm days, stress 0.18, impact 0.08, capacity 5%/day, ADV 40M KAS), EXCEPT:
 - the exogenous redemption schedule is OFF in every headline cell (profile suffix N); the schedule cells (S0) are kept only as the W1 reference;
 - the index is never the elastic 'orig' cushion (bases: flat, x1.5, x2 ramps, 2024 episode).
Every behaviour parameter below is a SWEPT assumption: the central values are labels for the table, not estimates."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v1_exp as X
FROZEN = dict(auction_end_price=0.75)                       # redemption flag is set per profile
BASES = ("flat85", "d85_x1.5", "d85_x2", "flat70", "d70_x1.5", "d70_x2", "ep2024_kas-50_I+52")
BASES3 = ("flat85", "d85_x2", "ep2024_kas-50_I+52")
SHORT = {"flat85": "flat85", "d85_x1.5": "x1.5@85", "d85_x2": "x2@85", "flat70": "flat70", "d70_x1.5": "x1.5@70", "d70_x2": "x2@70", "ep2024_kas-50_I+52": "ep2024"}
ARCH = {"A0": X.arch(0.0, 0.0), "A3": X.arch(.03, .30), "A5": X.arch(.03, .30, "D1", "S3"), "A8": X.arch(.03, .50),
        "STACK": dict(**X.arch(.03, .70, "D1", "S3"), **X.C1V["C1a_g0+C2"])}
# --- behaviour blocks (central values; sweeps in oat()) ---
TOP = dict(rb_on=True, rb_att=.5, rb_trigger_icr=1.8, rb_delay=3, rb_hazard=.5, rb_topup=True, rb_target_icr=2.0, rb_budget=.15, rb_exit_mode="none")
EXIT = dict(rb_on=True, rb_att=.5, rb_trigger_icr=1.8, rb_delay=3, rb_hazard=.5, rb_topup=False, rb_budget=.15, rb_exit_mode="both", rb_exit_icr=1.6, rb_sell_slip=.03)
DEF = dict(TOP, rb_exit_mode="both", rb_exit_icr=1.6, rb_sell_slip=.03)
SPEC = dict(rb_spec_frac=.2, rb_spec_icr=1.7)
MIN = dict(rb_miner_frac=.2, rb_miner_opex=.004)
RUN = dict(rb_run_red=.15, rb_sig_icr=1.2, rb_red_dump=1.0)        # ENRK holders redeem at face and sell the KAS the same day
CENTRAL_B = dict(DEF, **SPEC, **MIN)                                 # borrower/miner behaviours only: NO redemption cushion of any kind
CENTRAL_R = dict(CENTRAL_B, **RUN, rb_run_b=.5)
FRIENDLY_B = dict(DEF, rb_att=.75, rb_delay=0, rb_hazard=1.0, rb_budget=.5)
HOSTILE_B = dict(DEF, rb_att=.25, rb_delay=7, rb_hazard=.25, rb_budget=.05, rb_exit_bump=.2, rb_spec_frac=.4, rb_spec_icr=1.65,
                 rb_miner_frac=.4, rb_miner_opex=.01)                # 'hostile' = chosen as adverse for the protocol on each borrower dimension (checked in OAT)
HOSTILE_R = dict(HOSTILE_B, **RUN, rb_run_b=.25)
_N = dict(enable_redemption=False)
PROF = {"N0": dict(_N), "S0": dict(enable_redemption=True),
        "TOP": dict(TOP, **_N), "EXIT": dict(EXIT, **_N), "DEF": dict(DEF, **_N), "SPEC": dict(SPEC, **_N), "MIN": dict(MIN, **_N), "RUN": dict(RUN, **_N),
        "CENTRAL_B": dict(CENTRAL_B, **_N), "FRIENDLY_B": dict(FRIENDLY_B, **_N), "HOSTILE_B": dict(HOSTILE_B, **_N),
        "CENTRAL_R": dict(CENTRAL_R, **_N), "HOSTILE_R": dict(HOSTILE_R, **_N)}
def cell(base, name, a, **extra):
    return ((base, name), {**X.scen_kw(base), **FROZEN, **a, **extra})
def hl():
    """headline: 5 architectures x 7 adverse bases x 11 profiles"""
    return [cell(b, f"{an}|{pn}", a, **p) for b in BASES for an, a in ARCH.items() for pn, p in PROF.items()]
def sens():
    """impact x capacity sensitivity: 5 architectures x 3 bases x {N0, CENTRAL_B, HOSTILE_B} x impact {.04,.08,.16} x capacity {2.5,5,10}%/day"""
    out = []
    for b in BASES3:
        for an, a in ARCH.items():
            for pn in ("N0", "CENTRAL_B", "HOSTILE_B"):
                for imp in (.04, .08, .16):
                    for cap in (.025, .05, .10):
                        out.append(cell(b, f"{an}|{pn}|imp{imp}|cap{cap*100:g}", a, **PROF[pn], impact_coefficient=imp, daily_liquidation_capacity=cap))
    return out
def oat():
    """one-at-a-time sweeps around CENTRAL_R (borrowers + run) on A3 / A5 (S3 withheld surplus) x flat85 / x2@85"""
    out = []
    grid = [("att", "rb_att", (0.0, .25, .5, .75, 1.0)), ("delay", "rb_delay", (0, 3, 7, 14)), ("hazard", "rb_hazard", (.25, .5, 1.0)),
            ("trigger", "rb_trigger_icr", (1.65, 1.8, 2.0)), ("target", "rb_target_icr", (1.8, 2.0, 2.5)), ("budget", "rb_budget", (.05, .15, .5, 1.0)),
            ("exit_icr", "rb_exit_icr", (1.55, 1.6, 1.7, 1.8)), ("exit_mode", "rb_exit_mode", ("none", "cash", "sell", "both")),
            ("slip", "rb_sell_slip", (0.0, .03, .10)), ("bump", "rb_exit_bump", (0.0, .1, .2, .3)),
            ("spec_frac", "rb_spec_frac", (0.0, .1, .2, .4)), ("spec_icr", "rb_spec_icr", (1.6, 1.65, 1.7, 1.8)),
            ("miner_frac", "rb_miner_frac", (0.0, .1, .2, .4)), ("miner_opex", "rb_miner_opex", (.001, .004, .01)),
            ("run_red", "rb_run_red", (0.0, .05, .15, .5)), ("run_b", "rb_run_b", (0.0, .25, .5, 1.0)), ("sig_icr", "rb_sig_icr", (1.1, 1.2, 1.3, 1.5)),
            ("red_dump", "rb_red_dump", (0.0, .5, 1.0))]
    for b in ("flat85", "d85_x2"):
        for an in ("A3", "A5"):
            for nm, k, vals in grid:
                for v in vals:
                    out.append(cell(b, f"{an}|{nm}={v}", ARCH[an], **{**PROF["CENTRAL_R"], k: v}))
            out.append(cell(b, f"{an}|ref_N0", ARCH[an], **PROF["N0"]))
    return out
def size():
    """sustainable-size curves: liquidator capital = 1% of ADV x price (USD), convex impact, size_scale sweep (as ECON-V1 E3)"""
    out = []
    for b in ("flat85", "d85_x2"):
        for an, a in ARCH.items():
            for pn in ("N0", "CENTRAL_B", "HOSTILE_B"):
                for adv in (70e6, 150e6):
                    for sc in (.05, .1, .2, .4, .7, 1.0):
                        out.append(cell(b, f"{an}|{pn}|adv{adv/1e6:g}|sc{sc}", a, **PROF[pn], size_scale=sc, daily_volume_kas=adv,
                                        capacity_mode="adv", adv_frac=.01, convex_impact=True))
    return out
EXPS = {"HL": hl, "SENS": sens, "OAT": oat, "SIZE": size}
if __name__ == "__main__":
    for k, f in EXPS.items(): print(k, len(f()))
