"""Why: statistics, borrower-side proxies and Pareto frontier for ECON-T1 (owner brief 2026-11-10).
Usage: python3 -B analyze_t1.py t1_main.pkl t1_cells.csv   (writes CSV; import for report_t1.py)
Quantile convention = sorted[int(n*p)] as in ECON-M2. Bootstrap 500 resamples of paths (paired cells share the index set)."""
import pickle, sys, csv
import numpy as np

WS = (0.05, 0.10, 0.20)

def load(p):
    """p = one pickle or several joined by commas (cells are merged; same paths)."""
    ds = [pickle.load(open(x, "rb")) for x in p.split(",")]; d = ds[0]; F = {f: j for j, f in enumerate(d["fields"])}
    d["A"] = {c: np.array(v) for x in ds for c, v in x["data"].items()}; d["F"] = F
    return d

def q(x, p):
    n = len(x); return np.sort(x)[min(int(n * p), n - 1)]

def bidx(n, B=500, seed=7):
    return np.random.default_rng(seed).integers(0, n, size=(B, n))

def qci(x, p, idx):
    n = x.shape[0]; v = np.sort(np.sort(x[idx], axis=1)[:, min(int(n * p), n - 1)])
    return v[int(.025 * len(v))], v[int(.975 * len(v))]

def mci(x, idx):
    v = np.sort(x[idx].mean(axis=1)); return v[int(.025 * len(v))], v[int(.975 * len(v))]

def col(d, c, f): return d["A"][c][:, d["F"][f]]

def stats(d, c, idx=None):
    r, s, pj, pr = c; g = lambda f: col(d, c, f)
    en, kf, la = g("enrk_loss_pct"), g("kfiat_loss_pct"), g("stranded_hole_pct")
    o = dict(r=r * 100, s=s, pj=pj, pr=pr, enrk50=q(en, .5), enrk95=q(en, .95), enrk99=q(en, .99),
             kfm=kf.mean(), kf95=q(kf, .95), la95=q(la, .95), lam=la.mean())
    sur = g("surplus_pct"); eq = g("open_coll_pct") - 100.0
    wh = (pj + pr) / 100.0
    o["sur_pct_debt"] = sur.mean()
    o["withheld_debt"] = wh * sur.mean()                       # % of opening debt
    o["withheld_eq"] = 100.0 * wh * sur.mean() / eq.mean()     # % of borrowers' opening equity
    o["equity_pct_debt"] = eq.mean()
    o["resend"] = g("reserve_end_pct").mean(); o["resused"] = g("reserve_used_pct").mean()
    # borrower whole-cycle (y=0) delta vs holding the KAS, % of opening debt: debt cancelled by collateral sale,
    # borrower keeps minted D (100) + returned surplus; holding = opening collateral value x realised KAS ratio.
    ret = (1 - wh) * sur
    delta = 100.0 + ret - g("open_coll_pct") * g("final_kas_ratio")
    o["bor_delta"] = delta.mean(); o["bor_ret"] = ret.mean(); o["hold_end"] = (g("open_coll_pct") * g("final_kas_ratio")).mean()
    for w in WS: o[f"cost{int(w*100)}"] = r * 100 + w * 100 * o["withheld_debt"] / 100.0 * 1.0  # %/yr: r + w*withheld(% debt)
    if s > 0:
        inc, incp = g("junior_inc_pct"), g("junior_inc_pre_pct")
        net = inc - kf
        o.update(netm=net.mean(), net5=q(net, .05), p50=(net < -50).mean(), calm=incp.mean(), incm=inc.mean())
        for w in WS: o[f"E{int(w*100)}"] = (1 - w) * incp.mean() + w * net.mean()
        if idx is not None:
            o["netm_lo"], o["netm_hi"] = mci(net, idx)
    if idx is not None:
        o["enrk95_lo"], o["enrk95_hi"] = qci(en, .95, idx); o["kf95_lo"], o["kf95_hi"] = qci(kf, .95, idx)
    return o

def paired(d, c1, c0, f, p, idx):
    """paired difference of statistic (mean if p is None else quantile p) c1-c0 with bootstrap CI."""
    a, b = col(d, c1, f), col(d, c0, f)
    if p is None:
        x = a - b; return x.mean(), mci(x, idx)
    n = len(a); k = min(int(n * p), n - 1)
    pt = q(a, p) - q(b, p)
    v = np.sort(np.sort(a[idx], axis=1)[:, k] - np.sort(b[idx], axis=1)[:, k])
    return pt, (v[int(.025 * len(v))], v[int(.975 * len(v))])

def all_stats(d, deep=True):
    idx = bidx(d["paths"]) if deep else None
    return {c: stats(d, c, idx) for c in sorted(d["A"])}

if __name__ == "__main__":
    d = load(sys.argv[1]); S = all_stats(d)
    keys = sorted({k for o in S.values() for k in o})
    keys = ["r", "s", "pj", "pr"] + [k for k in keys if k not in ("r", "s", "pj", "pr")]
    with open(sys.argv[2], "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(keys)
        for c, o in S.items(): w.writerow([round(o.get(k, float("nan")), 3) for k in keys])
    print("cells", len(S), "paths", d["paths"])
