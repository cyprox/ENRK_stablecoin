"""Why: prove the extended simulator reproduces the original when new features are off (decision: owner brief 2026-11-10).
Checks: (1) stress_fee == stress_test_crash, all original fields, default+frozen configs, 50 paths x 3 drawdowns;
(2) r=0 with a 365-day pre period == original (calm year is a no-op);
(3) cached pre-crash snapshot == full run (r=3%, all D/S), and snapshot is independent of kFIAT share (to 1e-9, float summation order)."""
import sys, dataclasses
sys.dont_write_bytecode = True
import stress_test_crash as O
import stress_fee as N

ORIG = [f.name for f in dataclasses.fields(O.Result)]
bad = 0
n = 0
for frozen in (False, True):
    for dd in (0.5, 0.85, 0.95):
        for i in range(50):
            kw = dict(name="c", total_drawdown=dd, seed=O.SEED + i)
            if frozen:
                kw.update(auction_end_price=0.75, enable_redemption=True)
            a = O.run(O.Scenario(**kw)); b = N.run(N.Scenario(**kw))
            c = N.run(N.Scenario(pre_days=365, **kw))
            for f in ORIG:
                n += 1
                if getattr(a, f) != getattr(b, f): bad += 1; print("DIFF off", f, frozen, dd, i)
                if getattr(a, f) != getattr(c, f): bad += 1; print("DIFF r0+pre", f, frozen, dd, i)
print(f"(1,2) original-vs-extended: {n} field comparisons x2, differences: {bad}")
FZ = dict(auction_end_price=0.75, enable_redemption=True)
bad2 = 0; m = 0
for D in ("D1", "D2", "D3"):
    for S in ("S1", "S2", "S3"):
        for i in range(10):
            kw = dict(name="c", total_drawdown=0.85, seed=N.SEED + i, stability_fee=0.03, pre_days=365,
                      junior_ledger=True, dist_rule=D, surplus_rule=S, **FZ)
            full = N.run(N.Scenario(**kw))
            snap = N.run(N.Scenario(**kw), stop_after_pre=True)
            snap2 = N.run(N.Scenario(**{**kw, "kfiat_share": 0.5}), stop_after_pre=True)
            cached = N.run(N.Scenario(**kw), pre=snap)
            m += 1
            if dataclasses.asdict(full) != dataclasses.asdict(cached): bad2 += 1; print("DIFF cache", D, S, i)
            if snap["vaults"] != snap2["vaults"] or any(abs(x-y) > 1e-9 * (1 + abs(x)) for x, y in zip(snap["fee_tl"] + snap["sur_tl"], snap2["fee_tl"] + snap2["sur_tl"])):
                bad2 += 1; print("DIFF snapshot depends on s", i)
print(f"(3) cache/snapshot checks: {m}, differences: {bad2}")
# (4) ECON-T1: SP rule special cases equal the M2 rules: SP(0,0)==S1, SP(1,0)==S2 (D1), SP(0,1)==S3, at r=3%, s=30%.
bad3 = 0; m3 = 0
FIELDS_T = [f.name for f in dataclasses.fields(N.Result) if f.name != "open_coll_pct"]
for (pj, pr, ref) in ((0.0, 0.0, "S1"), (1.0, 0.0, "S2"), (0.0, 1.0, "S3")):
    for i in range(20):
        kw = dict(name="c", total_drawdown=0.85, seed=N.SEED + i, stability_fee=0.03, pre_days=365, junior_ledger=True, dist_rule="D1", **FZ)
        a = N.run(N.Scenario(surplus_rule=ref, **kw)); b = N.run(N.Scenario(surplus_rule="SP", phi_j=pj, phi_r=pr, **kw))
        m3 += 1
        if any(getattr(a, f) != getattr(b, f) for f in FIELDS_T): bad3 += 1; print("DIFF SP", pj, pr, i)
print(f"(4) SP special cases vs S1/S2/S3: {m3}, differences: {bad3}")
print("check: OK" if bad + bad2 + bad3 == 0 else "check FAILED")
