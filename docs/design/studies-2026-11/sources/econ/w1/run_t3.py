"""Why: Monte Carlo runner for ECON-T3 (index dynamics in the crash), owner brief 2026-11-10.
Paths SEED+i, identical in every cell (paired). Frozen M2 crash config (floor 75%, redemption on, ICR 200%, 1000 vaults, D1).
Pre-crash year simulated once per (r, path) and cached (index process is OFF in the pre-year: idx_in_pre False).
Usage: python3 -B run_t3.py --kind main|cap|sstar --out X.npz [--paths 500] [--procs 8]"""
import argparse, sys, pickle
import numpy as np
from multiprocessing import Pool
sys.dont_write_bytecode = True
import stress_fee as N
import t3_scen as T

FIELDS = ("enrk_loss_pct", "kfiat_loss_pct", "stranded_hole_pct", "junior_inc_pct", "junior_inc_pre_pct", "junior_hold_pct",
          "unbacked_usd_pct", "unbacked_units_pct", "final_peg", "peg_max", "peg_min", "breaker_days", "vaults_liquidated",
          "liquidated_pre", "final_kas_ratio", "surplus_pct", "reserve_used_pct", "redeemed_pct")
FROZEN = dict(auction_end_price=0.75, enable_redemption=True)
A = {}

def init(kind):
    A["kind"] = kind; A["combos"] = T.combos(kind); A["cg"] = T.cellgrid(kind)

def task(arg):
    r, i = arg
    cg = [c for c in A["cg"] if c[0] == r]
    out = {}
    snaps = {}
    for sc, brk, cap, st in A["combos"]:
        kw, dd, days, _ = T.SCEN[sc]
        base = dict(name="g", total_drawdown=dd, crash_days=days, seed=N.SEED + i, stability_fee=r, pre_days=365,
                    junior_ledger=True, breaker=brk, capacity_mode=cap, stress_sensitivity=st, **FROZEN, **kw)
        if "snap" not in snaps:
            snaps["snap"] = N.run(N.Scenario(**{**base, "kfiat_share": 0.30, "index_mode": "flat", "breaker": "none",
                                                "capacity_mode": "units", "stress_sensitivity": 0.18,
                                                "total_drawdown": 0.85, "crash_days": 60}), stop_after_pre=True)
        for (rr, s, S) in cg:
            res = N.run(N.Scenario(**{**base, "kfiat_share": s / 100.0, "dist_rule": "D1", "surplus_rule": S}), pre=snaps["snap"])
            out[(sc, brk, cap, st, rr, s, S)] = [getattr(res, f) for f in FIELDS]
    return i, out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--paths", type=int, default=500); ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    cg = T.cellgrid(a.kind); rs = sorted({c[0] for c in cg})
    jobs = [(r, i) for r in rs for i in range(a.paths)]
    arrs = {}
    with Pool(a.procs, initializer=init, initargs=(a.kind,)) as pool:
        for i, out in pool.imap_unordered(task, jobs, chunksize=2):
            for k, v in out.items():
                if k not in arrs: arrs[k] = np.full((a.paths, len(FIELDS)), np.nan, dtype=np.float64)
                arrs[k][i] = v
    pickle.dump({"fields": FIELDS, "paths": a.paths, "kind": a.kind, "data": arrs}, open(a.out, "wb"))
    print("wrote", a.out, len(arrs), "cells x", a.paths, "paths")
