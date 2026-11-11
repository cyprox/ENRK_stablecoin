"""Why: extra liquidations caused by the fee in the 365-day calm year vs r (ICR erosion), 200 paths, no behavioural response by borrowers."""
import sys
from multiprocessing import Pool
sys.dont_write_bytecode = True
import stress_fee as N
FZ = dict(auction_end_price=0.75, enable_redemption=True, kfiat_share=.3)
R = (0.025, 0.03, 0.0305, 0.035, 0.04, 0.05, 0.07, 0.10)
def f(i):
    out = []
    for r in R:
        s = N.run(N.Scenario(name="d", total_drawdown=.85, seed=N.SEED + i, stability_fee=r, pre_days=365, **FZ), stop_after_pre=True)
        out.append((s["liquidated"], sum(1 for v in s["vaults"] if v[1])))
    return out
if __name__ == "__main__":
    with Pool(8) as p: X = p.map(f, range(200), chunksize=4)
    for j, r in enumerate(R):
        print(f"r={r*100:g}%: vaults liquidated in the calm year (of 1000) mean {sum(x[j][0] for x in X)/200:6.1f}  min {min(x[j][0] for x in X)} max {max(x[j][0] for x in X)}")
