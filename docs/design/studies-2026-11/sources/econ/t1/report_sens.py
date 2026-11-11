"""Why: sensitivity tables (impact coefficient x liquidation capacity) for ECON-M2 headline cells s=30 (owner brief 2026-11-10).
Base (0.08, 0.05) comes from grid_main.pkl. Usage: python3 -B report_sens.py > tables_sens.txt"""
import analyze as A
IMP = (0.04, 0.08, 0.16); CAP = (0.025, 0.05, 0.10)
idx = A.boot_idx(500, 300)
def pk(i, c): return "grid_main.pkl" if (i, c) == (0.08, 0.05) else f"sens_{i}_" + {0.025: "0.025", 0.05: "0.05", 0.10: "0.10"}[c] + ".pkl"
print("## S1 D1/S1 s=30, r in {0,3,5}: loss metrics and junior net (cycle) by (impact, capacity/day)")
print("imp   cap    r% | KASend ENRK p50 p95 [CI]      | kF p50 mean p95 [CI]     | latent p95 [CI] | calm  cycle mean [CI]  p5   P(net<-50) | liq_pre | paired dkF mean [CI]")
flags = []
store = {}
for i in IMP:
    for c in CAP:
        d, F = A.load(pk(i, c)); store[(i, c)] = (d, F)
        for r in (0, .03, .05):
            cell = (r, 30, "D1", "S1"); o = A.cell_stats(d, F, cell, idx, deep=True)
            kas = sum(A.col(d, F, cell, "final_kas_ratio")) / d["paths"]
            dk, ck = A.paired_diff(d, F, cell, (0, 30, "D1", "S1"), "kfiat_loss_pct", idx)
            print(f"{i:<5} {c:<6} {r*100:<3g}| {kas:.3f} {o['enrk50']:>5.1f} {o['enrk95']:>5.1f} [{o['enrk95ci'][0]:.1f},{o['enrk95ci'][1]:.1f}] | {o['kf50']:>5.1f} {o['kfm']:>5.1f} {o['kf95']:>5.1f} [{o['kf95ci'][0]:.1f},{o['kf95ci'][1]:.1f}] | {o['la95']:>5.1f} [{o['la95ci'][0]:.1f},{o['la95ci'][1]:.1f}] | {o['calm']:>5.1f} {o['netm']:>6.1f} [{o['netmci'][0]:.1f},{o['netmci'][1]:.1f}] {o['net5']:>6.1f} {o['p50loss']:.3f} | {o['liqpre']:>5.0f} | {dk:+.2f} [{ck[0]:+.2f},{ck[1]:+.2f}]")
print("\n## S2 other D/S combos at r=3%, s=30: junior cycle mean / p5 / P(net<-50%) ; kFIAT mean ; latent p95  (per impact,cap)")
for D in ("D1", "D2", "D3"):
    for S in ("S1", "S2", "S3"):
        row = []
        for i in IMP:
            for c in CAP:
                d, F = store[(i, c)]; o = A.cell_stats(d, F, (.03, 30, D, S), idx, deep=False)
                row.append(f"{o['netm']:.0f}/{o['net5']:.0f}/{o['p50loss']:.2f}|kF{o['kfm']:.0f}|L{o['la95']:.0f}")
        print(f"{D} {S}: " + "  ".join(row))
print("(columns in order: imp 0.04 cap 2.5,5,10 | imp 0.08 cap 2.5,5,10 | imp 0.16 cap 2.5,5,10)")
print("\n## S3 'junior hole larger' scan: any (impact,cap,D,S,r) with paired mean kFIAT loss increase CI above 0 or latent p95 up >0.5pt vs r=0")
n = 0
for (i, c), (d, F) in store.items():
    for D in ("D1", "D2", "D3"):
        for S in ("S1", "S2", "S3"):
            for r in (.03, .05):
                dk, ck = A.paired_diff(d, F, (r, 30, D, S), (0, 30, D, S), "kfiat_loss_pct", idx)
                la = A.q(A.col(d, F, (r, 30, D, S), "stranded_hole_pct"), .95) - A.q(A.col(d, F, (0, 30, D, S), "stranded_hole_pct"), .95)
                en, ce = A.paired_diff(d, F, (r, 30, D, S), (0, 30, D, S), "enrk_loss_pct", idx)
                if ck[0] > 0 or la > 0.5 or ce[0] > 0:
                    n += 1; print(f"  imp {i} cap {c} {D} {S} r={r*100:g}%: dkF {dk:+.2f} [{ck[0]:+.2f},{ck[1]:+.2f}] dENRK {en:+.2f} [{ce[0]:+.2f},{ce[1]:+.2f}] dLatentP95 {la:+.1f}")
print("count flagged:", n, "of", len(store) * 9 * 2)
print("\n## S4 equilibrium s* from s=30 only is not possible (single s); calm-year return and crash-cycle mean at s=30 are in S1/S2 above.")
