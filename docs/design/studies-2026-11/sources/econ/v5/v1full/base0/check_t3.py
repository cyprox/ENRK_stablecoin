"""Why: prove the T3 index extension is a no-op when off (decision: owner brief 2026-11-10).
(a) check.py (original vs extended, defaults)  -> run separately.
(b) index_mode="flat" == ORIGINAL simulator run with IndexResponse elasticities 0 (peg == 1 for ever), 3 drawdowns x 2 configs x 40 paths.
(c) "proc" with vol 0, no jumps, rho 0 == flat ; "det" with target 1 == flat ; breaker modes == none when |I-1|<11% ; capacity "value" == "units" at I=1.
(d) pre-year cache (snapshot) == full run with the process on (proc, rho -0.5, breaker liq_latch), 10 paths.
(e) sanity: proc paths differ from flat; breaker trips when expected."""
import sys, dataclasses
sys.dont_write_bytecode = True
import stress_test_crash as O
import stress_fee as N
ORIG = [f.name for f in dataclasses.fields(O.Result)]
bad = n = 0
FZ = dict(auction_end_price=0.75, enable_redemption=True)
for frozen in (False, True):
    for dd in (0.5, 0.85, 0.95):
        for i in range(40):
            kw = dict(name="c", total_drawdown=dd, seed=O.SEED + i, **(FZ if frozen else {}))
            ref = O.run(O.Scenario(response=O.IndexResponse(0.0, 0.0, 0.0, 1.0), **kw))
            variants = {
                "flat": dict(index_mode="flat"),
                "proc0": dict(index_mode="proc", idx_vol=0.0, idx_jumps=False),
                "det1": dict(index_mode="det", idx_target=1.0),
                "flat+brk": dict(index_mode="flat", breaker="liq_latch"),
                "flat+cap": dict(index_mode="flat", capacity_mode="value"),
                "flat+pre": dict(index_mode="flat", pre_days=365),
            }
            for nm, v in variants.items():
                r = N.run(N.Scenario(**kw, **v))
                for f in ORIG:
                    n += 1
                    if getattr(ref, f) != getattr(r, f):
                        bad += 1; print("DIFF", nm, f, frozen, dd, i, getattr(ref, f), getattr(r, f))
print(f"(b,c) {n} field comparisons, differences: {bad}")
bad2 = m = 0
for i in range(10):
    kw = dict(name="c", total_drawdown=0.85, seed=N.SEED + i, stability_fee=0.03, pre_days=365, junior_ledger=True,
              index_mode="proc", idx_rho=-0.5, breaker="liq_latch", capacity_mode="value", **FZ)
    full = N.run(N.Scenario(**kw)); snap = N.run(N.Scenario(**kw), stop_after_pre=True)
    cached = N.run(N.Scenario(**kw), pre=snap); m += 1
    if dataclasses.asdict(full) != dataclasses.asdict(cached): bad2 += 1; print("DIFF cache", i)
print(f"(d) cache checks: {m}, differences: {bad2}")
# (d2) the run_t3.py snapshot (flat, units, stress .18, -85%/60d, share .30) reused for other scenarios == full run
bad3 = 0; k3 = 0
import t3_scen as T
for r in (0.0, 0.03):
    for i in range(4):
        snap = N.run(N.Scenario(name="g", total_drawdown=0.85, crash_days=60, seed=N.SEED + i, stability_fee=r, pre_days=365, junior_ledger=True,
                                index_mode="flat", kfiat_share=0.30, **FZ), stop_after_pre=True)
        for sc in ("p_rho-.5", "d85_x2", "N2_energy2_kas-50", "ep2024_kas-50_I+52", "orig85"):
            kw, dd, days, _ = T.SCEN[sc]
            for (brk, cap, st, s, S) in (("liq_latch", "value", 0.32, 0, "S3"), ("mb", "units", 0.25, 50, "S1")):
                base = dict(name="g", total_drawdown=dd, crash_days=days, seed=N.SEED + i, stability_fee=r, pre_days=365, junior_ledger=True,
                            breaker=brk, capacity_mode=cap, stress_sensitivity=st, kfiat_share=s / 100, surplus_rule=S, **FZ, **kw)
                full = N.run(N.Scenario(**base)); cached = N.run(N.Scenario(**base), pre=snap); k3 += 1
                if dataclasses.asdict(full) != dataclasses.asdict(cached): bad3 += 1; print("DIFF cache2", r, i, sc, brk)
print(f"(d2) shared-snapshot checks: {k3}, differences: {bad3}")
a = N.run(N.Scenario(name="x", total_drawdown=0.85, index_mode="proc", seed=N.SEED, **FZ))
b = N.run(N.Scenario(name="x", total_drawdown=0.85, index_mode="flat", seed=N.SEED, **FZ))
c = N.run(N.Scenario(name="x", total_drawdown=0.85, index_mode="det", idx_target=2.0, breaker="liq_latch", seed=N.SEED, **FZ))
print("(e) proc final peg", round(a.final_peg, 3), "flat", b.final_peg, "det2 breaker_days", c.breaker_days, "final", round(c.final_peg, 3))
ok = (bad + bad2 + bad3 == 0 and a.final_peg != 1.0 and c.breaker_days > 0)
print("check_t3: OK" if ok else "check_t3 FAILED")
