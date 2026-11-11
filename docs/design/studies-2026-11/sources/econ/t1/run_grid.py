"""Why: Monte Carlo grid for ECON-M2 (stability fee x junior share x distribution x surplus rule), owner brief 2026-11-10.
Frozen config of loss_absorption_analysis.py: floor 75%, redemption on (crash only), ICR 200%, 1000 vaults, -85%, 60-day crash, 365-day pre period.
Paths = SEED+i (same paths in every cell: paired / common random numbers). Per-path outputs are pickled.
Usage: python3 -B run_grid.py --out grid.pkl [--paths 500] [--rs 0,1,2,3,5] [--ss 0,15,30,50] [--Ds D1,D2,D3] [--Ss S1,S2,S3]
                              [--kw '{"impact_coefficient":0.04}'] [--drawdown 0.85] [--procs 8]"""
import argparse, json, pickle, sys
from multiprocessing import Pool
sys.dont_write_bytecode = True
import stress_fee as N

FIELDS = ("enrk_loss_pct", "kfiat_loss_pct", "stranded_hole_pct", "final_kas_ratio", "junior_inc_pre_pct",
          "junior_inc_pct", "junior_hold_pct", "liquidated_pre", "vaults_liquidated", "fee_paid_pct",
          "fee_paid_pre_pct", "surplus_pct", "surplus_pre_pct", "reserve_end_pct", "reserve_used_pct",
          "redeemed_pct", "discount_cost_pct")
FROZEN = dict(auction_end_price=0.75, enable_redemption=True)
A = {}

def task(arg):
    r, i = arg
    base = dict(name="g", total_drawdown=A["drawdown"], seed=N.SEED + i, stability_fee=r, pre_days=365,
                junior_ledger=True, **FROZEN, **A["kw"])
    snap = N.run(N.Scenario(**{**base, "kfiat_share": 0.30}), stop_after_pre=True)
    out = {}
    for s in A["ss"]:
        for D in A["Ds"]:
            for S in A["Ss"]:
                res = N.run(N.Scenario(**{**base, "kfiat_share": s / 100.0, "dist_rule": D, "surplus_rule": S}), pre=snap)
                out[(r, s, D, S)] = tuple(getattr(res, f) for f in FIELDS)
    return i, out

def init(a):
    A.update(a)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--paths", type=int, default=500)
    ap.add_argument("--rs", default="0,1,2,3,5")
    ap.add_argument("--ss", default="0,15,30,50")
    ap.add_argument("--Ds", default="D1,D2,D3")
    ap.add_argument("--Ss", default="S1,S2,S3")
    ap.add_argument("--kw", default="{}")
    ap.add_argument("--drawdown", type=float, default=0.85)
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    cfg = dict(ss=[int(x) for x in a.ss.split(",")], Ds=a.Ds.split(","), Ss=a.Ss.split(","),
               kw=json.loads(a.kw), drawdown=a.drawdown)
    rs = [float(x) / 100.0 for x in a.rs.split(",")]
    jobs = [(r, i) for r in rs for i in range(a.paths)]
    cells = {}
    with Pool(a.procs, initializer=init, initargs=(cfg,)) as pool:
        for i, out in pool.imap_unordered(task, jobs, chunksize=4):
            for k, v in out.items():
                cells.setdefault(k, {})[i] = v
    data = {k: [d[i] for i in range(a.paths)] for k, d in cells.items()}
    pickle.dump({"fields": FIELDS, "cfg": cfg, "paths": a.paths, "data": data}, open(a.out, "wb"))
    print("wrote", a.out, len(data), "cells x", a.paths, "paths")
