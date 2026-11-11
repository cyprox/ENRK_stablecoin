"""Why: print the report tables for ECON-M2 from grid_main.pkl (owner brief 2026-11-10). Usage: python3 -B report.py grid_main.pkl > tables_main.txt"""
import sys, analyze as A
d, F = A.load(sys.argv[1]); n = d["paths"]; idx = A.boot_idx(n, 500)
RS = (0, .01, .02, .03, .05); SS = (15, 30, 50); DS = ("D1", "D2", "D3"); SSR = ("S1", "S2", "S3")
O = {}
def get(c):
    if c not in O: O[c] = A.cell_stats(d, F, c, idx, deep=True)
    return O[c]

print("## T1 loss metrics, D1/S1 (pure fee effect; no reserve). % of tranche opening size; [95% bootstrap CI of p95, 500 resamples]")
print("s   r%   ENRK p50  p95 [CI]        p99 | kFIAT p50  mean  p95 [CI]        | latent p95 [CI]")
for s in (0, 15, 30, 50):
    for r in RS:
        o = get((r, s, "D1", "S1"))
        print(f"{s:<3} {r*100:<4g} {o['enrk50']:>7.1f} {o['enrk95']:>6.1f} [{o['enrk95ci'][0]:.1f},{o['enrk95ci'][1]:.1f}] {o['enrk99']:>6.1f} | {o['kf50']:>7.1f} {o['kfm']:>6.1f} {o['kf95']:>6.1f} [{o['kf95ci'][0]:.1f},{o['kf95ci'][1]:.1f}] | {o['la95']:.1f} [{o['la95ci'][0]:.1f},{o['la95ci'][1]:.1f}]")

print("\n## T2 paired difference vs r=0 (same s,D,S, same paths): mean kFIAT loss (pts), mean ENRK loss (pts), latent p95 (pts); CI = bootstrap of the mean paired diff")
print("D S  s  r%  dkFIATmean [CI]          dENRKmean [CI]        dLatentP95   dkFIATp95  flag")
flags = []
for D in DS:
    for S in SSR:
        for s in SS:
            for r in RS[1:]:
                c = (r, s, D, S); c0 = (0, s, D, S)
                dk, ck = A.paired_diff(d, F, c, c0, "kfiat_loss_pct", idx)
                de, ce = A.paired_diff(d, F, c, c0, "enrk_loss_pct", idx)
                dl = get(c)["la95"] - get(c0)["la95"]; d95 = get(c)["kf95"] - get(c0)["kf95"]
                fl = "HOLE LARGER" if ck[0] > 0 or dl > 0.5 else ""
                if fl: flags.append((D, S, s, r, dk, dl))
                if s == 30 or fl:
                    print(f"{D} {S} {s:<3} {r*100:<3g} {dk:>7.2f} [{ck[0]:.2f},{ck[1]:.2f}]   {de:>7.2f} [{ce[0]:.2f},{ce[1]:.2f}]   {dl:>6.2f}   {d95:>7.2f}   {fl}")
print("flags (junior mean loss up with CI above 0, or latent p95 up > 0.5pt):", len(flags))

print("\n## T3 junior NET return, % of junior face, over (365-day pre period + 60-day crash), income valued at receipt. calm = pre-year income only (no crash).")
print("D S  s  r%   calm  | cycle: mean [CI]       p5 [CI]          p50    p95   P(net<-50%) P(loss>50% face) | mean if KAS income held to end")
for D in DS:
    for S in SSR:
        for s in SS:
            for r in RS:
                if s != 30 and not (D == "D1" and S == "S1"): continue
                o = get((r, s, D, S))
                print(f"{D} {S} {s:<3} {r*100:<3g} {o['calm']:>6.1f} | {o['netm']:>6.1f} [{o['netmci'][0]:.1f},{o['netmci'][1]:.1f}]  {o['net5']:>6.1f} [{o['net5ci'][0]:.1f},{o['net5ci'][1]:.1f}] {o['net50']:>6.1f} {o['net95']:>6.1f}   {o['p50loss']:.3f}   {o['pg50']:.3f} | {o['netholdm']:.1f}")

print("\n## T4 borrower impact (means over paths). liq_pre = vaults liquidated in the 365 calm days (of 1000); extra = paired minus r=0.")
print("r%   liq_pre extra_pre | liq_total extra_total | fee paid %debt (pre+crash) | surplus %debt (all) [S1 returned to owner; S2/S3 taken]")
for r in RS:
    o = get((r, 30, "D1", "S1")); o0 = get((0, 30, "D1", "S1"))
    print(f"{r*100:<4g} {o['liqpre']:>7.1f} {o['liqpre']-o0['liqpre']:>8.1f} | {o['liq']:>9.1f} {o['liq']-o0['liq']:>10.1f} | {o['fee']:>6.2f} (pre {o['feepre']:.2f}) | {o['sur']:.2f} (pre {o['surpre']:.2f})")
print("borrower cost as % of debt/yr = r (fee) ; in S2/S3 the liquidated borrower also loses the surplus (above, % of opening debt, 14-18% over the cycle, of which pre-year share shown)")

print("\n## T5 effect of D and S at r=3%, s=30 (and r=5%): losses and reserve")
print("r% D S  ENRK p95  p99 | kFIAT p50 mean p95 | latent p95 | reserve end %debt | reserve used %debt | junior cycle mean")
for r in (.03, .05):
    for D in DS:
        for S in SSR:
            o = get((r, 30, D, S))
            print(f"{r*100:<3g} {D} {S} {o['enrk95']:>7.1f} {o['enrk99']:>5.1f} | {o['kf50']:>6.1f} {o['kfm']:>5.1f} {o['kf95']:>5.1f} | {o['la95']:>5.1f} | {o['resend']:>6.2f} | {o['resused']:>6.2f} | {o['netm']:>6.1f}")

print("\n## T6 wrong-way risk (D1/S1, s=30): crash-window fee income vs naive flat-price expectation, and KAS-held marking")
for r in RS[1:]:
    c = (r, 30, "D1", "S1"); o = get(c)
    inc = A.col(d, F, c, "junior_inc_pct"); incp = A.col(d, F, c, "junior_inc_pre_pct"); hold = A.col(d, F, c, "junior_hold_pct")
    cr = [a - b for a, b in zip(inc, incp)]; naive = r * 100 / .30 * 60 / 365
    h = [a for a in hold]
    print(f"r={r*100:g}%  crash-window income {sum(cr)/n:.2f}% face (naive 60d at flat price & full book {naive:.2f}%) ratio {sum(cr)/n/naive:.2f}; total income at receipt {sum(inc)/n:.1f}% ; same KAS marked at END price {sum(h)/n:.1f}% (haircut {1-sum(h)/sum(inc):.0%}); cycle net at receipt {o['netm']:.1f}% vs held {o['netholdm']:.1f}%")

print("\n## T7 equilibrium junior share s* (percent of debt) where E_w(s) = h, linear interpolation on s over {15,30,50}; E_w = (1-w)*calm + w*cycle")
print("(entries: 'none' = E<h already at s=15 so the junior is not worth holding at the minimum share; '>=50' = E>=h up to s=50)")
for w in (.05, .10, .20):
    for h in (5, 10, 20):
        print(f"-- w={w*100:g}%/yr, hurdle h={h}%/yr")
        print("D S   " + "  ".join(f"r={r*100:g}%".ljust(10) for r in RS))
        for D in DS:
            for S in SSR:
                row = []
                for r in RS:
                    E = {s: A.Ew(get((r, s, D, S)), w) for s in SS}
                    e = A.equilibrium(E, SS, h)
                    row.append(e.replace(" (E<h at s=15)", "").replace(" (E>=h on all s)", "").ljust(10))
                print(f"{D} {S}  " + "  ".join(row))
