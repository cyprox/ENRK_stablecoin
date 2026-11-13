"""Why: Monte Carlo runner for ECON-W1 (paired paths: path i = SEED+i in every cell; unit paths built from per-path RNGs shared across units), owner question 2026-11-11.
Usage: python3 -B w1_run.py --exp WB --out WB.pkl [--paths 500] [--procs 3]"""
import argparse, sys, pickle, math, random, json
import numpy as np
from multiprocessing import Pool
sys.dont_write_bytecode = True
import stress_fee as N
import w1_exp as E
FIELDS = ("enrk_loss_pct", "kfiat_loss_pct", "stranded_hole_pct", "junior_inc_pct", "junior_inc_pre_pct", "junior_hold_pct",
          "unbacked_usd_pct", "unbacked_units_pct", "final_peg", "peg_max", "peg_min", "vaults_liquidated",
          "liquidated_pre", "final_kas_ratio", "surplus_pct", "reserve_used_pct", "redeemed_pct", "freeze_days", "latent_max_pct", "pushed_pct", "deep_transfer_pct",
          "subpar_loss_pct", "subpar_redeemed_pct", "discount_cost_pct", "fee_paid_pct", "stranded_vaults", "auctions_expired",
          "debt_units_start", "redemption_blocked_pct", "reserve_end_pct")
A = {}
HIST = json.load(open("units_hist.json"))["hist"]
PAR = {"U2": "U2_CNY_FRED", "U3": "U3_basket", "U3b_eq": "U3b_USD_CNY_RUB_eq", "U3b_532": "U3b_USD50_CNY30_RUB20", "U4": "U4_elec", "U6": "U6_gold"}
BOOT = np.load("boot.npz")
H = 60
def init(exp):
    A["cells"] = E.EXPS[exp]()
def build_path(unit, mode, seed, days):
    """USD-value path of the unit over the crash days (relative to 1 at crash start). Same normals / same bootstrap start for every unit on a path (pairing)."""
    if mode in ("worst+", "worst-"):
        w = BOOT[unit]; k = int(w[:, -1].argmax() if mode == "worst+" else w[:, -1].argmin()); return tuple(float(x) for x in w[k][:days])
    if mode == "boot":
        k = random.Random(seed * 31 + 7).randrange(BOOT[unit].shape[0]); p = BOOT[unit][k]
        return tuple(float(x) for x in p[:days]) if days <= H else tuple(float(x) for x in p)
    rng = random.Random(seed * 7919 + 13); z = [rng.gauss(0.0, 1.0) for _ in range(days)]
    sig, mu = HIST[PAR[unit]]["vol"], HIST[PAR[unit]]["drift"]
    dt = 1.0 / 365.0; x = 0.0; out = []
    if unit == "U4":      # monthly publication: steps on crash days 9 and 39 (ASSUMED dates), monthly sd = vol/sqrt(12)
        for c in range(days):
            if c in (9, 39): x += (mu - 0.5 * sig * sig) / 12.0 + sig / math.sqrt(12.0) * z[0 if c == 9 else 1]
            out.append(x)
    else:
        for c in range(days):
            x += (mu - 0.5 * sig * sig) * dt + sig * math.sqrt(dt) * z[c]; out.append(x)
    if mode.startswith("s") and mode != "s0":
        f = math.log(1.0 + float(mode[1:]) / 100.0)
        out = [o + f * (c + 1) / days for c, o in enumerate(out)]
    elif mode.startswith("j"):
        f = math.log(1.0 + float(mode[1:]) / 100.0)
        out = [o + (f if c >= 5 else 0.0) for c, o in enumerate(out)]
    return tuple(math.exp(o) for o in out)
def task(i):
    snaps = {}; out = {}
    for key, c in A["cells"]:
        kw = dict(c["kw"]); r = kw["stability_fee"]; red = kw.get("enable_redemption", True)
        sk = (r, red)
        if sk not in snaps:
            snaps[sk] = N.run(N.Scenario(name="g", total_drawdown=.85, crash_days=60, seed=N.SEED + i, stability_fee=r, pre_days=365, junior_ledger=True,
                                         kfiat_share=.30, index_mode="flat", **{**E.FROZEN, "enable_redemption": red}), stop_after_pre=True)
        ukw = E.unit_kw(c["unit"], c["mode"])
        if ukw["index_mode"] == "path": ukw["idx_path"] = build_path(c["unit"], c["mode"], N.SEED + i, 60)
        base = dict(name="g", seed=N.SEED + i, pre_days=365, junior_ledger=True, total_drawdown=c["dd"], crash_days=60, **{**E.FROZEN, **kw}, **ukw)
        res = N.run(N.Scenario(**base), pre=snaps[sk])
        out[key] = [getattr(res, f) for f in FIELDS]
    return i, out
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--exp", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--paths", type=int, default=500); ap.add_argument("--procs", type=int, default=3); ap.add_argument("--only", default="")
    a = ap.parse_args(); arrs = {}
    with Pool(min(a.procs, 3), initializer=init, initargs=(a.exp,)) as pool:
        for i, out in pool.imap_unordered(task, range(a.paths), chunksize=2):
            for k, v in out.items():
                if k not in arrs: arrs[k] = np.full((a.paths, len(FIELDS)), np.nan)
                arrs[k][i] = v
    pickle.dump({"fields": FIELDS, "paths": a.paths, "exp": a.exp, "data": arrs}, open(a.out, "wb"))
    print("wrote", a.out, len(arrs), "cells x", a.paths, "paths")
