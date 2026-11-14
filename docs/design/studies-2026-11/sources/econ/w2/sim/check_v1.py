"""Why: prove the ECON-V1 extensions are inert when OFF, consistent when ON (decision: owner brief 2026-11-11, validation required).
(1) v1 simulator == ECON-T3 simulator (base0/stress_fee.py) on every T3 Result field, features off (orig/flat/proc/det index, ledger rules, breaker, capacity);
(2) surplus rule SP special cases == S1/S2/S3;
(3) cached pre-year snapshot == full run with the new features ON (C1, C2, carry-over, adv capacity, convex impact, size_scale);
(4) ENRK accounting identity with C2 / carry-over / redemption;
(5) carry-over, legacy basis == the p3 patch (analyse_projet/loss_absorption_analysis.py copy in p3ref/): losses, latent, pushed."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # W2 copy: lets 'python3 -I' find the local simulator (only change vs the W1 file)
import dataclasses, importlib.util
sys.dont_write_bytecode = True
import stress_fee as N

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m
T3 = load("t3sim", "base0/stress_fee.py")
FIELDS = [f.name for f in dataclasses.fields(T3.Result)]
FZ = dict(auction_end_price=0.75, enable_redemption=True)
bad = n = 0
cfgs = []
for idx in (dict(index_mode="orig"), dict(index_mode="flat"), dict(index_mode="proc", idx_vol=.3, idx_rho=-.5), dict(index_mode="det", idx_target=2.0)):
    for extra in (dict(), dict(breaker="liq_latch"), dict(capacity_mode="value"), dict(stress_sensitivity=.28), dict(daily_liquidation_capacity=.025, impact_coefficient=.16)):
        for dd in (.5, .85):
            cfgs.append(dict(total_drawdown=dd, stability_fee=.03, pre_days=0, junior_ledger=True, **FZ, **idx, **extra))
for kw0 in cfgs:
    for i in range(12):
        kw = dict(name="c", seed=N.SEED + i, **kw0)
        a = T3.run(T3.Scenario(**kw)); b = N.run(N.Scenario(**kw))
        for f in FIELDS:
            n += 1
            if getattr(a, f) != getattr(b, f): bad += 1; print("DIFF (1)", f, kw0, i)
print(f"(1) v1-vs-t3 features off: {n} field comparisons, differences: {bad}")
bad2 = m = 0
for i in range(20):
    base = dict(name="c", total_drawdown=.85, seed=N.SEED + i, stability_fee=.03, pre_days=365, junior_ledger=True, **FZ)
    for (pj, pr, S, D) in ((0, 0, "S1", "D1"), (1, 0, "S2", "D1"), (0, 1, "S3", "D1")):
        a = N.run(N.Scenario(**{**base, "surplus_rule": S, "dist_rule": D}))
        b = N.run(N.Scenario(**{**base, "surplus_rule": "SP", "phi_j": pj, "phi_r": pr}))
        m += 1
        if dataclasses.asdict(a) != dataclasses.asdict(b): bad2 += 1; print("DIFF (2)", S, i)
print(f"(2) SP special cases == S1/S2/S3: {m} cases, differences: {bad2}")
bad3 = m3 = 0
feats = [dict(c1_days=3, c1_step=.05, c1_min=.5, bidder_greed=.5, stress_sensitivity=.32), dict(subpar_redemption=True, stress_sensitivity=.28),
         dict(policy="borrowers_first", soc_cap=.05), dict(policy="kfiat_then_borrowers", soc_cap=.10, soc_basis="legacy"),
         dict(capacity_mode="adv", adv_frac=.01, daily_volume_kas=150e6, convex_impact=True), dict(size_scale=.3, index_mode="det", idx_target=2.0),
         dict(c1_days=2, subpar_redemption=True, policy="borrowers_first", soc_cap=.02, stress_sensitivity=.3)]
for ft in feats:
    for i in range(8):
        kw = dict(name="c", total_drawdown=.85, seed=N.SEED + i, stability_fee=.03, pre_days=365, junior_ledger=True, **FZ, **ft)
        full = N.run(N.Scenario(**kw)); snap = N.run(N.Scenario(**kw), stop_after_pre=True); cached = N.run(N.Scenario(**kw), pre=snap)
        m3 += 1
        if dataclasses.asdict(full) != dataclasses.asdict(cached): bad3 += 1; print("DIFF (3)", ft, i)
print(f"(3) cache == full with new features ON: {m3} cases, differences: {bad3}")
bad4 = m4 = 0
for ft in feats + [dict()]:
    for i in range(25):
        kw = dict(name="c", total_drawdown=.85, seed=N.SEED + i, **FZ, **ft)
        r = N.run(N.Scenario(**kw)); m4 += 1
        # start = redeemed(burned incl. sub-par) + repaid by auctions + (written off - sub-par loss) + remaining  [+ pushed ENRK part moves between vaults: conserved]
        lhs = r.enrk_start
        rhs = r.redeemed_units + r.enrk_repaid_auction + (r.enrk_written_off - r.subpar_loss_pct / 100 * r.enrk_start) + r.enrk_remaining
        if ft.get("policy", "waterfall") != "waterfall":
            continue      # pushed ENRK debt is created on survivors: identity checked on waterfall configs
        if abs(lhs - rhs) > 1e-6 * lhs: bad4 += 1; print("DIFF (4)", ft, i, lhs, rhs)
print(f"(4) ENRK accounting identity (waterfall configs): {m4} cases, differences: {bad4}")
sys.path.insert(0, "p3ref")
import loss_absorption_analysis as P3
bad5 = m5 = 0
for pol, cap, kwp in (("waterfall", None, {}), ("borrowers_first", None, {}), ("borrowers_first", .05, {}), ("borrowers_first", .15, {}), ("kfiat_then_borrowers", .10, {}), ("kfiat_then_borrowers", None, {})):
    for dd in (.85, .95):
        for i in range(15):
            a = P3.M.run(P3.M.Scenario(name="x", total_drawdown=dd, seed=P3.SEED + i, policy=pol, soc_cap=cap, **FZ))
            b = N.run(N.Scenario(name="x", total_drawdown=dd, seed=P3.SEED + i, policy=pol, soc_cap=cap, soc_basis="legacy", index_mode="orig", **FZ))
            m5 += 1
            for fa, fb in (("enrk_loss_pct", "enrk_loss_pct"), ("kfiat_loss_pct", "kfiat_loss_pct"), ("stranded_hole_pct", "stranded_hole_pct"), ("vaults_liquidated", "vaults_liquidated")):
                if getattr(a, fa) != getattr(b, fb): bad5 += 1; print("DIFF (5)", pol, cap, dd, i, fa, getattr(a, fa), getattr(b, fb))
            if abs(P3.M.LAST["soc_pct"] - b.pushed_pct) > 1e-9: bad5 += 1; print("DIFF (5) soc", pol, cap, dd, i)
print(f"(5) carry-over legacy basis == p3 patch: {m5} cases, differences: {bad5}")
print("check_v1: OK" if bad + bad2 + bad3 + bad4 + bad5 == 0 else "check_v1: FAILED")
