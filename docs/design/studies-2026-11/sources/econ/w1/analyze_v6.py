"""Why: tables for ECON-V6 from v6.pkl (paired paths, bootstrap CIs; decision: owner brief 2026-11-11).
Usage: python3 -B analyze_v6.py v6.pkl > tables_v6.txt
All losses: % of the OPENING tranche in peg units; unbacked: % of opening debt VALUE (units x I at the loss day, plus latent hole at end I)."""
import sys, pickle
import numpy as np
sys.dont_write_bytecode = True
import analyze_t3 as A3
d = pickle.load(open(sys.argv[1], "rb")); F = {f: j for j, f in enumerate(d["fields"])}; D = d["data"]
def c(k, f): return D[k][:, F[f]]
def pct(x, p): return A3.pct(x, p)
def fm(x, ci=None, nd=1): return A3.fm(x, ci, nd)
def row(label, r, s=30, S="S1", base=None):
    k = (label, r, s, S)
    if k not in D: return None
    en, kf, la, ub = c(k, "enrk_loss_pct"), c(k, "kfiat_loss_pct"), c(k, "stranded_hole_pct"), c(k, "unbacked_usd_pct")
    o = dict(en50=pct(en, .5), en95=pct(en, .95), en95ci=A3.ci_q(en, .95), kfm=kf.mean(), kf95=pct(kf, .95), la95=pct(la, .95), la95ci=A3.ci_q(la, .95),
             ubm=ub.mean(), ubci=A3.ci_mean(ub), ub95=pct(ub, .95), p_ub5=float((ub > 5).mean()))
    if s > 0:
        net = c(k, "junior_inc_pct") - kf; o["net"] = net.mean(); o["netci"] = A3.ci_mean(net); o["pg50"] = float((kf > 50).mean())
    fp = c(k, "final_peg"); o["fp"] = fp.mean(); o["fp5"] = pct(fp, .05); o["fp95"] = pct(fp, .95)
    bd = c(k, "breaker_days"); o["ptrip"] = float((bd > 0).mean()); o["bd"] = bd.mean(); fd = c(k, "breaker_first_day"); o["first"] = float(np.median(fd[fd >= 0])) if (fd >= 0).any() else float("nan")
    o["redeemed"] = c(k, "redeemed_pct").mean(); o["liq"] = c(k, "vaults_liquidated").mean()
    o["icr_end"] = c(k, "mean_icr_end").mean()
    if base:
        b = (label if base is True else base, r, s, S)
        x = c(k, "unbacked_usd_pct") - c(b, "unbacked_usd_pct"); o["dub"] = x.mean(); o["dubci"] = A3.ci_mean(x)
        x = c(k, "enrk_loss_pct") - c(b, "enrk_loss_pct"); o["den"] = x.mean(); o["denci"] = A3.ci_mean(x)
        x = c(k, "kfiat_loss_pct") - c(b, "kfiat_loss_pct"); o["dkf"] = x.mean(); o["dkfci"] = A3.ci_mean(x)
    return o
hdr = "| %s | ENRK p50 | ENRK p95 [CI] | kFIAT mean | kFIAT p95 | latent p95 [CI] | unbacked mean [CI] | P(unb>5%%) | junior net [CI] | final I mean (p5-p95) | trip%% | brk days | first day |"
def line(name, o):
    return "| %s | %.1f | %s | %.1f | %.1f | %s | %s | %.0f%% | %s | %.2f (%.2f-%.2f) | %.0f | %.1f | %s |" % (
        name, o["en50"], fm(o["en95"], o["en95ci"]), o["kfm"], o["kf95"], fm(o["la95"], o["la95ci"]), fm(o["ubm"], o["ubci"], 2), 100 * o["p_ub5"],
        fm(o["net"], o["netci"]) if "net" in o else "-", o["fp"], o["fp5"], o["fp95"], 100 * o["ptrip"], o["bd"], ("%.0f" % o["first"]) if o["first"] == o["first"] else "-")
import v6_scen as V
print("N paths =", d["paths"], "cells =", len(D))
print("\n## BASE (r=3%, s=30%, S1) by index scenario")
print(hdr % "scenario"); print("|" + "---|" * 13)
for sc in V.S_BASE:
    o = row(f"base|{sc}", .03); print(line(sc, o))
print("\n## BASE no junior, no fee (r=0, s=0)")
print("| scenario | ENRK p95 [CI] | latent p95 | unbacked mean [CI] | P(unb>5%) |"); print("|---|---|---|---|---|")
for sc in V.S_BASE:
    o = row(f"base|{sc}", 0.0, 0); print("| %s | %s | %.1f | %s | %.0f%% |" % (sc, fm(o["en95"], o["en95ci"]), o["la95"], fm(o["ubm"], o["ubci"], 2), 100 * o["p_ub5"]))
print("\n## BASE: fee only (r=3%, s=0)")
for sc in V.S_BASE:
    o = row(f"base|{sc}", .03, 0); print("| %s | %s | %.1f | %s |" % (sc, fm(o["en95"], o["en95ci"]), o["la95"], fm(o["ubm"], o["ubci"], 2)))
print("\n## BREAKER (r=3%, s=30, S1; deltas paired vs breaker none, same scenario)")
for sc in V.S_BRK:
    print("\n### scenario", sc); print(hdr % "trigger_action" + " dUnbacked vs none [CI] | dENRK mean | dkFIAT mean |"); print("|" + "---|" * 16)
    for t in V.TRIG:
        o = row(f"brk|{sc}|{t}", .03, base=f"brk|{sc}|none"); print(line(t, o) + " %s | %+.2f | %+.2f |" % (fm(o["dub"], o["dubci"], 2), o["den"], o["dkf"]))
print("\n## SHAPING (clip / slope / rate limit), r=3%, s=30, S1; holder cost = mean final I (frozen) - mean final I (variant)")
for sc in V.S_SHAPE:
    print("\n### scenario", sc); print(hdr % "shape" + " dUnbacked vs frozen [CI] | holder dI (mean) |"); print("|" + "---|" * 15)
    f0 = c((f"shape|{sc}|frozen", .03, 30, "S1"), "final_peg").mean()
    for t in V.SHAPE:
        o = row(f"shape|{sc}|{t}", .03, base=f"shape|{sc}|frozen"); print(line(t, o) + " %s | %+.3f |" % (fm(o["dub"], o["dubci"], 2), o["fp"] - f0))
print("\n## kFIAT A1 vs A2")
print("| scenario | cell | mode | kFIAT mean | kFIAT p95 | ENRK p95 | latent p95 | junior net | W_end mean (p5/p50) | P(W<0.5) | ratio-form W mean | max |A2-A1| over all paths and fields |")
print("|" + "---|" * 12)
for sc in V.S_KF:
    for (r, s, S) in ((.03, 30, "S1"), (.03, 15, "S1"), (.03, 50, "S1"), (.03, 30, "S3")):
        for m in ("A1", "A2"):
            k = (f"kf|{sc}|{m}", r, s, S); o = row(k[0], r, s, S); w = c(k, "kfiat_index_end")
            mx = max(np.abs(c((f"kf|{sc}|A1", r, s, S), f) - c((f"kf|{sc}|A2", r, s, S), f)).max() for f in ("enrk_loss_pct", "kfiat_loss_pct", "stranded_hole_pct", "junior_inc_pct", "unbacked_usd_pct")) if m == "A2" else float("nan")
            print("| %s | s=%d %s | %s | %.1f | %.1f | %.1f | %.1f | %.1f | %.2f (%.2f/%.2f) | %.0f%% | %.3f | %s |" % (sc, s, S, m, o["kfm"], o["kf95"], o["en95"], o["la95"], o["net"], w.mean(), pct(w, .05), pct(w, .5), 100 * (w < .5).mean(), c(k, "kfiat_index_ratio_end").mean(), "%.2g" % mx if m == "A2" else ""))
