"""Why: test the hypothesis that the fee benefit comes from the mass of vaults clipped at ICR=153% at opening (build_population floor).
Paired effect of r=3% (365d pre-year + crash) vs r=0, s=30, D1/S1, 500 paths, by opening target ICR (floor mass falls as target rises)."""
import sys
from multiprocessing import Pool
sys.dont_write_bytecode = True
import stress_fee as N
FZ = dict(auction_end_price=0.75, enable_redemption=True, kfiat_share=.3)
T = (1.8, 2.0, 2.3, 2.6)
def f(i):
    o = []
    for t in T:
        for fee in (0.0, .03):
            r = N.run(N.Scenario(name="d", total_drawdown=.85, seed=N.SEED + i, target_icr=t, stability_fee=fee, pre_days=365, **FZ))
            o.append((r.kfiat_loss_pct, r.enrk_loss_pct, r.liquidated_pre))
    return o
if __name__ == "__main__":
    with Pool(8) as p: R = p.map(f, range(500), chunksize=8)
    import math
    for j, t in enumerate(T):
        fl = 0.5 * math.erfc(-(math.log(1.53 / t) / 0.22) / math.sqrt(2))
        a, b = 2 * j, 2 * j + 1
        print(f"target ICR {t}: share of vaults at the 153% floor ~{fl:.1%} | kFIAT mean r0 {sum(r[a][0] for r in R)/500:5.2f} r3 {sum(r[b][0] for r in R)/500:5.2f} (paired d {sum(r[b][0]-r[a][0] for r in R)/500:+.2f}) | ENRK mean d {sum(r[b][1]-r[a][1] for r in R)/500:+.2f} | pre-liq r3 {sum(r[b][2] for r in R)/500:.0f}")
