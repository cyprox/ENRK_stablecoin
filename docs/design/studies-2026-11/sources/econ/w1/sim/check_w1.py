"""Why: prove the ECON-W1 extensions (index_mode "path", idx_max_up_step) are inert when OFF and consistent when ON (decision: owner brief 2026-11-11, validation required).
(1) W1 simulator == ECON-V1 simulator (v1ref/stress_fee.py) on every Result field, features off; (2) path mode with the det ramp values == det mode;
(3) path of ones == flat; (4) up-limit very large == off; up-limit .0025 on a x2 ramp: published peg_max == 1.0025**60 exactly; (5) cached pre-year == full run in path + up-limit modes."""
import sys, dataclasses, importlib.util, math
sys.dont_write_bytecode = True
import stress_fee as N
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m
V1 = load("v1sim", "v1ref/stress_fee.py")
FIELDS = [f.name for f in dataclasses.fields(V1.Result)]
FZ = dict(auction_end_price=0.75, enable_redemption=True)
bad = n = 0
def cmp(a, b, tag, fields=FIELDS):
    global bad, n
    for f in fields:
        n += 1
        x, y = getattr(a, f), getattr(b, f)
        if x != y and not (x != x and y != y): bad += 1; print("DIFF", tag, f, x, y)
# (1)
for idx in (dict(index_mode="orig"), dict(index_mode="flat"), dict(index_mode="proc", idx_vol=.3, idx_rho=-.5), dict(index_mode="det", idx_target=2.0)):
    for extra in (dict(), dict(policy="kfiat_then_borrowers", soc_cap=.05), dict(c1_days=3, subpar_redemption=True), dict(surplus_rule="S3", kfiat_share=.5)):
        for dd in (.7, .85):
            for i in range(6):
                kw = dict(name="c", seed=N.SEED + i, total_drawdown=dd, stability_fee=.03, pre_days=0, junior_ledger=True, **FZ, **{"kfiat_share": .3, **idx, **extra})
                cmp(N.run(N.Scenario(**kw)), V1.run(V1.Scenario(**kw)), f"(1){idx}{extra}{dd}{i}")
print("(1) W1 off == V1:", n, "field comparisons, differences:", bad)
# (2) (3)
b0, n0 = bad, n
for tgt in (1.5, 2.0, 0.6):
    path = tuple(tgt ** ((c + 1) / 60) for c in range(60))
    for i in range(10):
        kw = dict(name="c", seed=N.SEED + i, total_drawdown=.85, stability_fee=.03, pre_days=0, junior_ledger=True, kfiat_share=.3, **FZ)
        cmp(N.run(N.Scenario(index_mode="det", idx_target=tgt, **kw)), N.run(N.Scenario(index_mode="path", idx_path=path, **kw)), f"(2){tgt}{i}")
for i in range(10):
    kw = dict(name="c", seed=N.SEED + i, total_drawdown=.85, stability_fee=.03, pre_days=0, junior_ledger=True, kfiat_share=.3, **FZ)
    cmp(N.run(N.Scenario(index_mode="flat", **kw)), N.run(N.Scenario(index_mode="path", idx_path=(1.0,) * 60, **kw)), f"(3){i}")
print("(2)(3) path==det, path(1)==flat:", n - n0, "comparisons, differences:", bad - b0)
# (4)
b0, n0 = bad, n
for i in range(10):
    kw = dict(name="c", seed=N.SEED + i, total_drawdown=.85, stability_fee=.03, pre_days=0, junior_ledger=True, kfiat_share=.3, **FZ)
    for ix in (dict(index_mode="det", idx_target=2.0), dict(index_mode="proc", idx_vol=.3)):
        cmp(N.run(N.Scenario(**ix, **kw)), N.run(N.Scenario(**ix, idx_max_up_step=10.0, **kw)), f"(4a){ix}{i}")
    r = N.run(N.Scenario(index_mode="det", idx_target=2.0, idx_max_up_step=.0025, **kw)); n += 1
    if abs(r.peg_max - 1.0025 ** 60) > 1e-12: bad += 1; print("DIFF (4b)", r.peg_max, 1.0025 ** 60)
    r = N.run(N.Scenario(index_mode="det", idx_target=0.6, idx_max_up_step=.0025, **kw)); n += 1     # falling index: not limited
    r0 = N.run(N.Scenario(index_mode="det", idx_target=0.6, **kw))
    cmp(r, r0, f"(4c){i}")
print("(4) up-limit off/large inert, binds exactly, falls unlimited:", n - n0, "comparisons, differences:", bad - b0)
# (5)
b0, n0 = bad, n
for i in range(8):
    base = dict(name="c", seed=N.SEED + i, total_drawdown=.85, crash_days=60, stability_fee=.03, pre_days=365, junior_ledger=True, kfiat_share=.3, **FZ)
    snap = N.run(N.Scenario(**{**base, "index_mode": "flat"}), stop_after_pre=True)
    path = tuple(math.exp(0.1 * math.sin(c / 7.0) + 0.002 * c) for c in range(60))
    for ix in (dict(index_mode="path", idx_path=path), dict(index_mode="path", idx_path=path, idx_max_up_step=.0025), dict(index_mode="proc", idx_vol=.22, idx_max_up_step=.0025)):
        for extra in (dict(), dict(surplus_rule="S3", c1_days=3, subpar_redemption=True)):
            cmp(N.run(N.Scenario(**base, **ix, **extra)), N.run(N.Scenario(**base, **ix, **extra), pre=snap), f"(5){ix.get('index_mode')}{i}")
print("(5) cached pre-year == full run:", n - n0, "comparisons, differences:", bad - b0)
print("check_w1:", "OK" if bad == 0 else "FAIL", "total comparisons", n, "differences", bad)
