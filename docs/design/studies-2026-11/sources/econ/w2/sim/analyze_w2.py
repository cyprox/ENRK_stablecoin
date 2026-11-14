"""Why: tables, paired statistics and bootstrap CIs for ECON-W2 (reactive borrowers) (decision: owner approval of plan 2026-11-13).
Usage: python3 -I -B analyze_w2.py > tables_w2.txt   (reads HL.pkl OAT.pkl SENS.pkl SIZE.pkl in this directory).
Units: losses = % of OPENING tranche (peg units); unbacked = % of opening debt VALUE (USD at the loss-day index); latent = stranded hole at the end, % opening debt units;
junior net = junior income - kFIAT write-off, % of kFIAT face, peg terms, cycle = 365 calm days + crash. Quantiles are 'higher' order statistics; CIs are paired bootstrap 95% (B=500)."""
import sys, os, pickle, math
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
import numpy as np
def load(e):
    p = os.path.join(HERE, e + ".pkl")
    if not os.path.exists(p): return None
    d = pickle.load(open(p, "rb")); d["F"] = {f: j for j, f in enumerate(d["fields"])}; return d
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
    net = col(d, k, "junior_inc_pct") - kf
    return dict(en=en, kf=kf, ub=ub, la=la, net=net, en95=pct(en, .95), en99=pct(en, .99), kfm=kf.mean(), kf95=pct(kf, .95), la95=pct(la, .95), pla=float(np.mean(la > 1e-9)),
                ubm=ub.mean(), netm=net.mean(), fz=col(d, k, "freeze_days").mean(), top=col(d, k, "rb_topup_pct").mean(), exc=col(d, k, "rb_exit_cash_pct").mean(),
                exs=col(d, k, "rb_exit_sell_pct").mean(), dump=col(d, k, "rb_dump_adv").mean(), run=col(d, k, "rb_run_red_pct").mean(), sur=col(d, k, "surplus_pct").mean(),
                red=col(d, k, "redeemed_pct").mean(), debt=col(d, k, "debt_units_start").mean(), acted=col(d, k, "rb_acted_vaults").mean())
def f(x, n=1): return f"{x:.{n}f}"
def hd(h): print("\n" + h + "\n" + "=" * len(h))
def line(o): return f"{f(o['en95'])} / {f(o['en99'])} | {f(o['kfm'])} / {f(o['kf95'])} | {f(o['la95'])} ({100*o['pla']:.1f}%) | {f(o['ubm'], 2)} | {o['netm']:+.1f}"
def main():
    HL = load("HL"); OAT = load("OAT"); SE = load("SENS"); SZ = load("SIZE")
    if HL:
        keys = list(HL["data"]); bases = []; archs = []; profs = []
        for (b, nm) in keys:
            a, p = nm.split("|")
            if b not in bases: bases.append(b)
            if a not in archs: archs.append(a)
            if p not in profs: profs.append(p)
        hd(f"H1 headline ({HL['paths']} paired paths): ENRK p95 / p99 | kFIAT mean / p95 | latent p95 (share of paths with hole) | unbacked mean | junior net")
        for b in bases:
            for a in archs:
                print(f"\n[{b}] {a}")
                for p in profs:
                    print(f"  {p:11s} {line(S(HL, (b, a + '|' + p)))}")
        hd("H2 paired difference vs N0 (passive, no redemption cushion): d ENRK p95 [CI] | d unbacked mean [CI]   ('*' CI excludes 0)")
        for b in bases:
            for a in archs:
                n0 = S(HL, (b, a + "|N0")); print(f"\n[{b}] {a}")
                for p in profs:
                    if p == "N0": continue
                    o = S(HL, (b, a + "|" + p))
                    pb = HL["data"][(b, a + "|" + p)][:, HL["F"]["enrk_loss_pct"]]; pn = HL["data"][(b, a + "|N0")][:, HL["F"]["enrk_loss_pct"]]
                    d95 = o["en95"] - n0["en95"]
                    B = bidx(len(pb)); v = np.sort(np.quantile(pb[B], .95, axis=1, method="higher") - np.quantile(pn[B], .95, axis=1, method="higher"))
                    c1 = (float(v[int(.025 * len(v))]), float(v[int(.975 * len(v))]))
                    du = o["ub"] - n0["ub"]; c2 = cim(du)
                    print(f"  {p:11s} dENRKp95 {d95:+6.1f} [{c1[0]:+.1f},{c1[1]:+.1f}]{'*' if c1[0]>0 or c1[1]<0 else ' '} | dUnbacked {du.mean():+6.2f} [{c2[0]:+.2f},{c2[1]:+.2f}]{'*' if c2[0]>0 or c2[1]<0 else ' '}")
        hd("H3 behaviour intensities (mean over paths): top-up USD % of opening debt value | exit by cash % debt | exit by self-liquidation % debt | KAS sold by borrowers/redeemers (days of ADV) | run redemption % ENRK | surplus % debt | vaults acting")
        for b in bases:
            for a in ("A3", "A5"):
                if (b, a + "|N0") not in HL["data"]: continue
                print(f"\n[{b}] {a}")
                for p in profs:
                    o = S(HL, (b, a + "|" + p))
                    print(f"  {p:11s} {f(o['top'])} | {f(o['exc'])} | {f(o['exs'])} | {f(o['dump'], 2)} | {f(o['run'])} | {f(o['sur'])} | {f(o['acted'], 0)} | debt start {o['debt']/1e6:.2f}M units")
        hd("H4 W1 reproduction (S0 = W1 cell with the exogenous redemption schedule, passive): flat85 A0/A3/A5/A8/STACK ENRK p95 / kFIAT mean / net / unbacked")
        for a in archs:
            if ("flat85", a + "|S0") in HL["data"]: o = S(HL, ("flat85", a + "|S0")); print(f"  {a:6s} {f(o['en95'])} / {f(o['kfm'])} / {o['netm']:+.1f} / {f(o['ubm'], 2)}")
    if OAT:
        hd(f"O1 one-at-a-time sweeps around CENTRAL_R ({OAT['paths']} paths): ENRK p95 / p99 | kFIAT mean / p95 | latent p95 (share) | unbacked mean | junior net  [base] arch|param=value")
        for k in OAT["data"]:
            print(f"  [{k[0]}] {k[1]:28s} {line(S(OAT, k))}")
    if SE:
        hd(f"E1 impact x capacity sensitivity ({SE['paths']} paths): ENRK p95 | unbacked mean   (rows impact .04/.08/.16 x cols capacity 2.5/5/10 %/day)")
        keys = list(SE["data"]); cells = {}
        for (b, nm) in keys:
            a, p, im, cp = nm.split("|"); cells[(b, a, p, im, cp)] = (b, nm)
        for b in sorted({k[0] for k in cells}):
            for a in sorted({k[1] for k in cells}):
                for p in ("N0", "CENTRAL_B", "HOSTILE_B"):
                    print(f"\n[{b}] {a} {p}")
                    for im in ("imp0.04", "imp0.08", "imp0.16"):
                        row = []
                        for cp in ("cap2.5", "cap5", "cap10"):
                            o = S(SE, cells[(b, a, p, im, cp)]); row.append(f"{f(o['en95'])} | {f(o['ubm'], 1)}")
                        print(f"  {im:8s} " + "   ".join(f"{r:>14s}" for r in row))
    if SZ:
        hd(f"Z1 size curves ({SZ['paths']} paths), liquidator capital 1% ADV x price, convex impact: unbacked mean by size_scale, and ceiling (largest size with unbacked mean <= tol)")
        keys = list(SZ["data"]); groups = {}
        for (b, nm) in keys:
            a, p, adv, sc = nm.split("|"); groups.setdefault((b, a, p, adv), {})[float(sc[2:])] = (b, nm)
        for g, d in sorted(groups.items()):
            xs = sorted(d); ub = [S(SZ, d[x])["ubm"] for x in xs]; en = [S(SZ, d[x])["en95"] for x in xs]
            debt = [S(SZ, d[x])["debt"] for x in xs]
            adv_usd = float(g[3][3:]) * 1e6 * 0.10
            ce = []
            for tol in (1.0, 3.0, 5.0):
                best = None
                if ub[0] > tol: ce.append("<0.05")
                else:
                    best = xs[0]
                    for j in range(1, len(xs)):
                        if ub[j] <= tol: best = xs[j]
                        else:
                            best = xs[j - 1] + (xs[j] - xs[j - 1]) * (tol - ub[j - 1]) / (ub[j] - ub[j - 1]); break
                    if best is not None: ce.append(f"{best:.2f}")
            debt_usd1 = debt[-1] * 1.0 if xs[-1] == 1.0 else float("nan")
            print(f"  [{g[0]}] {g[1]:6s} {g[2]:10s} {g[3]:8s} ub " + " ".join(f"{u:5.1f}" for u in ub) + " | ENRKp95 " + " ".join(f"{u:5.1f}" for u in en) +
                  f" | ceiling(tol 1/3/5) {ce[0]}/{ce[1]}/{ce[2]} x base; base debt {debt_usd1/1e6:.2f}M USD = {100*debt_usd1/adv_usd:.0f}% of ADV")
    if SZ:

        hd("Z2 sustainable debt at tolerance tol for unbacked mean (linear interpolation on the size grid .05-1.0; USD M at 0.10 USD/KAS; % of ADV): tol 1 / 3 / 5")
        for g, d in sorted(groups.items()):
            xs = sorted(d); ub = [S(SZ, d[x])["ubm"] for x in xs]; d1 = S(SZ, d[xs[-1]])["debt"]
            adv_usd = float(g[3][3:]) * 1e6 * 0.10; out = []
            for tol in (1.0, 3.0, 5.0):
                if ub[0] > tol: out.append("<0.05x"); continue
                best = xs[0]
                for j in range(1, len(xs)):
                    if ub[j] <= tol: best = xs[j]
                    else: best = xs[j - 1] + (xs[j] - xs[j - 1]) * (tol - ub[j - 1]) / (ub[j] - ub[j - 1]); break
                out.append(f"{best*d1/1e6:.2f}M ({100*best*d1/adv_usd:.0f}%)")
            print(f"  [{g[0]}] {g[1]:6s} {g[2]:10s} {g[3]:8s} " + " / ".join(out))

    # demand response (t2 numbers, ASSUMED): remaining demand m = D(r)/D(0) * exp(-k X)
    hd("D1 remaining demand m = D(r)/D(0) x exp(-k X); D(r)/D(0) at ICR 250, T=1 from econ-t2 (L8 .70, L4 .53, P .48 at r=3; 1.0 at r=0); k = semi-elasticity per pt of withheld surplus")
    print("  k=0.10 (L8-like, 40% cut per 5 pts) ... k=0.18 (60% cut per 5 pts, upper end of the owner brief)")
    for nm, d3 in (("L8", .70), ("L4", .53), ("P", .48)):
        for X in (0.0, 1.7, 5.0, 10.0):
            print(f"  set {nm:2s} r=3% X={X:4.1f} pts: m = " + " / ".join(f"k={k}: {d3*math.exp(-k*X):.2f}" for k in (0.10, 0.18)))
if __name__ == "__main__":
    main()
