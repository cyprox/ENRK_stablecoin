"""Why: scenario catalogue and grid definitions for ECON-T3 (index dynamics inside the crash), owner brief 2026-11-10.
Index scenarios: name -> (kwargs for stress_fee.Scenario, KAS drawdown, crash_days, group). Index value I = peg (peg_0 = 1).
Component maths for named scenarios (weights .4/.3/.2/.1, other components 1.0): energy x2 -> I = 1 + .3 = 1.30;
hash-rate -60% -> I = 1 - .4*.6 = 0.76; 2024 episode: I = 1.52 over 97 days (econ-a4 s6)."""
SCEN = {}
def add(name, dd, days, group, **kw):
    SCEN[name] = (kw, dd, days, group)

# KAS -85% / 60 days (M2 frozen crash)
add("orig85", .85, 60, "ref85", index_mode="orig")           # M2/p3 baseline: elastic index, peg FALLS with KAS (~0.55 at the end)
add("flat85", .85, 60, "ref85", index_mode="flat")           # I == 1 for ever: the literal KAS-only crash
add("p_base", .85, 60, "proc85", index_mode="proc", idx_vol=.22, idx_rho=0.0)
add("p_rho-.5", .85, 60, "proc85", index_mode="proc", idx_vol=.22, idx_rho=-0.5)
add("p_rho+.5", .85, 60, "proc85", index_mode="proc", idx_vol=.22, idx_rho=0.5)
add("p_vol19", .85, 60, "proc85", index_mode="proc", idx_vol=.19, idx_rho=0.0)
add("p_vol26", .85, 60, "proc85", index_mode="proc", idx_vol=.26, idx_rho=0.0)
add("p_vol55", .85, 60, "proc85", index_mode="proc", idx_vol=.55, idx_rho=0.0)
add("p_vol55_rho-.5", .85, 60, "proc85", index_mode="proc", idx_vol=.55, idx_rho=-0.5)
add("p_nojump", .85, 60, "proc85", index_mode="proc", idx_vol=.22, idx_rho=0.0, idx_jumps=False)
add("d85_x1.5", .85, 60, "det85", index_mode="det", idx_target=1.5)
add("d85_x2", .85, 60, "det85", index_mode="det", idx_target=2.0)
add("d85_x3", .85, 60, "det85", index_mode="det", idx_target=3.0)
# KAS -70%
add("flat70", .70, 60, "ref70", index_mode="flat")
add("d70_x1.5", .70, 60, "det70", index_mode="det", idx_target=1.5)
add("d70_x2", .70, 60, "det70", index_mode="det", idx_target=2.0)
add("d70_x3", .70, 60, "det70", index_mode="det", idx_target=3.0)
add("N4_hash-60_kas-70", .70, 60, "named", index_mode="det", idx_target=0.76)
# KAS -50%
add("flat50", .50, 60, "ref50", index_mode="flat")
add("N2_energy2_kas-50", .50, 60, "named", index_mode="det", idx_target=1.30)
add("flat50_97d", .50, 97, "ref97", index_mode="flat")
add("ep2024_kas-50_I+52", .50, 97, "named", index_mode="det", idx_target=1.52)

FLAT_OF = {"orig85": "flat85", "flat85": "flat85", "p_": "flat85", "d85": "flat85", "d70": "flat70", "N4": "flat70",
           "N2": "flat50", "ep2024": "flat50_97d", "flat70": "flat70", "flat50": "flat50", "flat50_97d": "flat50_97d"}
def flat_for(name):
    for k, v in FLAT_OF.items():
        if name.startswith(k): return v
    raise KeyError(name)

REF = ("orig85", "flat85", "flat70", "flat50", "flat50_97d")
BRK_ALL = ("none", "mb", "liq_latch")
STRESS = (0.18, 0.25, 0.28, 0.32)

def combos(kind):
    """list of (scen, breaker, capacity_mode, stress). Cells = combos x (r,s,S) of the kind."""
    out = []
    if kind == "main":
        for sc in SCEN:
            active = sc not in ("flat85", "flat70", "flat50", "flat50_97d")
            for st in STRESS:
                for b in (BRK_ALL if active else ("none",)):
                    if st != 0.18 and b == "mb": continue
                    out.append((sc, b, "units", st))
    elif kind == "cap":      # liquidator capital in USD: units capacity falls as I rises
        for sc in ("p_base", "p_rho-.5", "d85_x1.5", "d85_x2", "d85_x3", "N2_energy2_kas-50", "ep2024_kas-50_I+52", "N4_hash-60_kas-70"):
            for b in ("none", "liq_latch"):
                out.append((sc, b, "value", 0.18))
    elif kind == "sstar":
        for sc in ("flat85", "orig85", "p_base", "p_rho-.5", "p_rho+.5", "p_vol55", "p_vol55_rho-.5", "d85_x1.5", "d85_x2", "d85_x3"):
            active = sc != "flat85"
            for st in (0.18, 0.25):
                for b in (("none", "liq_latch") if active else ("none",)):
                    out.append((sc, b, "units", st))
    return out

def cellgrid(kind):
    if kind in ("main", "cap"):
        return [(r, s, S) for r in (0.0, 0.03) for s in (0, 30) for S in ("S1", "S3")]
    return [(0.03, s, "S1") for s in (15, 30, 50)]
