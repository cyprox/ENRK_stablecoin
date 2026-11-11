"""Why: tables for ECON-T1 from t1_main.pkl (owner brief 2026-11-10). Usage: python3 -B report_t1.py t1_main.pkl > tables_t1.md"""
import sys
import numpy as np
import analyze_t1 as A

d = A.load(sys.argv[1]); idx = A.bidx(d["paths"]); S = A.all_stats(d)
PJ = (0, 10, 25, 50, 75, 100)
AX = [(j, 0) for j in PJ] + [(0, r) for r in PJ[1:]]
MIX = [(10, 10), (25, 25), (50, 25), (25, 50), (50, 50), (75, 25)]
f = lambda x, n=1: ("%." + str(n) + "f") % x
RS = (0, 1, 2, 3, 4, 5, 7, 10)

print("# T1-tables (every number a model output; 500 paths; loss % of tranche opening size; withheld = (phi_j+phi_r) x surplus)\n")
print("Columns: ENRK p50/p95[CI]/p99 | kFIAT mean/p95 | latent p95 | junior net mean[CI] / p5 / P(net<-50%) | calm-yr income | reserve end %debt | withheld %debt / %equity | borrower delta y=0 %debt | borrower cost %/yr = r + w*withheld, w=5/10/20%\n")
for s in (0, 15, 30, 50):
    print(f"\n## s = {s}%  (phi_j needs a junior: at s=0 only phi_j=0 rows are meaningful)\n")
    print("| r | pj | pr | ENRK p50 | p95 [CI] | p99 | kF mean | kF p95 | lat p95 | net mean [CI] | net p5 | P<-50 | calm | res_end | wh %debt | wh %eq | bor delta | cost w5 | w10 | w20 |")
    print("|" + "---|" * 20)
    for r in RS:
        for (pj, pr) in AX + MIX:
            c = (r / 100.0, s, pj, pr)
            if c not in S or (s == 0 and pj > 0): continue
            o = S[c]
            net = (f"{f(o['netm'])} [{f(o['netm_lo'])},{f(o['netm_hi'])}]", f(o['net5']), f(100 * o['p50'], 1), f(o['calm'])) if s > 0 else ("-",) * 4
            print(f"| {r} | {pj} | {pr} | {f(o['enrk50'])} | {f(o['enrk95'])} [{f(o['enrk95_lo'])},{f(o['enrk95_hi'])}] | {f(o['enrk99'])} | {f(o['kfm'])} | {f(o['kf95'])} | {f(o['la95'])} | {net[0]} | {net[1]} | {net[2]} | {net[3]} | {f(o['resend'])} | {f(o['withheld_debt'])} | {f(o['withheld_eq'])} | {f(o['bor_delta'])} | {f(o['cost5'])} | {f(o['cost10'])} | {f(o['cost20'])} |")

# --- paired effect of splits on the loss metrics, same r and s, vs phi=0
print("\n\n## Paired effect vs no split (same r, s): d ENRK p95, d kFIAT mean, d latent p95, with 95% bootstrap CI\n")
print("| s | r | pj | pr | dENRK p95 [CI] | dkF mean [CI] | dnet mean [CI] |\n|---|---|---|---|---|---|---|")
for s in (15, 30, 50):
    for r in (0, 3):
        for (pj, pr) in AX + MIX:
            c = (r / 100.0, s, pj, pr); c0 = (r / 100.0, s, 0, 0)
            if c == c0 or c not in S: continue
            e, ec = A.paired(d, c, c0, "enrk_loss_pct", .95, idx); k, kc = A.paired(d, c, c0, "kfiat_loss_pct", None, idx)
            a, b = A.col(d, c, "junior_inc_pct") - A.col(d, c, "kfiat_loss_pct"), A.col(d, c0, "junior_inc_pct") - A.col(d, c0, "kfiat_loss_pct")
            x = a - b; nc = A.mci(x, idx)
            print(f"| {s} | {r} | {pj} | {pr} | {f(e,2)} [{f(ec[0],2)},{f(ec[1],2)}] | {f(k,2)} [{f(kc[0],2)},{f(kc[1],2)}] | {f(x.mean(),1)} [{f(nc[0],1)},{f(nc[1],1)}] |")

# --- frontier
def cells(s, rmax=3, only=None):
    return [o for c, o in S.items() if c[1] == s and o["r"] <= rmax + 1e-9 and (only is None or only(o))]
def lab(o): return f"r={o['r']:.0f} pj={o['pj']} pr={o['pr']}"
print("\n\n## Hurdle frontier: minimum borrower cost (r + w*withheld, %/yr) s.t. junior E_w >= h, E_w = (1-w) calm + w * cycle net (w = crash prob/yr, same w in cost and E)\n")
print("r grid {0,1,2,3}; pure-fee column searches r up to 10 (r>3 only for pj=pr=0).\n")
print("| w | h | s | min-cost cell (any split) | cost | ENRK p95 | kF mean | | min pure fee (pj=pr=0) | cost | | min with pr=0 | cost | | min with pj=0 | cost |\n|" + "---|" * 15)
FR = {}
for w in (5, 10, 20):
    for h in (5, 10, 20):
        for s in (15, 30, 50):
            def feas(o): return o[f"E{w}"] >= h
            def best(L):
                L = [o for o in L if feas(o)]
                return min(L, key=lambda o: (o[f"cost{w}"], o["enrk95"])) if L else None
            b = best(cells(s)); pf = best(cells(s, 10, lambda o: o["pj"] == 0 and o["pr"] == 0)); b1 = best(cells(s, 3, lambda o: o["pr"] == 0)); b2 = best(cells(s, 3, lambda o: o["pj"] == 0))
            FR[(w, h, s)] = (b, pf)
            g = lambda o: (lab(o), f(o[f"cost{w}"], 2)) if o else ("none", "-")
            print(f"| {w} | {h} | {s} | {g(b)[0]} | {g(b)[1]} | {f(b['enrk95']) if b else '-'} | {f(b['kfm']) if b else '-'} | | {g(pf)[0]} | {g(pf)[1]} | | {g(b1)[0]} | {g(b1)[1]} | | {g(b2)[0]} | {g(b2)[1]} |")

print("\n\n## Minimum r that clears the hurdle for fixed splits (w=10%; r grid 0..10; 'none' = none)\n")
print("| h | s | " + " | ".join(f"({a},{b})" for a, b in AX + MIX) + " |\n|" + "---|" * (2 + len(AX + MIX)))
for h in (5, 10, 20):
    for s in (15, 30, 50):
        row = []
        for (pj, pr) in AX + MIX:
            rr = [c[0] * 100 for c in sorted(S) if c[1] == s and c[2] == pj and c[3] == pr and S[c]["E10"] >= h]
            row.append(f(min(rr), 0) if rr else "none")
        print(f"| {h} | {s} | " + " | ".join(row) + " |")
print("(cell label = (phi_j, phi_r) in %)")

print("\n\n## Protection per unit of extra borrower cost (w=10%): base = s same, r=0, no split. Extra cost = r + 0.10*withheld (%/yr). Gain = base - cell. Top 8 by ENRK p95 gain per cost; cost>0.05 only\n")
for s in (15, 30, 50):
    b0 = S[(0.0, s, 0, 0)]; rows = []
    for c, o in S.items():
        if c[1] != s or o["r"] > 3 + 1e-9: continue
        dc = o["cost10"] - b0["cost10"]
        if dc <= 0.05: continue
        rows.append((o, dc, (b0["enrk95"] - o["enrk95"]) / dc, (b0["kfm"] - o["kfm"]) / dc, (b0["kf95"] - o["kf95"]) / dc, (b0["la95"] - o["la95"]) / dc))
    print(f"\ns={s}: base ENRK p95 {f(b0['enrk95'])}, kF mean {f(b0['kfm'])}, kF p95 {f(b0['kf95'])}, latent p95 {f(b0['la95'])}\n")
    print("| rank | cell | extra cost %/yr | ENRK p95 | gain/cost (ENRK p95) | gain/cost (kF mean) | gain/cost (kF p95) | gain/cost (latent p95) | junior E10 |\n|" + "---|" * 9)
    for k, (o, dc, g1, g2, g3, g4) in enumerate(sorted(rows, key=lambda t: -t[2])[:8], 1):
        print(f"| {k} | {lab(o)} | {f(dc,2)} | {f(o['enrk95'])} | {f(g1,2)} | {f(g2,2)} | {f(g3,2)} | {f(g4,2)} | {f(o['E10'])} |")
    pf = [t for t in rows if t[0]["pj"] == 0 and t[0]["pr"] == 0]
    o, dc, g1, g2, g3, g4 = max(pf, key=lambda t: t[2])
    print(f"| pure-fee best | {lab(o)} | {f(dc,2)} | {f(o['enrk95'])} | {f(g1,2)} | {f(g2,2)} | {f(g3,2)} | {f(g4,2)} | {f(o['E10'])} |")

print("\n\n## Junior AND senior both safe, cheapest borrower cost (w=10%). Junior safe = E10 >= h AND P(net<-50%) <= 1%. Senior safe = ENRK p95 <= X (X is an analysis label, not a design threshold).\n")
print("| h | s | X | cheapest any split | cost | cheapest pure fee (r<=10) | cost |\n|---|---|---|---|---|---|---|")
for h in (5, 10, 20):
    for s in (15, 30, 50):
        for X in (1.0, 2.0):
            ok = lambda o: o["E10"] >= h and o["p50"] <= 0.01 and o["enrk95"] <= X
            L = [o for o in cells(s, 3) if ok(o)]; P = [o for o in cells(s, 10, lambda o: o["pj"] == 0 and o["pr"] == 0) if ok(o)]
            bL = min(L, key=lambda o: o["cost10"]) if L else None; bP = min(P, key=lambda o: o["cost10"]) if P else None
            print(f"| {h} | {s} | {X} | {lab(bL) if bL else 'none'} | {f(bL['cost10'],2) if bL else '-'} | {lab(bP) if bP else 'none'} | {f(bP['cost10'],2) if bP else '-'} |")
