"""Why: tables, paired statistics and bootstrap CIs for ECON-V1 (owner brief 2026-11-11).
Usage: python3 -B analyze_v1.py [E6 E1 E2 E4 E5 E3 ...] > tables_v1.txt    (reads <exp>.pkl in cwd; writes cells_v1.csv)
Units: losses = % of OPENING tranche (peg units); unbacked_usd = % of opening debt VALUE; freeze_days = crash days (of 60/97) with >=1 under-water alive vault;
junior net = junior income at receipt (fees [+ surplus share]) minus kFIAT write-off, % of kFIAT face, peg units, cycle = 365 calm days + crash.
SURVIVE (my label, NOT a design threshold): ENRK p95 <= 2% AND latent p95 <= 1% AND unbacked mean <= 3%; HOLD (lenient): ENRK p95 <= 5% AND latent p95 <= 1%."""
import sys, os, pickle, csv
import numpy as np
import v1_exp as X

def load(e):
    p = e + ".pkl"
    if not os.path.exists(p): return None
    d = pickle.load(open(p, "rb")); d["F"] = {f: j for j, f in enumerate(d["fields"])}; return d
def col(d, k, f): return d["data"][k][:, d["F"][f]]
def pct(x, p): return float(np.quantile(x, p, method="higher"))
_IDX = {}
def bidx(n, B=500):
    if n not in _IDX: _IDX[n] = np.random.default_rng(7).integers(0, n, size=(B, n))
    return _IDX[n]
def ci_mean(x): v = np.sort(x[bidx(len(x))].mean(axis=1)); return float(v[int(.025 * len(v))]), float(v[int(.975 * len(v))])
def ci_q(x, p):
    B = x[bidx(len(x))]; v = np.sort(np.quantile(B, p, axis=1, method="higher")); return float(v[int(.025 * len(v))]), float(v[int(.975 * len(v))])
def f1(x, nd=1): return f"{x:.{nd}f}"
def fc(x, c, nd=1): return f"{x:.{nd}f} [{c[0]:.{nd}f},{c[1]:.{nd}f}]"

def S(d, k, ci=False):
    en, kf, la, ub = (col(d, k, f) for f in ("enrk_loss_pct", "kfiat_loss_pct", "stranded_hole_pct", "unbacked_usd_pct"))
    o = dict(en50=pct(en, .5), en95=pct(en, .95), en99=pct(en, .99), enm=en.mean(), kfm=kf.mean(), kf95=pct(kf, .95), la95=pct(la, .95),
             ubm=ub.mean(), fz=col(d, k, "freeze_days").mean(), fz95=pct(col(d, k, "freeze_days"), .95), lmax95=pct(col(d, k, "latent_max_pct"), .95),
             push=col(d, k, "pushed_pct").mean(), push95=pct(col(d, k, "pushed_pct"), .95), disc=col(d, k, "discount_cost_pct").mean(),
             deep=col(d, k, "deep_transfer_pct").mean(), spl=col(d, k, "subpar_loss_pct").mean(), spr=col(d, k, "subpar_redeemed_pct").mean(),
             red=col(d, k, "redeemed_pct").mean(), sur=col(d, k, "surplus_pct").mean(), ceil=None, ressum=col(d, k, "reserve_used_pct").mean())
    D0 = col(d, k, "debt_units_start").mean()
    o["D0"] = D0
    sh = share_of(k)
    if sh > 0:
        net = col(d, k, "junior_inc_pct") - kf
        o.update(netm=net.mean(), calm=col(d, k, "junior_inc_pre_pct").mean(), net5=pct(net, .05))
    else:
        o.update(netm=float("nan"), calm=float("nan"), net5=float("nan"))
    if ci:
        o["en95ci"] = ci_q(en, .95); o["ubci"] = ci_mean(ub)
        if sh > 0: o["netci"] = ci_mean(net)
    o["surv"] = o["en95"] <= 2 and o["la95"] <= 1 and o["ubm"] <= 3
    o["hold"] = o["en95"] <= 5 and o["la95"] <= 1
    return o

def share_of(k):
    nm = k[1]
    for t in nm.split("_"):
        if t.startswith("s") and t[1:].replace(".", "").isdigit(): return float(t[1:])
    return 0.0
def hd(h): print("\n" + h + "\n" + "=" * len(h))
FLAG = lambda o: "SURV" if o["surv"] else ("hold" if o["hold"] else "FAIL")
SC = X.SCEN8

def Ew(o, w): return (1 - w) * o["calm"] + w * o["netm"]
def equilibrium(E, ss, h):
    pts = [(s, E[s]) for s in ss]
    if pts[0][1] < h: return "none"
    for (s0, e0), (s1, e1) in zip(pts, pts[1:]):
        if e0 >= h > e1: return "%.0f" % (s0 + (s1 - s0) * (e0 - h) / (e0 - e1))
    return ">=%d" % pts[-1][0]

rows_csv = []
def csv_add(exp, d):
    for k in d["data"]:
        o = S(d, k); rows_csv.append([exp, k[0], k[1]] + [o[x] for x in ("en50", "en95", "en99", "kfm", "kf95", "la95", "ubm", "netm", "fz", "lmax95", "push", "disc", "deep", "spl")])

def t_e6(d):
    hd("T1 (E6) headline: architecture x adverse base, base parameters (stress .18, cap 5%/day, impact .08, ADV 40M), 500 paths")
    print("cell = ENRK p95 / p99 | kFIAT mean / p95 | latent p95 | unbacked mean | junior net mean || verdict (SURV/hold/FAIL)")
    archs = list(X.HEAD)
    for sc in SC:
        print(f"\n[{X.SHORT[sc]}]")
        for a in archs:
            o = S(d, (sc, a), ci=True)
            nt = f"{o['netm']:+.1f}" if o["netm"] == o["netm"] else "  n/a"
            print(f"  {a:<20} ENRK {f1(o['en95']):>5}/{f1(o['en99']):>5} [95%CI p95 {o['en95ci'][0]:.1f},{o['en95ci'][1]:.1f}] | kF {f1(o['kfm']):>5}/{f1(o['kf95']):>5} | lat95 {f1(o['la95']):>5} | unb {f1(o['ubm']):>5} | net {nt:>6} || {FLAG(o)}")
    hd("T1b survival matrix (E6)")
    print(f"{'architecture':<20}" + "".join(f"{X.SHORT[s]:>13}" for s in SC))
    for a in archs:
        print(f"{a:<20}" + "".join(f"{FLAG(S(d,(s,a))):>13}" for s in SC))

def t_e7(d):
    hd("T8 (E7) EXPLORATION: stacked levers (S3 reserve + C1a/C2 + capped carry-over + larger junior), 500 paths")
    for sc in SC:
        print(f"\n[{X.SHORT[sc]}]")
        for a in X.STACK:
            o = S(d, (sc, a), ci=True)
            nt = f"{o['netm']:+.1f}" if o["netm"] == o["netm"] else "  n/a"
            print(f"  {a:<26} ENRK {f1(o['en95']):>5}/{f1(o['en99']):>5} [p95 CI {o['en95ci'][0]:.1f},{o['en95ci'][1]:.1f}] | kF {f1(o['kfm']):>5}/{f1(o['kf95']):>5} | lat95 {f1(o['la95']):>5} | unb {f1(o['ubm']):>5} | net {nt:>6} | fz {o['fz']:.1f} || {FLAG(o)}")

def t_e1(d):
    ss = (.15, .30, .50)
    hd("T2 (E1) P1/P2: ENRK p95 (%) / unbacked mean (%) / junior net mean (% face), D1 S1, grid r x s, per base")
    for sc in SC:
        print(f"\n[{X.SHORT[sc]}]  rows r, cols s = 0 / 15 / 30 / 50 (mandatory share)")
        for r in (0.0, .01, .02, .03, .05):
            cells = []
            for s in (0.0, .15, .30, .50):
                o = S(d, (sc, f"r{r*100:g}_s{s*100:g}_D1_S1"))
                nt = f"{o['netm']:+.0f}" if o["netm"] == o["netm"] else "n/a"
                cells.append(f"{o['en95']:5.1f}/{o['ubm']:4.1f}/{nt:>4}{'*' if o['surv'] else (chr(39) if o['hold'] else ' ')}")
            print(f"  r={r*100:g}%  " + "  ".join(cells))
    print("  legend: * = SURVIVE, ' = HOLD (lenient) as defined in the header")
    hd("T2b (E1) voluntary equilibrium share s* (D1/S1; w = crash probability per year; hurdle h on E = (1-w) calm + w cycle-net; interpolation on s in 15/30/50)")
    for sc in SC:
        print(f"\n[{X.SHORT[sc]}]")
        for r in (.01, .02, .03, .05):
            E = {s: None for s in ss}; o = {s: S(d, (sc, f"r{r*100:g}_s{s*100:g}_D1_S1")) for s in ss}
            txt = []
            for w in (.05, .10, .20):
                for h in (.05, .10, .20):
                    if w != .10 and h != .10: continue
                    Ev = {s * 100: Ew(o[s], w) for s in ss}
                    txt.append(f"w{w*100:g}/h{h*100:g}: {equilibrium(Ev, (15, 30, 50), h*100)}")
            print(f"  r={r*100:g}%  " + "   ".join(txt) + "   | E_w(w=10%) at s=15/30/50: " + " / ".join(f"{Ew(o[s],.10):+.1f}" for s in ss))
        r = 0.0
        o = {s: S(d, (sc, f"r0_s{s*100:g}_D1_S1")) for s in ss}
        print(f"  r=0%  E_w(w=10%) at s=15/30/50: " + " / ".join(f"{Ew(o[s],.10):+.1f}" for s in ss))
    hd("T2c (E1) D1 / D2 / D3 at r=3% and r=5%: ENRK p95 / kFIAT mean / unbacked mean / junior net / reserve end(%debt unused)")
    for sc in SC:
        print(f"\n[{X.SHORT[sc]}]")
        for r in (.03, .05):
            for s in (0.0, .15, .30, .50):
                line = []
                for D in ("D1", "D2", "D3"):
                    o = S(d, (sc, f"r{r*100:g}_s{s*100:g}_{D}_S1"))
                    nt = f"{o['netm']:+.0f}" if o["netm"] == o["netm"] else "n/a"
                    line.append(f"{D}: {o['en95']:5.1f}/{o['kfm']:5.1f}/{o['ubm']:5.1f}/{nt:>4}")
                print(f"  r={r*100:g}% s={s*100:g}%  " + " | ".join(line))
    hd("T3 (E1) P5 surplus rule at r=0 / r=3, s=15/30/50: ENRK p95 / kFIAT mean / junior net.  S1 owner; S2 = junior(D1); S3 reserve; SP_0_x = x to reserve; phi_j analytic = net + phi_j*surplus/s")
    for sc in SC:
        print(f"\n[{X.SHORT[sc]}]")
        for r in (0.0, .03):
            for s in (.15, .30, .50):
                parts = []
                base = S(d, (sc, f"r{r*100:g}_s{s*100:g}_D1_S1"))
                parts.append(f"S1 {base['en95']:4.1f}/{base['kfm']:5.1f}/{base['netm']:+6.1f}")
                parts.append(f"S2 ({base['netm']+base['sur']/(s*100)*100:+.1f})")
                for pr in (.25, .5):
                    o = S(d, (sc, f"r{r*100:g}_s{s*100:g}_D1_SP_0_{pr}")); parts.append(f"rsv{int(pr*100)} {o['en95']:4.1f}/{o['kfm']:5.1f}/{o['netm']:+6.1f}")
                o = S(d, (sc, f"r{r*100:g}_s{s*100:g}_D1_S3")); parts.append(f"S3 {o['en95']:4.1f}/{o['kfm']:5.1f}/{o['netm']:+6.1f} (reserve used {o['ressum']:.1f}% debt)")
                print(f"  r={r*100:g}% s={s*100:g}%  " + " | ".join(parts))
    # linearity check of phi_j
    errs = []
    for sc in SC:
        a = S(d, (sc, "r3_s30_D1_S1")); b = S(d, (sc, "r3_s30_D1_S2")); c = S(d, (sc, "r3_s30_D1_SP_0.5_0.5")); e = S(d, (sc, "r3_s30_D1_SP_0_0.5"))
        errs.append((abs(b["netm"] - (a["netm"] + a["sur"] / 30 * 100 * 1.0)), abs(c["netm"] - (e["netm"] + 0.5 * a["sur"] / 30 * 100))))
    print("\n  phi_j linearity check (|S2 - analytic|, |SP(.5,.5) - analytic|), max over bases: %.2e, %.2e" % (max(x[0] for x in errs), max(x[1] for x in errs)))

def t_e2(d):
    hd("T4 (E2) P4 loss rule, architecture r=3% s=30% D1 S1 (and r=0 s=0 in the CSV), 500 paths. pushed = cumulative gross shortfall pushed to borrowers, % opening debt")
    print("cols: ENRK p95/p99 | kFIAT mean/p95 | latent p95 (day-end) | peak under-water hole p95 | freeze days mean | unbacked mean | pushed mean/p95")
    for arch_ in ("r3_s30", "r0_s0"):
        for sc in SC:
            print(f"\n[{X.SHORT[sc]}] {arch_}")
            for (pol, cap, basis, nm) in X.POLICIES:
                o = S(d, (sc, f"{arch_}_{nm}"))
                print(f"  {nm:<17} {o['en95']:5.1f}/{o['en99']:5.1f} | {o['kfm']:5.1f}/{o['kf95']:5.1f} | {o['la95']:5.1f} | {o['lmax95']:5.1f} | {o['fz']:5.1f} | {o['ubm']:5.1f} | {o['push']:5.1f}/{o['push95']:5.1f}")
    hd("T4b (E2) capacity sensitivity (daily capacity 2.5% / 10%), r=3% s=30%")
    for sc in ("flat85", "d85_x2"):
        for capd in (2.5, 10):
            print(f"\n[{X.SHORT[sc]}] capacity {capd}%/day")
            for nm in ("waterfall", "BF_uncapped", "BF_cap5", "KB_uncapped", "KB_cap5", "BF_cap5_LEGACY"):
                o = S(d, (sc, f"cap{capd:g}_r3_s30_{nm}"))
                print(f"  {nm:<17} {o['en95']:5.1f}/{o['en99']:5.1f} | {o['kfm']:5.1f}/{o['kf95']:5.1f} | {o['la95']:5.1f} | {o['lmax95']:5.1f} | {o['fz']:5.1f} | {o['ubm']:5.1f} | {o['push']:5.1f}/{o['push95']:5.1f}")

def t_e4(d):
    hd("T6 (E4) P14 unfreeze mechanisms, r=3% s=30%: C1 deepening floor (a: -5pts/3d to 50%; b: -10pts/2d to 40%), g = bidder greed, C2 sub-par redemption")
    print("cols: freeze days mean | latent p95 | peak hole p95 | unbacked mean | ENRK p95 | kFIAT mean | bidder discount cost mean | of which beyond-floor | sub-par ENRK loss | redeemed % ENRK")
    for sc in ("flat85", "d85_x2", "d70_x2", "ep2024_kas-50_I+52"):
        for st in (.18, .28, .32):
            for capd in (.05, .025):
                print(f"\n[{X.SHORT[sc]}] stress {st}, capacity {capd*100:g}%/day")
                for nm in X.C1V:
                    o = S(d, (sc, f"r3_s30_st{st}_cap{capd*100:g}_{nm}"))
                    print(f"  {nm:<11} fz {o['fz']:5.1f} | lat95 {o['la95']:5.1f} | peak95 {o['lmax95']:5.1f} | unb {o['ubm']:5.1f} | ENRK95 {o['en95']:5.1f} | kF {o['kfm']:5.1f} | disc {o['disc']:5.1f} | deep {o['deep']:4.2f} | subpar {o['spl']:4.2f} | red {o['red']:5.1f}")

def t_e5(d):
    hd("T7 (E5) sensitivity impact {.04,.08,.16} x capacity {2.5,5,10}%/day on headline architectures: ENRK p95 / unbacked mean   [S = SURVIVE, h = hold, . = fail]")
    for sc in ("flat85", "d85_x2", "ep2024_kas-50_I+52"):
        for a in X.HEAD:
            print(f"\n[{X.SHORT[sc]}] {a}   rows impact, cols capacity 2.5/5/10")
            for imp in (.04, .08, .16):
                cells = []
                for capd in (2.5, 5, 10):
                    o = S(d, (sc, f"{a}_imp{imp}_cap{capd:g}"))
                    cells.append(f"{o['en95']:5.1f}/{o['ubm']:5.1f}{'S' if o['surv'] else ('h' if o['hold'] else '.')}")
                print(f"  imp {imp:<4} " + "   ".join(cells))
    hd("T7b (E5) count of cells (of 9) that SURVIVE / hold per architecture and base")
    print(f"{'architecture':<20}" + "".join(f"{X.SHORT[s]:>14}" for s in ("flat85", "d85_x2", "ep2024_kas-50_I+52")))
    for a in X.HEAD:
        row = []
        for sc in ("flat85", "d85_x2", "ep2024_kas-50_I+52"):
            ns = nh = 0
            for imp in (.04, .08, .16):
                for capd in (2.5, 5, 10):
                    o = S(d, (sc, f"{a}_imp{imp}_cap{capd:g}")); ns += o["surv"]; nh += (o["hold"] and not o["surv"])
            row.append(f"{ns}S+{nh}h")
        print(f"{a:<20}" + "".join(f"{x:>14}" for x in row))

def t_e3(d):
    hd(f"T5 (E3) P13 debt ceiling: liquidator capital = adv_frac x ADV x price, convex impact; paths={d['paths']} (EXPLORATION if < 500)")
    print("ceiling = opening debt value / (ADV x price) in %; cols: ENRK p95/p99 | unbacked mean | freeze days | latent p95 | ok(SURV)")
    for sc in ("flat85", "d85_x2", "d70_x2", "ep2024_kas-50_I+52"):
        for (r, s) in ((.03, .30), (0.0, 0.0)):
            for adv in (70, 150, 230):
                for af in (.5, 1, 2):
                    line = []
                    for scale in (.05, .1, .2, .4, .7, 1.0, 1.5):
                        k = (sc, f"r{r*100:g}_s{s*100:g}_adv{adv:g}_sc{scale}_af{af:g}")
                        o = S(d, k); ceil = o["D0"] / (adv * 1e6 * 0.1) * 100
                        line.append(f"{ceil:5.1f}%:{o['en95']:4.1f}/{o['ubm']:4.1f}/{o['fz']:3.0f}/{o['la95']:3.0f}{'S' if o['surv'] else ('h' if o['hold'] else '.')}")
                    print(f"[{X.SHORT[sc]}] r{r*100:g}s{s*100:g} ADV{adv}M cap{af}%ADV/day  " + " ".join(line))
    hd("T5b (E3) as-coded reference (units capacity 5% of debt/day, ADV 40M, sqrt impact) at scales .1/.4/1.0")
    for sc in ("flat85", "d85_x2"):
        for (r, s) in ((.03, .30), (0.0, 0.0)):
            for scale in (.1, .4, 1.0):
                o = S(d, (sc, f"r{r*100:g}_s{s*100:g}_ASCODED_sc{scale}"))
                print(f"[{X.SHORT[sc]}] r{r*100:g}s{s*100:g} scale {scale}: debt {o['D0']*0.1/1e6:.2f}M-units  ENRK95 {o['en95']:.1f} unb {o['ubm']:.1f} fz {o['fz']:.0f} lat95 {o['la95']:.1f}")
    hd("T5c (E3) largest grid ceiling (% of ADV USD volume) that still SURVIVES, per (base, arch, ADV, capital)")
    for sc in ("flat85", "d85_x2", "d70_x2", "ep2024_kas-50_I+52"):
        for (r, s) in ((.03, .30), (0.0, 0.0)):
            for adv in (70, 150, 230):
                res = []
                for af in (.5, 1, 2):
                    best = None
                    for scale in (.05, .1, .2, .4, .7, 1.0, 1.5):
                        o = S(d, (sc, f"r{r*100:g}_s{s*100:g}_adv{adv:g}_sc{scale}_af{af:g}"))
                        if o["surv"]: best = o["D0"] / (adv * 1e6 * 0.1) * 100
                    res.append("none" if best is None else f"{best:.1f}%")
                print(f"[{X.SHORT[sc]}] r{r*100:g}s{s*100:g} ADV{adv}M capital .5/1/2 %ADV/day -> " + " / ".join(res))

if __name__ == "__main__":
    which = sys.argv[1:] or ["E6", "E1", "E2", "E4", "E5", "E3", "E7"]
    fn = dict(E6=t_e6, E1=t_e1, E2=t_e2, E4=t_e4, E5=t_e5, E3=t_e3, E7=t_e7)
    for e in which:
        d = load(e)
        if d is None: print(f"[{e}.pkl missing]"); continue
        fn[e](d); csv_add(e, d)
    with open("cells_v1.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["exp", "scenario", "cell", "en50", "en95", "en99", "kfiat_mean", "kfiat_p95", "latent_p95", "unbacked_mean", "junior_net", "freeze_days", "peak_hole_p95", "pushed", "disc_cost", "deep_transfer", "subpar_loss"]); w.writerows(rows_csv)
