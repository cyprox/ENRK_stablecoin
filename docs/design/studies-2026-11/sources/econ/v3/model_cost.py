# DERIVED arithmetic only (no market data fetched here). Constant-product pool, quote-side reserve L (USD),
# fee f per swap. x = relative price displacement wanted.
import math
f=0.003
print("L_usd  x    capital_in_usd  roundtrip_fee_usd  arb_loss_per_restore_usd(L*x^2/4)  blocks_to_sustain_1h_if_arbed_each_block*cost")
for L in (10_000,100_000,500_000,2_000_000):
    for x in (0.03,0.05,0.10,0.20):
        cap=L*(math.sqrt(1+x)-1)          # quote added to move price up by x
        rt=2*f*cap                        # fee paid in and out
        arb=L*x*x/4
        print(f"{L:>9} {x:4.2f} {cap:12.0f} {rt:12.1f} {arb:14.1f}")
# KAS book (r4 section 5): sell k KAS into merged 6-venue book; (order KAS, avg slip, last fill below best bid)
print("\nKAS merged book (r4 sec5): 1M KAS=0.22% avg; 5M=0.43%; 11.4M=0.94% avg/-1.7% last; 20M=2.33% avg/-5.7% last; 36.8M exhausts (-32.5%)")
kas=0.02951
for q,lab in ((11.4e6,'5% ADV'),(20e6,'8.8% ADV')):
    print(f"{lab}: {q*kas:,.0f} USD notional")
# publisher cost, fee floor = 100 sompi * max(compute, transient/2); KAS=0.02951 USD
for name,compute,transient in (("1->2 update tx (approx 2.6k mass, T4/AUD)",2600,6000),("round N=64 use",61406,150904),("round N=256 use",245342,602488),("round N=425 (derived)",245342/256*425,602488/256*425)):
    mass=max(compute,transient/2); fee_kas=100*mass/1e8
    print(f"{name}: floor fee {fee_kas:.4f} KAS = {fee_kas*kas:.5f} USD ; per day at 1 per 10 s (8640): {fee_kas*8640:.1f} KAS = {fee_kas*8640*kas:.2f} USD")
