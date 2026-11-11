"""Why: Monte Carlo grid for ECON-T1 (auction-surplus split phi_j/phi_r x r x junior share), owner brief 2026-11-10.
Frozen config (floor 75%, redemption in crash, ICR 200%, 1000 vaults, -85%, 365-day calm pre-period), D1 only.
Paths = SEED+i, identical in every cell (paired). Usage:
  python3 -B run_t1.py --out t1_main.pkl [--paths 500] [--rs 0,1,2,3,5] [--ss 0,15,30,50] [--pairs full|head|zero] [--kw JSON] [--procs 8]"""
import argparse, json, pickle, sys
from multiprocessing import Pool
sys.dont_write_bytecode = True
import stress_fee as N

FIELDS = ("enrk_loss_pct", "kfiat_loss_pct", "stranded_hole_pct", "final_kas_ratio", "junior_inc_pre_pct",
          "junior_inc_pct", "junior_hold_pct", "liquidated_pre", "vaults_liquidated", "fee_paid_pct",
          "fee_paid_pre_pct", "surplus_pct", "surplus_pre_pct", "reserve_end_pct", "reserve_used_pct",
          "redeemed_pct", "discount_cost_pct", "open_coll_pct")
FROZEN = dict(auction_end_price=0.75, enable_redemption=True)
VALS = (0, 10, 25, 50, 75, 100)
FULL = [(j, r) for j in VALS for r in VALS if j + r <= 100]
HEAD = [(0, 0), (25, 0), (50, 0), (100, 0), (0, 25), (0, 50), (0, 100), (10, 10), (25, 25), (50, 50), (50, 25), (25, 50)]
A = {}

def task(arg):
    r, i = arg
    base = dict(name="t", total_drawdown=0.85, seed=N.SEED + i, stability_fee=r, pre_days=365,
                junior_ledger=True, dist_rule="D1", surplus_rule="SP", **FROZEN, **A["kw"])
    snap = N.run(N.Scenario(**{**base, "kfiat_share": 0.30}), stop_after_pre=True)
    out = {}
    for s in A["ss"]:
        for pj, pr in A["pairs"]:
            res = N.run(N.Scenario(**{**base, "kfiat_share": s / 100.0, "phi_j": pj / 100.0, "phi_r": pr / 100.0}), pre=snap)
            out[(r, s, pj, pr)] = tuple(getattr(res, f) for f in FIELDS)
    return i, out

def init(a): A.update(a)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--paths", type=int, default=500)
    ap.add_argument("--rs", default="0,1,2,3,5"); ap.add_argument("--ss", default="0,15,30,50")
    ap.add_argument("--pairs", default="full"); ap.add_argument("--kw", default="{}"); ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    cfg = dict(ss=[int(x) for x in a.ss.split(",")], pairs={"full": FULL, "head": HEAD, "zero": [(0, 0)]}[a.pairs], kw=json.loads(a.kw))
    rs = [float(x) / 100.0 for x in a.rs.split(",")]
    jobs = [(r, i) for r in rs for i in range(a.paths)]
    cells = {}
    with Pool(a.procs, initializer=init, initargs=(cfg,)) as pool:
        for i, out in pool.imap_unordered(task, jobs, chunksize=2):
            for k, v in out.items(): cells.setdefault(k, {})[i] = v
    data = {k: [d[i] for i in range(a.paths)] for k, d in cells.items()}
    pickle.dump({"fields": FIELDS, "cfg": cfg, "paths": a.paths, "data": data}, open(a.out, "wb"))
    print("wrote", a.out, len(data), "cells x", a.paths, "paths")
