"""Why: isolate why a stability fee LOWERS crash losses in the model (diagnostic for ECON-M2, hypotheses only).
Variants (s=30, D1/S1, frozen cfg, 500 paths): base r=0 | r=3% pre-year+crash | r=3% crash window only | r=0 with opening ICR 1.97
 | r=3% pre-year but fee stops at crash start | r=0 with ICR 1.97 + no-op.  Paired mean diff vs base."""
import sys
from multiprocessing import Pool
sys.dont_write_bytecode = True
import stress_fee as N
FZ = dict(auction_end_price=0.75, enable_redemption=True)
V = {
 "base r=0": dict(),
 "r=3 pre+crash": dict(stability_fee=.03, pre_days=365),
 "r=3 crash only (no pre-year)": dict(stability_fee=.03),
 "r=0, opening ICR 1.97 (=erosion w/o KAS leaving)": dict(target_icr=1.97),
 "r=0, opening ICR 1.94": dict(target_icr=1.94),
 "r=6 crash only": dict(stability_fee=.06),
}
def f(i):
    return [(lambda r: (r.enrk_loss_pct, r.kfiat_loss_pct, r.stranded_hole_pct, r.vaults_liquidated))(
        N.run(N.Scenario(name="d", total_drawdown=.85, seed=N.SEED + i, kfiat_share=.3, **FZ, **kw))) for kw in V.values()]
if __name__ == "__main__":
    with Pool(8) as p: R = p.map(f, range(500), chunksize=8)
    def q95(x): x = sorted(x); return x[int(.95 * len(x))]
    base = [r[0] for r in R]
    for j, name in enumerate(V):
        col = [[r[j][k] for r in R] for k in range(4)]
        dk = sum(r[j][1] - r[0][1] for r in R) / 500; de = sum(r[j][0] - r[0][0] for r in R) / 500
        print(f"{name:<52} ENRK mean {sum(col[0])/500:5.2f} p95 {q95(col[0]):5.1f} | kFIAT mean {sum(col[1])/500:5.2f} p95 {q95(col[1]):5.1f} | paired d(kF mean) {dk:+.2f} d(ENRK mean) {de:+.2f}")

# ---- part 2: where does the improvement come from? pre-year erosion vs crash-window fee (cached snapshots swapped) ----
def g(i):
    kw = dict(name="d", total_drawdown=.85, seed=N.SEED + i, kfiat_share=.3, pre_days=365, **FZ)
    s0 = N.run(N.Scenario(stability_fee=0.0, **kw), stop_after_pre=True)
    s3 = N.run(N.Scenario(stability_fee=.03, **kw), stop_after_pre=True)
    out = []
    for fee, snap in ((0.0, s0), (0.0, s3), (.03, s0), (.03, s3)):
        r = N.run(N.Scenario(stability_fee=fee, **kw), pre=snap)
        out.append((r.enrk_loss_pct, r.kfiat_loss_pct, r.final_kas_ratio))
    return out
if __name__ == "__main__":
    with Pool(8) as p: R = p.map(g, range(500), chunksize=8)
    print("part 2 (s=30): crash-window fee x pre-year-eroded collateral; paired d vs (no erosion, no crash fee)")
    for j, name in enumerate(("no erosion, no crash fee", "eroded collateral (r=3 pre-year), no crash fee", "no erosion, crash fee 3%", "eroded + crash fee 3%")):
        print(f"{name:<52} kFIAT mean {sum(r[j][1] for r in R)/500:5.2f} (d {sum(r[j][1]-r[0][1] for r in R)/500:+.2f})  ENRK mean {sum(r[j][0] for r in R)/500:5.2f} (d {sum(r[j][0]-r[0][0] for r in R)/500:+.2f})  KAS ratio {sum(r[j][2] for r in R)/500:.4f}")
