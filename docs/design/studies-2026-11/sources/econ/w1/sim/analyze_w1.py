"""Why: tables, paired statistics and bootstrap CIs for ECON-W1 (unit of account as a variable), owner question 2026-11-11.
Usage: python3 -B analyze_w1.py > tables_w1.txt   (reads WB.pkl, WC.pkl). Units: losses = % of OPENING tranche (peg units); unbacked = % of opening debt VALUE (USD at the loss-day index);
junior net = junior income - kFIAT write-off, % of kFIAT face, peg (unit) terms, cycle = 365 calm days + crash; holder USD return = final_peg*(1-ENRK loss)-1 (approximation: losses booked at the final index)."""
import sys, os, pickle, csv, math
import numpy as np
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "t2"))
def load(e):
    d = pickle.load(open(e + ".pkl", "rb")); d["F"] = {f: j for j, f in enumerate(d["fields"])}; return d
def col(d, k, f): return d["data"][k][:, d["F"][f]]
def pct(x, p): return float(np.quantile(x, p, method="higher"))
_I = {}
def bidx(n, B=500):
    if n not in _I: _I[n] = np.random.default_rng(7).integers(0, n, size=(B, n))
    return _I[n]
def cim(x): v = np.sort(x[bidx(len(x))].mean(axis=1)); return float(v[int(.025 * len(v))]), float(v[int(.975 * len(v))])
def ciq(x, p): B = x[bidx(len(x))]; v = np.sort(np.quantile(B, p, axis=1, method="higher")); return float(v[int(.025 * len(v))]), float(v[int(.975 * len(v))])
def S(d, k):
    en, kf, la, ub = (col(d, k, f) for f in ("enrk_loss_pct", "kfiat_loss_pct", "stranded_hole_pct", "unbacked_usd_pct"))
    fp = col(d, k, "final_peg")
    o = dict(en50=pct(en, .5), en95=pct(en, .95), en99=pct(en, .99), enm=en.mean(), kfm=kf.mean(), kf95=pct(kf, .95), la95=pct(la, .95), pla=float(np.mean(la > 1e-9)),
             lam=la.mean(), ubm=ub.mean(), fz=col(d, k, "freeze_days").mean(), peg=fp.mean(), pegsd=fp.std(), red=col(d, k, "redeemed_pct").mean(),
             hold=fp * (1 - en / 100) - 1, calm=col(d, k, "junior_inc_pre_pct").mean(), liqpre=col(d, k, "liquidated_pre").mean())
    net = col(d, k, "junior_inc_pct") - kf
    o["netm"] = net.mean(); o["net"] = net
    o["en"] = en; o["ub"] = ub; o["kf"] = kf
    return o
def f(x, n=1): return f"{x:.{n}f}"
def hd(h): print("\n" + h + "\n" + "=" * len(h))
def lab(u, m): return f"{u}|{m}"
rows = []
def main():
    WB = load("WB"); keys = list(WB["data"])
    scs = []
    for k in keys:
        if (k[0], k[1]) not in scs: scs.append((k[0], k[1]))
    hd("T1 (WB) KAS -85%/60d, A3 (r3 s30 S1): unit scenario -> ENRK p95 [CI] / p99 | kFIAT mean / p95 | latent p95 (share of paths with latent hole) | unbacked mean | junior net | final unit value mean (sd) | ENRK holder USD return mean / p5 / p95")
    base = S(WB, ("U1", "flat", 85, "A3"))
    for (u, m) in scs:
        k = (u, m, 85, "A3")
        if k not in WB["data"]: continue
        o = S(WB, k); c = ciq(o["en"], .95)
        h = o["hold"]
        print(f"{lab(u, m):16s} {f(o['en95'])} [{f(c[0])},{f(c[1])}] / {f(o['en99'])} | {f(o['kfm'])} / {f(o['kf95'])} | {f(o['la95'])} ({100*o['pla']:.1f}%) | {f(o['ubm'])} | {o['netm']:+.1f} | {o['peg']:.3f} ({o['pegsd']:.3f}) | {100*h.mean():+.1f}% / {100*np.percentile(h,5):+.1f}% / {100*np.percentile(h,95):+.1f}%")
    for depth in (85, 70):
        for a in ("A0", "A5", "A8", "STACK") if depth == 85 else ("A0", "A3", "A5", "A8", "STACK"):
            hd(f"T2 (WB) KAS -{depth}%, architecture {a}: ENRK p95 / p99 | kFIAT mean / p95 | latent p95 (P>0) | unbacked mean | junior net")
            for (u, m) in scs:
                k = (u, m, depth, a)
                if k not in WB["data"]: continue
                o = S(WB, k)
                print(f"{lab(u, m):16s} {f(o['en95'])} / {f(o['en99'])} | {f(o['kfm'])} / {f(o['kf95'])} | {f(o['la95'])} ({100*o['pla']:.1f}%) | {f(o['ubm'])} | {o['netm']:+.1f}")
    hd("T3 (WB) paired differences vs U1 (USD) per architecture, -85%: d(unbacked mean) [95% CI] ; d(ENRK p95) [CI];  '*' = CI excludes 0")
    for a in ("A0", "A3", "A5", "A8", "STACK"):
        print(f"\n[{a}]")
        b = S(WB, ("U1", "flat", 85, a))
        for (u, m) in scs:
            k = (u, m, 85, a)
            if k not in WB["data"] or u == "U1": continue
            o = S(WB, k); d = o["ub"] - b["ub"]; c = cim(d)
            B = bidx(len(d)); q = np.sort(np.quantile(o["en"][B], .95, axis=1, method="higher") - np.quantile(b["en"][B], .95, axis=1, method="higher"))
            print(f"{lab(u, m):16s} d_unb {d.mean():+6.2f} [{c[0]:+.2f},{c[1]:+.2f}]{'*' if c[0] > 0 or c[1] < 0 else ' '}   d_ENRKp95 {o['en95']-b['en95']:+6.1f} [{q[int(.025*len(q))]:+.1f},{q[int(.975*len(q))]:+.1f}]{'*' if q[int(.025*len(q))] > 0 or q[int(.975*len(q))] < 0 else ' '}")
    hd("T4 (WB) holder exposure A3 -85% (ENRK holder; unit terms = -ENRK loss; USD = final_peg*(1-loss)-1; kFIAT holder USD likewise): mean / p5 / p50 / p95 / P(USD loss>20%)")
    for (u, m) in scs:
        k = (u, m, 85, "A3")
        if k not in WB["data"]: continue
        o = S(WB, k); en = o["en"]; fp = col(WB, k, "final_peg"); kf = o["kf"]; hk = fp * (1 - kf / 100) - 1; h = o["hold"]
        print(f"{lab(u, m):16s} ENRK unit {-en.mean():+.1f}% / {-pct(en,.95):+.1f}% p5 | USD {100*h.mean():+.1f}% / {100*np.percentile(h,5):+.1f}% / {100*np.percentile(h,50):+.1f}% / {100*np.percentile(h,95):+.1f}% | P(loss>20%) {100*np.mean(h<-.2):.1f}% || kFIAT USD {100*hk.mean():+.1f}% / {100*np.percentile(hk,5):+.1f}% / {100*np.percentile(hk,50):+.1f}% / {100*np.percentile(hk,95):+.1f}%")
    # ---------------- WC
    if os.path.exists("WC.pkl"):
        WC = load("WC"); ks = list(WC["data"]); wsc = []
        for k in ks:
            if (k[0], k[1]) not in wsc: wsc.append((k[0], k[1]))
        import t2_demand as T2
        hd("T5 (WC) re-base, KAS -85%, D1/S1: per unit scenario, rows r, cols s=0/15/30/50: ENRK p95 / unbacked mean / junior net (cycle) / calm-year junior income; (* = SURVIVE label, ' = HOLD as in v1)")
        EW = {}
        for (u, m) in wsc:
            print(f"\n[{lab(u, m)}]")
            for r in (0.0, .01, .02, .03):
                cells = []
                for s in (0.0, .15, .30, .50):
                    k = (u, m, 85, f"r{r*100:g}_s{s*100:g}")
                    o = S(WC, k)
                    surv = o["en95"] <= 2 and o["la95"] <= 1 and o["ubm"] <= 3; hold = o["en95"] <= 5 and o["la95"] <= 1
                    nt = f"{o['netm']:+.0f}" if s > 0 else "n/a"
                    cells.append(f"{o['en95']:5.1f}/{o['ubm']:4.1f}/{nt:>4}/{o['calm']:4.1f}{'*' if surv else (chr(39) if hold else ' ')}")
                    EW[(u, m, r, s)] = (o["calm"], o["netm"])
                print(f"  r={r*100:g}%  " + "  ".join(cells))
        def Ew(u, m, r, s, w): c, n = EW[(u, m, r, s)]; return (1 - w) * c + w * n
        def equil(E, h):
            pts = [(15, E[15]), (30, E[30]), (50, E[50])]
            if pts[0][1] < h: return "none"
            for (s0, e0), (s1, e1) in zip(pts, pts[1:]):
                if e0 >= h > e1: return "%.0f" % (s0 + (s1 - s0) * (e0 - h) / (e0 - e1))
            return ">=50"
        hd("T6 (WC) voluntary equilibrium share s* (%), junior hurdle h = 5/10/20 % on E_w = (1-w) calm + w cycle-net, crash probability w = 5/10/20 %/yr (ASSUMED), interpolation on s in 15/30/50, D1/S1")
        for (u, m) in wsc:
            print(f"\n[{lab(u, m)}]")
            for r in (.01, .02, .03):
                parts = []
                for w in (.05, .10, .20):
                    parts.append(f"w{w*100:g}: " + " ".join(f"h{h}={equil({s*100: Ew(u,m,r,s,w) for s in (.15,.30,.50)} if False else {s: Ew(u,m,r,s/100,w) for s in (15,30,50)}, h)}" for h in (5, 10, 20)))
                print(f"  r={r*100:g}%  " + " | ".join(parts))
        hd("T7 (WC) T2 intersection: r_clear(h) = fee r at which a 30% voluntary junior has E_w(w=10%) = h; linear interpolation on r in 0..3, beyond 3 linear EXTRAPOLATION flagged (r>3 contains the 153% opening-ICR artefact). Demand D(r)/D(0), ICR 250, T=1, X=0 (t2 sets L8, L4, P) at min(r_clear,3)")
        sets = {k.split()[0]: v for k, v in T2.SETS.items()}
        hz = T2.horizon("T1")
        def Drel(Sx, r):
            d0 = T2.demand(Sx, 0, 250, 0, hz)[0]; return T2.demand(Sx, r * 100 / 100.0, 250, 0, hz)[0] / d0
        for (u, m) in wsc:
            E = [Ew(u, m, r, .30, .10) for r in (0.0, .01, .02, .03)]; out = []
            for h in (5, 10, 20):
                if E[0] >= h: rc = 0.0; tag = "0.0"
                else:
                    rc = None
                    for i in range(3):
                        if E[i] < h <= E[i + 1]: rc = 100 * (i * .01 + .01 * (h - E[i]) / (E[i + 1] - E[i])); break
                    if rc is None:
                        sl = (E[3] - E[2]) / 1.0
                        rc = 3.0 + ((h - E[3]) / sl if sl > 0 else float("inf")); tag = ">3 extrap %.1f" % rc if rc < 100 else "none (E_w falls with r)"
                    else: tag = f"{rc:.2f}"
                dd = ""
                if rc is not None and rc < 100:
                    rr = min(rc, 3.0); dd = " D/D0 L8 %.2f L4 %.2f P %.2f" % tuple(T2.demand(sets[s], rr, 250, 0, hz)[0] / T2.demand(sets[s], 0, 250, 0, hz)[0] for s in ("L8", "L4", "P"))
                out.append(f"h{h}: r_clear {tag}{dd}")
            print(f"{lab(u, m):16s} E_w(w=10%,s=30) at r=0/1/2/3: " + " / ".join(f"{e:+.1f}" for e in E) + " | " + " | ".join(out))
        hd("T8 (WC) redemption-off check, A3 (r3 s30): ENRK p95 / unbacked mean / kFIAT mean (redemption on in brackets)")
        for k in ks:
            if k[3].endswith("NOREDEMPTION"):
                o = S(WC, k); o2 = S(WC, (k[0], k[1], 85, "r3_s30")); print(f"{lab(k[0], k[1]):16s} {f(o['en95'])} / {f(o['ubm'])} / {f(o['kfm'])}   (on: {f(o2['en95'])} / {f(o2['ubm'])} / {f(o2['kfm'])})")
        hd("T9 (WC) opening-ICR artefact monitor: mean vaults liquidated in the calm year (of 1000), by r (unit-independent: the pre-year is at I=1)")
        k0 = wsc[0]
        for r in (0.0, .01, .02, .03): print(f"  r={r*100:g}%  liquidated_pre mean {S(WC, (k0[0], k0[1], 85, f'r{r*100:g}_s30'))['liqpre']:.2f}")
def wd():
    if not os.path.exists("WD.pkl"): return
    WD = load("WD"); WB = load("WB")
    hd("T10 (WD) replay of the worst historical 60-day window of each unit (2005-07..2026-11), KAS -85%: ENRK p95 / p99 | kFIAT mean / p95 | latent p95 | unbacked mean | junior net | (U1 reference in last line per arch)")
    for a in ("A0", "A3", "A5", "A8", "STACK"):
        o = S(WB, ("U1", "flat", 85, a)); print(f"\n[{a}] U1 reference: {f(o['en95'])} / {f(o['en99'])} | {f(o['kfm'])} / {f(o['kf95'])} | {f(o['la95'])} | {f(o['ubm'])} | {o['netm']:+.1f}")
        for k in WD["data"]:
            if k[3] != a: continue
            o = S(WD, k); print(f"  {k[0]:8s}{k[1]:7s} {f(o['en95'])} / {f(o['en99'])} | {f(o['kfm'])} / {f(o['kf95'])} | {f(o['la95'])} | {f(o['ubm'])} | {o['netm']:+.1f} | unit end {o['peg']:.3f}")
if __name__ == "__main__":
    main()
    wd()
