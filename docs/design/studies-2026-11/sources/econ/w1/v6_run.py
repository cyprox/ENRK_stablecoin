"""Why: Monte Carlo runner for ECON-V6 (paired paths: path i = SEED+i in every cell), owner brief 2026-11-11.
Usage: python3 -B v6_run.py --out v6.pkl [--paths 1000] [--procs 3] [--group all|base|brk|shape|kf]"""
import argparse, sys, pickle
import numpy as np
from multiprocessing import Pool
sys.dont_write_bytecode = True
import stress_fee as N
import v6_scen as V
import run_t3 as R
FIELDS = R.FIELDS + ("breaker_first_day", "kfiat_index_end", "kfiat_index_ratio_end", "kfiat_uncovered_pct", "auctions_filled", "mean_icr_end")
FROZEN = dict(auction_end_price=0.75, enable_redemption=True)
A = {}
def init(group):
    A["c"] = [c for c in V.combos() if group in ("all", c[1])]
def task(i):
    snaps = {}; out = {}
    for label, grp, sc, kw, cells in A["c"]:
        skw, dd, days, _ = V.SCEN[sc]
        for (r, s, S) in cells:
            if r not in snaps:
                snaps[r] = N.run(N.Scenario(name="g", total_drawdown=.85, crash_days=60, seed=N.SEED + i, stability_fee=r, pre_days=365, junior_ledger=True,
                                            kfiat_share=.30, index_mode="flat", stress_sensitivity=.18, **FROZEN), stop_after_pre=True)
            base = dict(name="g", total_drawdown=dd, crash_days=days, seed=N.SEED + i, stability_fee=r, pre_days=365, junior_ledger=True,
                        kfiat_share=s / 100.0, dist_rule="D1", surplus_rule=S, stress_sensitivity=.18, **FROZEN, **skw, **kw)
            res = N.run(N.Scenario(**base), pre=snaps[r])
            out[(label, r, s, S)] = [getattr(res, f) for f in FIELDS]
    return i, out
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--paths", type=int, default=1000)
    ap.add_argument("--procs", type=int, default=3); ap.add_argument("--group", default="all"); a = ap.parse_args()
    arrs = {}
    with Pool(a.procs, initializer=init, initargs=(a.group,)) as pool:
        for i, out in pool.imap_unordered(task, range(a.paths), chunksize=4):
            for k, v in out.items():
                if k not in arrs: arrs[k] = np.full((a.paths, len(FIELDS)), np.nan)
                arrs[k][i] = v
    pickle.dump({"fields": FIELDS, "paths": a.paths, "data": arrs}, open(a.out, "wb"))
    print("wrote", a.out, len(arrs), "cells x", a.paths, "paths")
