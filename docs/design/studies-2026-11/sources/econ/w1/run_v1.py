"""Why: Monte Carlo runner for ECON-V1 (paired paths, cached calm pre-year per (r, size_scale, capacity)), owner brief 2026-11-11.
Usage: python3 -B run_v1.py --exp E1 --out E1.pkl [--paths 500] [--procs 3]"""
import argparse, sys, pickle
import numpy as np
from multiprocessing import Pool
sys.dont_write_bytecode = True
import stress_fee as N
import v1_exp as X

FIELDS = ("enrk_loss_pct", "kfiat_loss_pct", "stranded_hole_pct", "junior_inc_pct", "junior_inc_pre_pct", "junior_hold_pct",
          "unbacked_usd_pct", "unbacked_units_pct", "final_peg", "vaults_liquidated", "liquidated_pre", "final_kas_ratio",
          "surplus_pct", "reserve_used_pct", "redeemed_pct", "freeze_days", "latent_max_pct", "pushed_pct", "deep_transfer_pct",
          "subpar_loss_pct", "subpar_redeemed_pct", "discount_cost_pct", "fee_paid_pct", "stranded_vaults", "auctions_expired",
          "debt_units_start", "redemption_blocked_pct", "reserve_end_pct")
A = {}
FROZEN = X.FROZEN

def init(exp):
    A["cells"] = X.EXPS[exp]()

def task(i):
    snaps = {}
    out = {}
    for key, kw in A["cells"]:
        r = kw["stability_fee"]; scl = kw.get("size_scale", 1.0); capd = kw.get("daily_liquidation_capacity", 0.05)
        sk = (r, scl, capd)
        if sk not in snaps:
            snaps[sk] = N.run(N.Scenario(name="g", total_drawdown=.85, crash_days=60, seed=N.SEED + i, stability_fee=r, pre_days=365,
                                         junior_ledger=True, kfiat_share=.30, index_mode="flat", size_scale=scl,
                                         daily_liquidation_capacity=capd, **FROZEN), stop_after_pre=True)
        res = N.run(N.Scenario(name="g", seed=N.SEED + i, pre_days=365, junior_ledger=True, **FROZEN, **kw), pre=snaps[sk])
        out[key] = [getattr(res, f) for f in FIELDS]
    return i, out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--paths", type=int, default=500); ap.add_argument("--procs", type=int, default=3)
    a = ap.parse_args()
    arrs = {}
    with Pool(min(a.procs, 3), initializer=init, initargs=(a.exp,)) as pool:
        for i, out in pool.imap_unordered(task, range(a.paths), chunksize=4):
            for k, v in out.items():
                if k not in arrs: arrs[k] = np.full((a.paths, len(FIELDS)), np.nan)
                arrs[k][i] = v
    pickle.dump({"fields": FIELDS, "paths": a.paths, "exp": a.exp, "data": arrs}, open(a.out, "wb"))
    print("wrote", a.out, len(arrs), "cells x", a.paths, "paths")
