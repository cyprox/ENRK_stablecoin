"""Independent re-run of v1 headline cells (own cell definitions from the report text), 500 paths, SEED+i. Usage: python3 -B my_cells.py OUT.pkl [paths]"""
import sys, pickle
sys.path.insert(0, "/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/v5/v1c")
sys.dont_write_bytecode = True
import numpy as np
from multiprocessing import Pool
import stress_fee as N
import v1_exp as X
FR = dict(auction_end_price=0.75, enable_redemption=True)
BASES = {"flat85": dict(total_drawdown=.85, crash_days=60, index_mode="flat"),
         "orig85": dict(total_drawdown=.85, crash_days=60, index_mode="orig"),
         "x2@85": dict(total_drawdown=.85, crash_days=60, index_mode="det", idx_target=2.0)}
ARCH = {"A0": dict(stability_fee=0., kfiat_share=0.), "A3": dict(stability_fee=.03, kfiat_share=.30, dist_rule="D1", surplus_rule="S1"),
        "A5": dict(stability_fee=.03, kfiat_share=.30, dist_rule="D1", surplus_rule="S3"),
        "A8": dict(stability_fee=.03, kfiat_share=.50, dist_rule="D1", surplus_rule="S1"),
        "A7": dict(stability_fee=.03, kfiat_share=.30, dist_rule="D1", surplus_rule="S1", **X.C1V["C1a_g0+C2"])}
CELLS = [(b, a) for b in ("flat85", "x2@85", "orig85") for a in ("A3", "A5", "A8")] + [("flat85", "A0"), ("flat85", "A7")]
F = ("enrk_loss_pct", "kfiat_loss_pct", "stranded_hole_pct", "junior_inc_pct", "unbacked_usd_pct", "freeze_days")
def task(i):
    snaps, out = {}, {}
    for b, a in CELLS:
        kw = {**BASES[b], **ARCH[a]}; r = kw["stability_fee"]
        if r not in snaps:
            snaps[r] = N.run(N.Scenario(name="g", total_drawdown=.85, crash_days=60, seed=N.SEED + i, stability_fee=r, pre_days=365,
                                        junior_ledger=True, kfiat_share=.30, index_mode="flat", **FR), stop_after_pre=True)
        res = N.run(N.Scenario(name="g", seed=N.SEED + i, pre_days=365, junior_ledger=True, **FR, **kw), pre=snaps[r])
        out[(b, a)] = [getattr(res, f) for f in F]
    return i, out
if __name__ == "__main__":
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    D = {c: np.zeros((n, len(F))) for c in CELLS}
    with Pool(3) as p:
        for i, o in p.imap_unordered(task, range(n), chunksize=4):
            for c, v in o.items(): D[c][i] = v
    pickle.dump(D, open(sys.argv[1], "wb"))
    for c in CELLS:
        d = D[c]; q = lambda x: float(np.quantile(x, .95, method="higher"))
        print(c, "ENRKp95 %.1f kFIATmean %.1f unbacked %.2f junior_net %.1f latent95 %.1f" % (q(d[:,0]), d[:,1].mean(), d[:,4].mean(), (d[:,3]-d[:,1]).mean(), q(d[:,2])))
