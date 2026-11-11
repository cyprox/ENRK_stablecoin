"""Normal-time economics of ENRK. Model outputs under stated assumptions, not forecasts.
Run: python3 m1_sim.py  -> writes results.json and prints calibration. Std lib + numpy."""
import json, sys, itertools
import warnings; warnings.filterwarnings('ignore')
import numpy as np
S='/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad'
OUT=S+'/econ/m1'
# ---- MEASURED parameters: docs/design/FROZEN_PARAMETERS.md s6 (fees), s1-4 (ICR/MCR); stress_test_crash.py:37 (liq fee on proceeds)
MINT,LIQ,RED,MCR,TREAS_SHARE,TREAS_CAP_USD=0.02,0.04,0.01,1.5,0.20,300_000.0
# ---- data
d=json.load(open(S+'/raw/kc_KAS.json'))['data']; d.sort(key=lambda r:int(r[0]))
close=np.array([float(r[2]) for r in d]); lr=np.diff(np.log(close))
calib={'days':len(close),'daily_sd':float(lr.std()),'ann_vol':float(lr.std()*np.sqrt(365)),
 'min_day':float(lr.min())}
w=np.log(close[365:]/close[:-365]); calib['roll365_ret_pct']={q:float((np.exp(np.percentile(w,q))-1)*100) for q in (5,25,50,75,95)}
calib['roll365_share_ret_gt100pct']=float((w>np.log(2)).mean()); calib['roll365_share_ret_lt_m50pct']=float((w<np.log(.5)).mean())
calib['roll365_share_between_m25_p50']=float(((w>np.log(.75))&(w<np.log(1.5))).mean())
# ---- regimes (ASSUMED drift / vol multiplier; vol base MEASURED)
VS=float(sys.argv[1]) if len(sys.argv)>1 else 1.0   # vol sensitivity multiplier
REG={'calm':(0.05,0.4*VS),'bull':(np.log(2.0),0.7*VS),'sideways':(0.0,0.7*VS),'slowbear':(np.log(0.5),0.7*VS)}
NP,NV,T=300,100,365
def paths(reg,seed):
    mu,vm=REG[reg]; rng=np.random.default_rng(seed)
    x=lr-lr.mean(); x=np.clip(x,-0.15,None)   # ASSUMED: no crash days (< -15%)
    B=10; out=np.empty((NP,T))
    for p in range(NP):
        idx=[]
        while len(idx)<T:
            s=rng.integers(0,len(x)-B); idx+=list(range(s,s+B))
        out[p]=x[idx[:T]]*vm
    out+=mu/T
    return np.exp(np.cumsum(out,axis=1))*1.0   # price relative to P0=1 (end of day t)
def run(P,r,q,icr0,seed=1):
    """P: (NP,T) price rel. to 1. D0=1 per path split over NV vaults. Debt in USD (peg=USD assumed)."""
    rng=np.random.default_rng(seed)
    icr=np.maximum(2.0,icr0*np.exp(rng.normal(0,0.15,(NP,NV))))  # ASSUMED spread
    d=np.full((NP,NV),1.0/NV); c=icr*d/1.0                       # KAS units, P0=1
    c0=c.copy(); alive=np.ones((NP,NV),bool)
    fee=dict(stab=np.zeros(NP),liq=np.zeros(NP),red=np.zeros(NP)); fee_kas=np.zeros((NP,T))
    bad=np.zeros(NP); liqdebt=np.zeros(NP); avgdebt=np.zeros(NP); resid=np.zeros((NP,NV)); liqd=np.zeros((NP,NV),bool)
    stabKAS_tot=np.zeros(NP)
    for t in range(T):
        p=P[:,t][:,None]
        # stability fee (KAS, lazily accrued, paid from collateral)
        sf=np.minimum(r/365*d/p,c); c=c-sf; fee['stab']+=(sf*p).sum(1); fee_kas[:,t]+=sf.sum(1)
        # redemption, lowest ICR first (min ICR 100%)
        if q>0:
            a=q/365*1.0
            ic=np.where(alive&(d>0),c*p/np.maximum(d,1e-18),9e9); ic=np.where(ic<1.0,9e9,ic)
            o=np.argsort(ic,axis=1); ds=np.take_along_axis(np.where(ic<9e9,d,0),o,1)
            cum=np.cumsum(ds,1)-ds; tk=np.clip(a-cum,0,ds); take=np.zeros_like(d); np.put_along_axis(take,o,tk,1)
            take=np.minimum(take,c*p)
            ck=take/p; d=d-take; c=c-ck; fee['red']+=RED*take.sum(1); fee_kas[:,t]+=RED*ck.sum(1)
        # liquidation
        icr_now=np.where(d>1e-15,c*p/np.maximum(d,1e-18),9e9)
        L=alive&(d>1e-15)&(icr_now<MCR)
        if L.any():
            V=c*p; f=LIQ*V; net=V-f; sh=np.maximum(d-net,0)
            fee['liq']+=(f*L).sum(1); fee_kas[:,t]+=((f/p)*L).sum(1)
            bad+=(sh*L).sum(1); liqdebt+=(d*L).sum(1)
            resid=np.where(L,np.maximum(net-d,0),resid); liqd|=L
            d=np.where(L,0,d); c=np.where(L,0,c); alive&=~L
        alive&=d>1e-15
        avgdebt+=d.sum(1)/T
    # borrower wealth delta without y (per unit of D0=1/NV each vault): see report s.borrower
    PT=P[:,-1][:,None]
    hold=c0*PT
    wealth=np.where(liqd,resid,c*PT-d)+ (1.0/NV)   # + D0 invested at y=0 (principal); y adds D0*y
    # alive-but-fully-redeemed vaults: formula c*PT-d holds (d=0)
    delta0=(wealth-hold)/(1.0/NV)    # per unit of vault debt, USD at end, excluding y*D0
    delta0_mean=delta0.mean(1)
    # median ICR at end among alive
    icr_end=np.where(alive,c*PT/np.maximum(d,1e-18),np.nan)
    return dict(stab=fee['stab']/avgdebt,liq=fee['liq']/avgdebt,red=fee['red']/avgdebt,
        avgdebt=avgdebt,bad=bad,liqfrac=liqdebt,fee_kas=fee_kas,delta0=delta0_mean,
        liq_share_vaults=liqd.mean(1),icr_end=np.nanmedian(icr_end,axis=1),
        fee_usd=(fee['stab']+fee['liq']+fee['red']), fee_kas_mtm=(fee_kas*P[:,-1][:,None]).sum(1),
        fee_usd_t=None)
if __name__=='__main__':
    res={}
    PS={g:paths(g,100+i) for i,g in enumerate(REG)}
    ret={g:(PS[g][:,-1]-1) for g in REG}
    calib['sim_ret_pct']={g:{q:float(np.percentile(ret[g],q)*100) for q in (10,50,90)} for g in REG}
    for g in REG:
        for r,qr,ic in itertools.product([0,.01,.02,.03,.05],[0,.02,.10],[2.0,2.5,3.0]):
            o=run(PS[g],r,qr,ic)
            m=lambda k:float(np.mean(o[k]))
            fee_usd_t=o['fee_usd']   # per D0=1 total
            # fee KAS MTM vs receipt
            res[f'{g}|{r}|{qr}|{ic}']=dict(stab=m('stab'),liq=m('liq'),red=m('red'),avgdebt=m('avgdebt'),
              bad=m('bad'),liqdebt=m('liqfrac'),
              liq_vault_share=m('liq_share_vaults'),icr_end=float(np.mean(o['icr_end'])),
              delta0=m('delta0'),delta0_p10=float(np.percentile(o['delta0'],10)),
              fee_usd_over_debt_p10=float(np.percentile((o['stab']+o['liq']+o['red']),10)),
              fee_usd_over_debt_p90=float(np.percentile((o['stab']+o['liq']+o['red']),90)),
              # junior MTM: non-mint fees paid in KAS, valued at year end, per avg debt
              fee_mtm=float(np.mean(o['fee_kas_mtm']/o['avgdebt'])),
              fee_rcpt=float(np.mean((o['stab']+o['liq']+o['red']))),
              fee_mtm_p10=float(np.percentile(o['fee_kas_mtm']/o['avgdebt'],10)),
              corr_ret=float(np.corrcoef(ret[g],o['stab']+o['liq']+o['red'])[0,1]) if (r+qr)>0 else None,
              bad_p90=float(np.percentile(o['bad'],90)),bad_max=float(o['bad'].max()))
    json.dump(dict(calib=calib,res=res),open(OUT+f'/results_vs{VS}.json','w'),indent=1)
    print(json.dumps(calib,indent=1))
