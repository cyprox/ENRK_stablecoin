"""Why: sensitivity of the headline T1 cells to impact x capacity (owner brief 2026-11-10).
Usage: python3 -B report_sens_t1.py > tables_sens_t1.md   (reads t1_sens_<impact>_<cap>.pkl; s=30, r in {0,3}, HEAD splits)"""
import analyze_t1 as A
f = lambda x, n=1: ("%." + str(n) + "f") % x
SPL = [(0, 0), (100, 0), (50, 0), (25, 0), (0, 100), (0, 50), (0, 25), (25, 25), (50, 50)]
print("# T1 sensitivity: s=30%, loss % of tranche size; E10 = 0.9*calm + 0.1*cycle net; cost10 = r + 0.1*withheld(%debt)\n")
for r in (0.0, 0.03):
    print(f"\n## r = {r*100:.0f}%\n")
    print("| impact | cap/day | split (pj,pr) | ENRK p95 | dENRK p95 vs none [CI] | kF mean | kF p95 | dkF mean [CI] | latent p95 | net mean | P(net<-50) | E10 | res_end | withheld %debt | cost10 |")
    print("|" + "---|" * 15)
    for imp in ("0.04", "0.08", "0.16"):
        for cap in ("0.025", "0.05", "0.10"):
            d = A.load(f"t1_sens_{imp}_{cap}.pkl"); idx = A.bidx(d["paths"])
            S = A.all_stats(d, deep=False); c0 = (r, 30, 0, 0)
            for (pj, pr) in SPL:
                c = (r, 30, pj, pr); o = S[c]
                if c != c0:
                    e, ec = A.paired(d, c, c0, "enrk_loss_pct", .95, idx); k, kc = A.paired(d, c, c0, "kfiat_loss_pct", None, idx)
                    de = f"{f(e,2)} [{f(ec[0],2)},{f(ec[1],2)}]"; dk = f"{f(k,2)} [{f(kc[0],2)},{f(kc[1],2)}]"
                else: de = dk = "-"
                print(f"| {imp} | {float(cap)*100:.1f}% | ({pj},{pr}) | {f(o['enrk95'])} | {de} | {f(o['kfm'])} | {f(o['kf95'])} | {dk} | {f(o['la95'])} | {f(o['netm'])} | {f(100*o['p50'])} | {f(o['E10'])} | {f(o['resend'])} | {f(o['withheld_debt'])} | {f(o['cost10'],2)} |")
