"""Why: statistics, paired differences, bootstrap CIs and tables for ECON-T3 (owner brief 2026-11-10).
Usage: python3 -B analyze_t3.py main.pkl sstar.pkl cap.pkl > tables_t3.txt  (also writes cells_t3.csv)
Units: all losses are % of the OPENING tranche size in peg units; unbacked_usd is % of opening debt VALUE (units x I at the loss day)."""
import sys, pickle, csv
import numpy as np
import t3_scen as T

def load(p):
    d = pickle.load(open(p, "rb")); d["F"] = {f: j for j, f in enumerate(d["fields"])}; return d
def col(d, k, f): return d["data"][k][:, d["F"][f]]
def pct(x, p): return float(np.quantile(x, p, method="higher"))
_IDX = {}
def bidx(n, B=500):
    if n not in _IDX: _IDX[n] = np.random.default_rng(7).integers(0, n, size=(B, n))
    return _IDX[n]
def ci_stat(x, fn):
    v = np.sort([fn(x[b]) for b in bidx(len(x))]); return float(v[int(.025 * len(v))]), float(v[int(.975 * len(v))])
def ci_mean(x): v = np.sort(x[bidx(len(x))].mean(axis=1)); return float(v[int(.025 * len(v))]), float(v[int(.975 * len(v))])
def ci_q(x, p):
    B = x[bidx(len(x))]; v = np.sort(np.quantile(B, p, axis=1, method="higher")); return float(v[int(.025 * len(v))]), float(v[int(.975 * len(v))])
def fm(x, c=None, nd=1):
    return f"{x:.{nd}f}" + (f" [{c[0]:.{nd}f},{c[1]:.{nd}f}]" if c else "")

def stats(d, k, deep=False):
    en, kf, la = col(d, k, "enrk_loss_pct"), col(d, k, "kfiat_loss_pct"), col(d, k, "stranded_hole_pct")
    ub = col(d, k, "unbacked_usd_pct")
    o = dict(en50=pct(en, .5), en95=pct(en, .95), en99=pct(en, .99), enm=en.mean(), kfm=kf.mean(), kf95=pct(kf, .95),
             la95=pct(la, .95), ubm=ub.mean(), ub95=pct(ub, .95), ubu=col(d, k, "unbacked_units_pct").mean())
    s = k[5]
    if s > 0:
        net = col(d, k, "junior_inc_pct") - kf
        o.update(netm=net.mean(), net5=pct(net, .05), net50=pct(net, .5), calm=col(d, k, "junior_inc_pre_pct").mean(),
                 pg50=float((kf > 50).mean()))
    pm, pn = col(d, k, "peg_max"), col(d, k, "peg_min")
    o["ptrip"] = float(((pm >= 1.11 - 1e-12) | (pn <= 0.89 + 1e-12)).mean())
    o["bd"] = col(d, k, "breaker_days").mean(); o["fp"] = col(d, k, "final_peg").mean()
    o["fp5"] = pct(col(d, k, "final_peg"), .05); o["fp95"] = pct(col(d, k, "final_peg"), .95)
    o["pmax95"] = pct(pm, .95); o["liq"] = col(d, k, "vaults_liquidated").mean()
    if deep:
        o["en95ci"] = ci_q(en, .95); o["la95ci"] = ci_q(la, .95); o["kfmci"] = ci_mean(kf); o["ubmci"] = ci_mean(ub)
        o["en99ci"] = ci_q(en, .99)
        if s > 0: o["netmci"] = ci_mean(net)
    return o

def pdiff(d, k1, k0, f):
    x = col(d, k1, f) - col(d, k0, f); return float(x.mean()), ci_mean(x)

def Ew(o, w): return (1 - w) * o["calm"] + w * o["netm"]   # as M2: cycle net already contains the pre-year (calm) income

def equilibrium(E, ss, h):
    pts = [(s, E[s]) for s in ss]
    if pts[0][1] < h: return "none"
    for (s0, e0), (s1, e1) in zip(pts, pts[1:]):
        if e0 >= h > e1: return "%.0f" % (s0 + (s1 - s0) * (e0 - h) / (e0 - e1))
    return ">=%d" % pts[-1][0]

def key(sc, b="none", cap="units", st=0.18, r=0.03, s=30, S="S1"): return (sc, b, cap, st, r, s, S)

if __name__ == "__main__":
    M = load(sys.argv[1]); SS = load(sys.argv[2]) if len(sys.argv) > 2 else None; C = load(sys.argv[3]) if len(sys.argv) > 3 else None
    n = M["paths"]; print("paths per cell:", n, " bootstrap resamples: 500; CI = 95% percentile bootstrap\n")
    # csv
    with open("cells_t3.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["scen", "breaker", "cap", "stress", "r", "s", "S", "en50", "en95", "en99", "enm", "kfm", "kf95", "la95", "ubm", "ub95", "netm", "net5", "ptrip", "breaker_days", "final_peg", "liq"])
        for k in sorted(M["data"], key=str):
            o = stats(M, k); w.writerow(list(k) + [round(o.get(x, float('nan')), 3) for x in ("en50", "en95", "en99", "enm", "kfm", "kf95", "la95", "ubm", "ub95", "netm", "net5", "ptrip", "bd", "fp", "liq")])
    SC = list(T.SCEN)
    for (r, s, S, title) in ((0.03, 30, "S1", "r=3%, s=30%, S1"), (0.0, 30, "S1", "r=0%, s=30%, S1"), (0.0, 0, "S1", "r=0%, s=0%, S1 (no junior)"), (0.03, 30, "S3", "r=3%, s=30%, S3 (surplus to reserve)"), (0.03, 0, "S1", "r=3%, s=0%, S1")):
        print(f"## T1 [{title}] stress 0.18, breaker NONE (never called), capacity in units. Losses % of opening tranche; unbacked % of opening debt VALUE")
        print("scenario                    | ENRK p50  p95 [CI]        p99 | kFIAT mean [CI]     p95 | latent p95 [CI] | unbacked USD mean [CI]   p95 | junior net mean [CI]  p5 | final I mean (p5-p95) | P(|I-1|>=11% any day)")
        for sc in SC:
            o = stats(M, key(sc, r=r, s=s, S=S), deep=True)
            kf = f"{o['kfm']:.1f} [{o['kfmci'][0]:.1f},{o['kfmci'][1]:.1f}] {o['kf95']:.1f}" if s > 0 else "-"
            nt = f"{o['netm']:.1f} [{o['netmci'][0]:.1f},{o['netmci'][1]:.1f}] {o['net5']:.1f}" if s > 0 else "-"
            print(f"{sc:<27} | {o['en50']:>5.1f} {o['en95']:>5.1f} [{o['en95ci'][0]:.1f},{o['en95ci'][1]:.1f}] {o['en99']:>5.1f} | {kf} | {o['la95']:.1f} [{o['la95ci'][0]:.1f},{o['la95ci'][1]:.1f}] | {o['ubm']:.2f} [{o['ubmci'][0]:.2f},{o['ubmci'][1]:.2f}] {o['ub95']:.1f} | {nt} | {o['fp']:.2f} ({o['fp5']:.2f}-{o['fp95']:.2f}) | {o['ptrip']:.2f}")
        print()
    print("## T2 what the index ADDS to the KAS-only crash (paired, same paths, same KAS drawdown/days; comparator = flat I=1). stress 0.18, breaker none, r=3%, s=30, S1. Differences in points; mean paired [CI]")
    print("scenario                    | dENRK mean | dENRK p95 | dENRK p99 | dkFIAT mean | dlatent p95 | dunbacked USD mean | djunior net mean | flat ENRK p95 / unbacked mean")
    for sc in SC:
        if sc.startswith("flat"): continue
        f = T.flat_for(sc); k1, k0 = key(sc), key(f)
        de, ce = pdiff(M, k1, k0, "enrk_loss_pct"); dk, ck = pdiff(M, k1, k0, "kfiat_loss_pct"); du, cu = pdiff(M, k1, k0, "unbacked_usd_pct")
        o1, o0 = stats(M, k1), stats(M, k0)
        dn = (col(M, k1, "junior_inc_pct") - col(M, k1, "kfiat_loss_pct")) - (col(M, k0, "junior_inc_pct") - col(M, k0, "kfiat_loss_pct"))
        print(f"{sc:<27} | {de:>6.2f} [{ce[0]:.2f},{ce[1]:.2f}] | {o1['en95']-o0['en95']:>6.1f} | {o1['en99']-o0['en99']:>6.1f} | {dk:>6.2f} [{ck[0]:.2f},{ck[1]:.2f}] | {o1['la95']-o0['la95']:>5.1f} | {du:>6.2f} [{cu[0]:.2f},{cu[1]:.2f}] | {dn.mean():>6.2f} [{ci_mean(dn)[0]:.2f},{ci_mean(dn)[1]:.2f}] | {o0['en95']:.1f} / {o0['ubm']:.2f}")
    print()
    print("## T3 circuit breaker assumptions (stress 0.18, r=3%, s=30, S1). none=never called; mb=trips at |I-1|>=11%, pauses redemption (mint/burn), liquidations continue (latched); liq_latch=also halts liquidations while latched")
    print("scenario                    | breaker   | ENRK p95  p99 | kFIAT mean p95 | latent p95 | unbacked mean [CI] p95 | breaker days mean | P(trip) | junior net mean")
    for sc in SC:
        if sc.startswith("flat"): continue
        for b in T.BRK_ALL:
            k = key(sc, b)
            if k not in M["data"]: continue
            o = stats(M, k, deep=True)
            print(f"{sc:<27} | {b:<9} | {o['en95']:>5.1f} {o['en99']:>5.1f} | {o['kfm']:>5.1f} {o['kf95']:>5.1f} | {o['la95']:>5.1f} | {o['ubm']:>6.2f} [{o['ubmci'][0]:.2f},{o['ubmci'][1]:.2f}] {o['ub95']:>5.1f} | {o['bd']:>5.1f} | {o['ptrip']:.2f} | {o['netm']:.1f}")
    print()
    print("## T4 stress_sensitivity (p3 F4: the freeze returns above ~0.25): r=3%, s=30, S1. cells: ENRK p95 / latent p95 / unbacked mean   (breaker none | liq_latch)")
    print("scenario                    | " + " | ".join(f"stress {st}" for st in T.STRESS))
    for sc in SC:
        row = []
        for st in T.STRESS:
            parts = []
            for b in ("none", "liq_latch"):
                k = key(sc, b, st=st)
                if k in M["data"] and not (b == "liq_latch" and sc.startswith("flat")):
                    o = stats(M, k); parts.append(f"{o['en95']:.1f}/{o['la95']:.1f}/{o['ubm']:.1f}")
            row.append(" | ".join(parts))
        print(f"{sc:<27} | " + "  ||  ".join(row))
    print()
    print("## T4b same, r=0%, s=0% (no junior, no fee): ENRK p95 / latent p95 / unbacked mean   (breaker none)")
    for sc in SC:
        row = []
        for st in T.STRESS:
            k = key(sc, "none", st=st, r=0.0, s=0); o = stats(M, k); row.append(f"{o['en95']:.1f}/{o['la95']:.1f}/{o['ubm']:.1f}")
        print(f"{sc:<27} | " + "  |  ".join(row))
    print()
    print("## T5 junior cycle net return (% of kFIAT face, peg units, income valued at receipt; pre-year 365 d + crash), stress 0.18, breaker none. mean [CI] / p5 / P(kFIAT loss>50%)")
    print("scenario                    | r=0 S1 | r=3 S1 | r=3 S3 | r=0 S3  (s=30)")
    for sc in SC:
        row = []
        for (r, S) in ((0.0, "S1"), (0.03, "S1"), (0.03, "S3"), (0.0, "S3")):
            o = stats(M, key(sc, r=r, S=S), deep=True)
            row.append(f"{o['netm']:.1f} [{o['netmci'][0]:.1f},{o['netmci'][1]:.1f}] / {o['net5']:.1f} / {o['pg50']:.3f}")
        print(f"{sc:<27} | " + " | ".join(row))
    print()
    print("## T6 junior cycle net with breaker liq_latch vs none (r=3%, s=30, S1, stress 0.18) and at stress 0.25")
    for sc in SC:
        if sc.startswith("flat") or sc == "orig85": continue
        a = [stats(M, key(sc, b, st=st))["netm"] for st in (0.18, 0.25) for b in ("none", "liq_latch")]
        print(f"{sc:<27} | st.18 none {a[0]:>6.1f} latch {a[1]:>6.1f} | st.25 none {a[2]:>6.1f} latch {a[3]:>6.1f}")
    print()
    if SS is not None:
        print("## T7 equilibrium junior share s* (r=3%, D1/S1): E_w(s) = (1-w)*calm + w*cycle net (as M2; cycle net includes the calm year); linear interpolation on s in {15,30,50}; 'none' = E<h at s=15; '>=50' = E>=h up to s=50. Compare M2 D1/S1 r=3: h=10% -> 29")
        print("scenario                    | stress | breaker   | E10(15,30,50) | cycle net(15,30,50) | s* h=5% | h=10% | h=20% (w=10%) | h=10% w=5% / w=20%")
        for sc in ("flat85", "orig85", "p_base", "p_rho-.5", "p_rho+.5", "p_vol55", "p_vol55_rho-.5", "d85_x1.5", "d85_x2", "d85_x3"):
            for st in (0.18, 0.25):
                for b in (("none", "liq_latch") if sc != "flat85" else ("none",)):
                    k = lambda s: key(sc, b, st=st, r=0.03, s=s)
                    if k(15) not in SS["data"]: continue
                    o = {s: stats(SS, k(s)) for s in (15, 30, 50)}
                    nets = " ".join(f"{o[s]['netm']:.1f}" for s in (15, 30, 50)); e10 = " ".join(f"{Ew(o[s], .1):.1f}" for s in (15, 30, 50))
                    def sst(w, h): return equilibrium({s: Ew(o[s], w) for s in (15, 30, 50)}, (15, 30, 50), h)
                    print(f"{sc:<27} | {st:<6} | {b:<9} | {e10:<16} | {nets:<18} | {sst(.1,5):>5} | {sst(.1,10):>5} | {sst(.1,20):>5} | {sst(.05,10)} / {sst(.2,10)}")
        print()
    if C is not None:
        print("## T8 capacity as liquidator capital in USD (units capacity = cap*D0*I0/I) vs as coded (units). r=3%, s=30, S1, stress 0.18. ENRK p95 / latent p95 / unbacked mean / junior net")
        for (sc, b, cap, st) in sorted({(k[0], k[1], k[2], k[3]) for k in C["data"]}):
            kv = key(sc, b, "value"); ku = key(sc, b, "units")
            ov, ou = stats(C, kv), stats(M, ku)
            print(f"{sc:<27} | {b:<9} | units {ou['en95']:>5.1f}/{ou['la95']:>5.1f}/{ou['ubm']:>6.2f}/{ou['netm']:>6.1f} | value {ov['en95']:>5.1f}/{ov['la95']:>5.1f}/{ov['ubm']:>6.2f}/{ov['netm']:>6.1f}")
