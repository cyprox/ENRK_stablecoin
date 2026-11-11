"""Why: statistics and equilibrium solver for the ECON-M2 grid (owner brief 2026-11-10).
Usage: python3 -B analyze.py grid_main.pkl cells.csv      -> cells.csv + printed tables"""
import pickle, random, sys, csv, statistics as st

def q(xs, p):
    xs = sorted(xs); return xs[min(int(len(xs) * p), len(xs) - 1)]

def load(p):
    d = pickle.load(open(p, "rb")); F = {f: j for j, f in enumerate(d["fields"])}
    return d, F

def col(d, F, cell, f): return [row[F[f]] for row in d["data"][cell]]

def boot_idx(n, B=500, seed=7):
    rg = random.Random(seed); return [[rg.randrange(n) for _ in range(n)] for _ in range(B)]

def ci(xs, p, idx):
    v = sorted(q([xs[i] for i in b], p) for b in idx)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v))]

def mean_ci(xs, idx):
    v = sorted(sum(xs[i] for i in b) / len(b) for b in idx)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v))]

def cell_stats(d, F, cell, idx, deep=True):
    r, s, D, S = cell
    en, kf, la = (col(d, F, cell, f) for f in ("enrk_loss_pct", "kfiat_loss_pct", "stranded_hole_pct"))
    o = dict(enrk50=q(en, .5), enrk95=q(en, .95), enrk99=q(en, .99), kf50=q(kf, .5), kfm=sum(kf) / len(kf),
             kf95=q(kf, .95), la95=q(la, .95))
    if deep:
        o["enrk95ci"] = ci(en, .95, idx); o["kf95ci"] = ci(kf, .95, idx); o["la95ci"] = ci(la, .95, idx)
    inc = col(d, F, cell, "junior_inc_pct"); incp = col(d, F, cell, "junior_inc_pre_pct"); hold = col(d, F, cell, "junior_hold_pct")
    if s > 0:
        net = [a - b for a, b in zip(inc, kf)]; neth = [a - b for a, b in zip(hold, kf)]
        o.update(net5=q(net, .05), net50=q(net, .5), net95=q(net, .95), netm=sum(net) / len(net),
                 p50loss=sum(1 for x in net if x < -50) / len(net), pg50=sum(1 for x in kf if x > 50) / len(kf),
                 calm=sum(incp) / len(incp), netholdm=sum(neth) / len(neth), incm=sum(inc) / len(inc))
        if deep:
            o["net5ci"] = ci(net, .05, idx); o["netmci"] = mean_ci(net, idx)
    o["liqpre"] = sum(col(d, F, cell, "liquidated_pre")) / d["paths"]
    o["liq"] = sum(col(d, F, cell, "vaults_liquidated")) / d["paths"]
    o["fee"] = sum(col(d, F, cell, "fee_paid_pct")) / d["paths"]
    o["feepre"] = sum(col(d, F, cell, "fee_paid_pre_pct")) / d["paths"]
    o["sur"] = sum(col(d, F, cell, "surplus_pct")) / d["paths"]
    o["surpre"] = sum(col(d, F, cell, "surplus_pre_pct")) / d["paths"]
    o["resend"] = sum(col(d, F, cell, "reserve_end_pct")) / d["paths"]
    o["resused"] = sum(col(d, F, cell, "reserve_used_pct")) / d["paths"]
    return o

def paired_diff(d, F, c1, c0, f, idx):
    a = col(d, F, c1, f); b = col(d, F, c0, f); x = [u - v for u, v in zip(a, b)]
    return sum(x) / len(x), mean_ci(x, idx)

def Ew(o, w): return (1 - w) * o["calm"] + w * o["netm"]

def equilibrium(E, ss, h):
    """E: dict s->value for s in ss (ascending, all >0). Return (label, s*)."""
    pts = [(s, E[s]) for s in ss]
    if pts[0][1] < h: return "none (E<h at s=%d)" % pts[0][0]
    for (s0, e0), (s1, e1) in zip(pts, pts[1:]):
        if e0 >= h > e1: return "%.0f" % (s0 + (s1 - s0) * (e0 - h) / (e0 - e1))
    return ">=%d (E>=h on all s)" % pts[-1][0]

if __name__ == "__main__":
    d, F = load(sys.argv[1]); n = d["paths"]; idx = boot_idx(n)
    rows = []
    cells = sorted(d["data"], key=lambda c: (c[0], c[1], c[2], c[3]))
    for c in cells:
        o = cell_stats(d, F, c, idx); rows.append((c, o))
    with open(sys.argv[2], "w", newline="") as fh:
        w = csv.writer(fh); keys = [k for k in max((o for _, o in rows), key=len) if not k.endswith("ci")] + ["enrk95lo", "enrk95hi", "kf95lo", "kf95hi", "la95lo", "la95hi"]
        w.writerow(["r", "s", "D", "S"] + keys)
        for c, o in rows:
            w.writerow([c[0], c[1], c[2], c[3]] + [round(o.get(k, float("nan")), 3) for k in keys[:-6]]
                       + [round(x, 2) for x in (*o["enrk95ci"], *o["kf95ci"], *o["la95ci"])])
    print("cells:", len(rows), "paths:", n)
