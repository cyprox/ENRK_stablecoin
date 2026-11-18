# Independent re-derivation of KSD (kaspadollar.com) maths. Stdlib only. Run: python3 -I 03-check.py
from math import log, floor, ceil
from fractions import Fraction as Fr
def h(s): print('\n== '+s)

h('1. Liquidation eq (4): x=(Rl*d - c*l)/(Rl-1-p)')
def liq(c,d,l,Rl=2.0,p=0.05):
    x=(Rl*d-c*l)/(Rl-1-p); 
    cn=c-(1+p)*x/l; dn=d-x
    return x,cn,dn,cn*l/dn
# whitepaper/how-it-works example: 1,000,000 KAS at $0.0366 => $36,600; debt 14,640 (250%)
c=1_000_000; P0=0.0366; d=36600/2.5; print('debt at 250%:',d)
l=P0*0.75; print('price after -25%:',l,' value',c*l,' ratio',c*l/d)
x,cn,dn,r=liq(c,d,l)
print('x repaid =',x,'(%.1f%% of debt)'%(100*x/d)); print('KAS value received =',(1.05)*x,' penalty =',0.05*x)
print('after: value',cn*l,'debt',dn,'ratio',r)
print('site says: x~1,926; KAS worth 2,023; left 25,427 vs 12,714 KSD; owner lost 96')
print('check: 1.05*1926=',1.05*1926,' 27450-2023=',27450-2023,' 14640-1926=',14640-1926,' penalty .05*1926=',.05*1926)
print('NOTE: ratio 27450/14640 =',27450/14640)
# rounding rule: whole KAS rounded down / whole KSD rounded up -> epsilon check
h('1b. Liquidation property sweep: ratio after == Rl for rho in (1+p, Rl)')
bad=0
for rho in [1.06,1.2,1.5,1.9,1.999]:
    d=1000.;c=rho*d/1.0; x,cn,dn,r=liq(c,d,1.0); print(rho,round(x,3),round(r,6))
h('1c. Edge: x vs d. x<d iff rho(l) > 1+p ? x<d  <=> Rl*d-c*l < d*(Rl-1-p) <=> c*l/d > 1+p')
for rho in [1.05,1.0500001,1.04,1.0]:
    d=1000.;x=(2*d-rho*d)/(2-1-.05);print('rho',rho,'x/d',x/d)
print('Liquidator gain in USD per KSD repaid = p*x at l; but only profitable vs market if l <= (1+p)P')
h('1d. Is a partial liquidation always strictly improving the owner? Bad-debt zone 1<rho<=1.05 full liquidation: owner gets 0')
h('1e. Observed: stated threshold text "Below 200%: liquidate part" but covenant condition 1<=rho(l)<Rl; rho>=Rl cannot be liquidated; after-liq rho = Rl exactly -> immediately re-liquidatable on any tick down (no hysteresis).')

h('2. Theorem 1: issuance cap')
M=50000;k=8;B=M/(2*k);print('B=',B,'2B=',2*B,'k*2B=',k*2*B)
# worst case within a 24h window: start b=B full, mint B at t0, refill B over 24h, mint B again => 2B per UTXO
# but a sliding-window adversary: could repeated windows exceed? long-run rate:
print('long-run mint rate per UTXO per day = refill B =',B,' => total/day =',k*B,'(sustained), burst 2B*k = M in any 24h window')
# Check sliding: at any 24h window mint <= b0 + refill(24h) <= B + B. Sustained: after burst, 24h later b refills to B. So back-to-back windows: day1 [t0,t0+24h]: 2B; day2 (t0+24h..t0+48h]: b=B at t0+24? 
b=B; tot=[];
for day in range(4):
    m=b; b=0; refill=B; m2=refill; tot.append(m+m2); b=0
print('sim greedy per-UTXO: mint everything available at start of each 24h, plus all refill at end:',tot,'(first day 2B, later days 2B only if mint just before boundary)')
print('Overlap check: any 24h window contains <= B(start budget)+B(refill) =',2*B,'. OK; the bound M is for NET supply; but burning credits budget (b+=x up to B), so burn+remint cycles allow GROSS minting beyond M with flat net: not a problem for net supply but see attack notes.')
print('Subtle: the bound 2B per UTXO holds only if timestamp-based proven time cannot exceed real time. Proven dt<=t_e+ - t_e (chain timestamps). Timestamps are bounded below by PMT and above by local clock +132s (site) -> miners can skew by minutes, refill by ~dt/24 of B => small')
print('Replicas: minting UTXO choice by user; k=8 parallel; attacker can use all 8 => 50,000 KSD/day unbacked worst case; as % of ? supply unknown')

h('3. Theorem 2: thresholds')
for pi,g in [(1.0,.5),(0.9,.5),(0.55,.5),(0.5,.5)]:
    print(f'pi={pi} g={g}: control price a>=pi/2={pi/2:.3f}; stop oracle a>pi-g={pi-g:.3f}')
print('how-it-works claim: a>=25% min when pi=50%: pi/2=',0.5/2,' ; site: "hashrate needed can never be less than 25% of network"')
print('BUT attacker with a withholding while others vote: attacker also lowers pi? If attacker is part of pi and votes, pi fixed. For control: needs a/pi>=1/2 AND window valid pi>=g. If honest pi_h=0.5-eps (<g) honest alone invalid; attacker adds votes to make window valid: needs a>=g-pi_h; attacker votes all => share a/(a+pi_h) >=1/2 iff a>=pi_h. So min a = max(...)? with pi_h=g/2.. a=pi_h=0.25 -> pi=0.5 valid. consistent with 25%.')
print('Hidden-hashrate question: pi measured as share of BLOCKS carrying votes, equals hashrate share only in expectation; window is 6000 blocks (~10 min) so sampling noise sd of share ~', (0.25*0.75/6000)**.5)
print('Launch pi=0.9: control 45%, stop >40% -> matches site')
print('Two largest (57.1%) vs thresholds with pi=1: control 50%, stop 50% => yes both. With pi=0.9: 45/40 => yes.')
print('Largest 32.7%: stop at pi=0.9 needs >40%: no. But after launch pi may drop toward g=0.5 -> stop needs >0 ... at pi=0.6, stop needs >10% (!). control needs 30%.')
for pi in [0.9,0.8,0.7,0.6,0.55]:
    print(f'  pi={pi}: control>={pi/2:.3f} stop>{pi-0.5:.3f}')
print('=> stop-oracle threshold collapses as participation falls toward g; 32.7% single pool could freeze oracle if pi<=0.727 (pi-0.5<0.327)')
print('   single pool 32.7% could control price if pi<=0.654 and min-pi-with-pool: control a>=pi/2')
h('3b. Median manipulation by cost: attacker with 32.7% (one pool) with pi=0.6')
print('   votes share a/pi=',0.327/0.6)
print('   also, window blocks are the 6000 highest blue work among mergesets; a pool can withhold only its own.')

h('4. Backing claims: 60% (2.5x) and 50% (2.0x)')
print('1-1/2.5 =',1-1/2.5,' 1-1/2 =',1-1/2)
print('Site: "In order for [liquidation] the price has to fall 20% from opening" : 1-2/2.5 =',1-2/2.5)
print('Whitepaper (5): rho(P)>=Rl*P/lu ; backed while P>=lu/Rl. After liquidation rho=Rl at l_u. fall of 50% from lu.')
print('But vault between 200%-250% never touched: ratio at lu could be ANY >=Rl; so rho(P)>=Rl*P/lu holds. OK. Vault at 250% survives 60% only if no liquidation: "60%" claim is for vaults at exactly open ratio; vaults at 200% only 50%.')
print('Backing is at ORACLE-lagged lu, and ignores liquidation penalty/redeem effects: redemption takes x/l KAS for x KSD: if l>P redeemer overpays?; l<P redeemer profits')
h('5. Fall limit: liquidation price l falls max 25%/h; lag')
F=.25;U=.10;p=.05
tau=8/60; print('lag factor (1-F)^-tau =',(1-F)**-tau,' vs 1+p=',1+p)
print('P fall between updates (10 min) at worst-case 25%/h-equivalent: 1-0.75^(10/60)=',1-0.75**(10/60))
for D in (.2,.4,.5):
    hh=log((1+p)*(1-D))/log(1-F); print(f'sudden fall D={D}: hours until l reaches (1+p)P: {hh:.3f} h = {hh*60:.1f} min')
print('Real crashes faster than 25%/h: e.g. -25% in 1h; then l lags by (price ratio). In flash crash (-40% in 10 min) liquidators earn NOTHING (l>(1+p)P) for 1.6h; vault drifts to <100% if fall>50%.')
print('Lag compounding: liquidation price l is rate-limited, so liquidation proceeds in a crash only if fall < ~ F per hour, i.e. the protocol cannot liquidate in precisely the scenario liquidations are needed.')
print('Doubling time of mint price: ln2/ln1.1 =',log(2)/log(1.1),'h ; halving l:',log(2)/-log(1-F),'h; tenth:',log(10)/-log(1-F))
print('Mint-price rate limit effect on honest users: after a crash and rebound m rises <=10%/h: recovery from -40% to old takes',log(1/0.6)/log(1.1),'h before minting at the true price. Minting allowed only when rho(m)>=2.5 using m<=median.')
print('Continuous compounding check: per hour (1+U) with dt fractional hours => m*(1.1)^dt consistent.')
h('6. Oracle price lag tau')
w=10;d=3;print('tau = w/2+delta =',w/2+d,'min')
h('7. Misc numbers on site')
print('KAS fall ATH->Oct2026: 0.17^(1/19700)-1 rate/h =',1-0.17**(1/19700),' => %.4f%%'%(100*(1-0.17**(1/19700))))
print('27 months in hours =',27*30.4375*24)
print('W=6000 blocks at 10bps =',6000/10/60,'min')
print('Window: 6000 blocks "last 10 min"; actual network block rate (verify): see 03-technical-verification.md')
print('Fundraising: 3.6M+1.4M =',3.6e6+1.4e6,' 72%/28% of 5M:',.72*5e6,.28*5e6)
print('Fee: 0.1% of value, floor 1 KAS; at KAS=0.0366 USD floor equals',1*0.0366,'USD -> floor binds for operations < $36.6 (i.e. 100% fee on a $0.0366 op; min debt 10 KSD => min fee 1 KAS=$0.0366=0.37% of 10 KSD')
h('8. Dust / min debt 10 KSD: griefing')
print('liquidation of a 10 KSD vault: penalty 5% =0.5 KSD vs oracle fee floor 1 KAS =',0.0366,'USD: liquidator profit',0.5-0.0366,'USD minus tx fee; min tx fee 100 sompi/gram*...; at KAS 0.0366 profitable only marginally')
