"""Builds markdown tables from results_vs*.json. Run: python3 m1_tables.py [vs] > tables_vs1.0.md"""
import json,sys,numpy as np
VS=sys.argv[1] if len(sys.argv)>1 else '1.0'
R=json.load(open(f'results_vs{VS}.json'))['res']
MINT=.02; CAP=300_000; G=['calm','bull','sideways','slowbear']; RS=[0,.01,.02,.03,.05]
def g(reg,r,q,ic,k): return R[f'{reg}|{r}|{q}|{ic}'][k]
def mix(r,q,ic,k): return float(np.mean([g(x,r,q,ic,k) for x in G]))
def F(reg,r,q,ic,c): # total fee % of avg debt
    return MINT*c+g(reg,r,q,ic,'stab')+g(reg,r,q,ic,'liq')+g(reg,r,q,ic,'red')
def Fm(r,q,ic,c): return float(np.mean([F(x,r,q,ic,c) for x in G]))
def pct(x): return f'{100*x:.2f}'
B=(0.02,2.5)
print(f'## VOL x{VS}\n')
print('### T1 revenue split, % of avg debt/yr (churn 1, redemption 2%, ICR 250); columns mint|stab|liq|red|total')
for reg in G+['mix']:
    for r in RS:
        if reg=='mix':
            v=[MINT,mix(r,.02,2.5,'stab'),mix(r,.02,2.5,'liq'),mix(r,.02,2.5,'red')]
        else: v=[MINT,g(reg,r,.02,2.5,'stab'),g(reg,r,.02,2.5,'liq'),g(reg,r,.02,2.5,'red')]
        print(f'{reg:9s} r={100*r:.0f}% | '+' | '.join(pct(x) for x in v)+f' | {pct(sum(v))}')
print('\n### T1b total fee % of debt by churn (mix of 4 regimes, q=2%, ICR 250)')
for r in RS: print(f'r={100*r:.0f}% '+' '.join(f'c={c}:{pct(Fm(r,.02,2.5,c))}' for c in (.5,1,2)))
print('\n### T1c total fee % by redemption rate (mix, c=1, ICR250)')
for r in RS: print(f'r={100*r:.0f}% '+' '.join(f'q={int(q*100)}%:{pct(Fm(r,q,2.5,1))}' for q in (0,.02,.10)))
print('\n### T1d total fee % by opening ICR (mix, c=1, q=2%)')
for r in RS: print(f'r={100*r:.0f}% '+' '.join(f'ICR{int(i*100)}:{pct(Fm(r,.02,i,1))}' for i in (2.0,2.5,3.0)))
print('\n### T2 USD revenue per year, M USD (mix, q=2%, ICR 250): D=1/5/20M, churn .5/1/2')
for r in RS:
    print(f'r={100*r:.0f}% '+' | '.join(f'c={c}: '+'/'.join(f'{Fm(r,.02,2.5,c)*D:.3f}' for D in (1,5,20)) for c in (.5,1,2)))
print('\n### T3 years to treasury cap ($300k = 2.5M units, FROZEN s6; 20% of all fees, mean revenue constant)')
for r in RS:
    print(f'r={100*r:.0f}% '+' | '.join(f'c={c}: '+'/'.join(f'{CAP/(.2*Fm(r,.02,2.5,c)*D*1e6):.1f}' for D in (1,5,20)) for c in (.5,1,2)))
print('\n### T3b years to cap, by regime (D=5M, c=1, q=2%, ICR250)')
for r in RS: print(f'r={100*r:.0f}% '+' '.join(f'{x}:{CAP/(.2*F(x,r,.02,2.5,1)*5e6):.1f}' for x in G))
print('\n### T4 borrower. y* = annual return the borrowed funds must earn to beat holding KAS (%/yr of debt), = -(delta0 - 2%*churn). fees-only cost = r+2%c+1%q')
print('regime r  ICR | fees-only(c=1,q=2%) | y* c=1 q=2% | y* at r=0 | fee-attributable y*-y*0 | delta0 p10 (c=0 part)')
for reg in G+['mix']:
    for ic in (2.0,2.5,3.0):
        for r in (0,.02,.05):
            d0=(lambda k: mix(r,.02,ic,k)) if reg=='mix' else (lambda k: g(reg,r,.02,ic,k))
            dz=(mix(0,.02,ic,'delta0') if reg=='mix' else g(reg,0,.02,ic,'delta0'))
            y=-(d0('delta0')-MINT*1); y0=-(dz-MINT*1)
            print(f'{reg:9s} r={100*r:.0f}% ICR{int(ic*100)} | {pct(r+MINT+.01*.02)} | {pct(y)} | {pct(y0)} | {pct(y-y0)} | {pct(d0("delta0_p10"))}')
print('\n### T5 liquidations & fee effect on ICR (c-independent), q=2%: share of vaults liquidated in year | bad debt % of D0 | (end ICR omitted; analytic: the fee removes r/ICR0 of collateral per year)')
for reg in G:
    for ic in (2.0,2.5,3.0):
        print(f'{reg:9s} ICR{int(ic*100)} '+' ; '.join(f'r={100*r:.0f}%: {pct(g(reg,r,.02,ic,"liq_vault_share"))}|{pct(g(reg,r,.02,ic,"bad"))}' for r in (0,.02,.05)))
print('\n### T6 junior gross yield, % of junior notional per yr = F/s (mix of regimes; c=1,q=2%,ICR250). D1 = 100% fee to junior; D2 pre-cap = 80%; D2 post-cap = D1; D3 = 0. Net of bad debt absorbed.')
def jy(reg,r,s,share,mtm=False,c=1,q=.02,ic=2.5):
    regs=G if reg=='mix' else [reg]
    out=[]
    for x in regs:
        f=F(x,r,q,ic,c)*(R[f'{x}|{r}|{q}|{ic}']['fee_mtm']/R[f'{x}|{r}|{q}|{ic}']['fee_rcpt'] if mtm and R[f'{x}|{r}|{q}|{ic}']['fee_rcpt']>0 else 1)
        a=g(x,r,q,ic,'avgdebt'); loss=min(g(x,r,q,ic,'bad'),s)/a
        out.append((share*f-loss)/s)
    return float(np.mean(out))
for r in RS:
    print(f'r={100*r:.0f}% '+' | '.join(f's={int(s*100)}%: D1 {pct(jy("mix",r,s,1))}, D2pre {pct(jy("mix",r,s,.8))}' for s in (.15,.3,.5)))
print('\n### T6b junior wrong-way: D1 yield s=30% by regime, receipt-value vs held-in-KAS marked at year end; p10 of fee (% of debt)')
for reg in G:
    for r in (0,.02,.05):
        k=f'{reg}|{r}|0.02|2.5'
        print(f'{reg:9s} r={100*r:.0f}% | at receipt {pct(jy(reg,r,.3,1))} | held in KAS {pct(jy(reg,r,.3,1,True))} | corr(fee USD, KAS ret)={R[k]["corr_ret"] if R[k]["corr_ret"] is None else round(R[k]["corr_ret"],2)} | mtm p10 fee %debt {pct(R[k]["fee_mtm_p10"])}')
print('\n### T7 s* = largest junior share s (1% grid) with net yield >= hurdle h; 100% = nobody needs to be compensated beyond; mix regimes; c=1,q=2%,ICR250. cols D1 | D2pre | D1-held-in-KAS | D3')
def sstar(r,h,share,mtm=False,reg='mix',c=1):
    best=0
    for s in np.arange(.01,1.001,.01):
        if jy(reg,r,s,share,mtm,c)>=h: best=s
    return best
for reg in ('mix','calm','bull','sideways','slowbear'):
  for h in (.05,.10,.20):
    for c in (1,):
        print(f'{reg} h={int(h*100)}% '+' ; '.join(f'r={100*r:.0f}%: {100*sstar(r,h,1,False,reg,c):.0f}|{100*sstar(r,h,.8,False,reg,c):.0f}|{100*sstar(r,h,1,True,reg,c):.0f}|0' for r in RS))
print('\n### T7b s* for mix, h=10%, by churn (D1)')
for c in (.5,1,2): print(f'c={c} '+' ; '.join(f'r={100*r:.0f}%: {100*sstar(r,.10,1,False,"mix",c):.0f}' for r in RS))
print('\n### bad debt (all vaults) % of D0, max over 300 paths, by regime ICR200 r=0/5%')
for reg in G: print(reg,' '.join(f'r={100*r:.0f}%:mean {pct(g(reg,r,.02,2.0,"bad"))} p90 {pct(g(reg,r,.02,2.0,"bad_p90"))} max {pct(g(reg,r,.02,2.0,"bad_max"))}' for r in (0,.05)))
