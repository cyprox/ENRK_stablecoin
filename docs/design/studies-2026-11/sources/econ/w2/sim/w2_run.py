"""Why: Monte Carlo runner for ECON-W2 (paired paths: path i = SEED+i in every cell; calm pre-year cached per (fee, speculator set, size)) (decision: owner approval of plan 2026-11-13).
Usage: python3 -I -B w2_run.py --exp HL --out HL.pkl [--paths 500] [--procs 3]   (never more than 3 processes)"""
import argparse, sys, os, pickle
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from multiprocessing import Pool
import stress_fee as N
import w2_exp as E
FIELDS = ("enrk_loss_pct", "kfiat_loss_pct", "stranded_hole_pct", "junior_inc_pct", "junior_inc_pre_pct", "junior_hold_pct",
          "unbacked_usd_pct", "unbacked_units_pct", "final_peg", "peg_max", "vaults_liquidated", "liquidated_pre", "final_kas_ratio",
          "surplus_pct", "reserve_used_pct", "redeemed_pct", "freeze_days", "latent_max_pct", "pushed_pct", "fee_paid_pct", "debt_units_start",
          "reserve_end_pct", "rb_topup_pct", "rb_exit_cash_pct", "rb_exit_sell_pct", "rb_dump_adv", "rb_run_red_pct", "rb_sig_max", "rb_acted_vaults",
          "redemption_blocked_pct", "stranded_vaults", "debt_units_end_alive", "enrk_start")
A = {}
def init(exp):
    A["cells"] = E.EXPS[exp]()
def task(i):
    snaps = {}; out = {}
    for key, kw in A["cells"]:
        sk = (kw["stability_fee"], kw.get("rb_spec_frac", 0.0), kw.get("rb_spec_icr", 1.7) if kw.get("rb_spec_frac", 0.0) > 0 else 0.0, kw.get("size_scale", 1.0))
        if sk not in snaps:
            snaps[sk] = N.run(N.Scenario(name="g", total_drawdown=.85, crash_days=60, seed=N.SEED + i, stability_fee=sk[0], pre_days=365, junior_ledger=True,
                                         kfiat_share=.30, index_mode="flat", auction_end_price=.75, enable_redemption=False,
                                         rb_spec_frac=sk[1], rb_spec_icr=kw.get("rb_spec_icr", 1.7), size_scale=sk[3]), stop_after_pre=True)
        base = dict(name="g", seed=N.SEED + i, pre_days=365, junior_ledger=True, **kw)
        res = N.run(N.Scenario(**base), pre=snaps[sk])
        out[key] = [getattr(res, f) for f in FIELDS]
    return i, out
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--exp", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--paths", type=int, default=500); ap.add_argument("--procs", type=int, default=3)
    a = ap.parse_args(); arrs = {}
    with Pool(min(a.procs, 3), initializer=init, initargs=(a.exp,)) as pool:
        for i, out in pool.imap_unordered(task, range(a.paths), chunksize=2):
            for k, v in out.items():
                if k not in arrs: arrs[k] = np.full((a.paths, len(FIELDS)), np.nan)
                arrs[k][i] = v
    pickle.dump({"fields": FIELDS, "paths": a.paths, "exp": a.exp, "data": arrs}, open(a.out, "wb"))
    print("wrote", a.out, len(arrs), "cells x", a.paths, "paths")
