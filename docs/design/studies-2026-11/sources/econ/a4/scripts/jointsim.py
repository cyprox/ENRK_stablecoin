"""Why: joint (peg index, KAS price) vault-population model: extra liquidation / unbacked-debt risk from index drift vs KAS-only crash,
with clip bounds and circuit-breaker variants (task A4 part 4). Deliberately simple; every number is a model output, not a forecast.
numpy only. Usage: python3 jointsim.py [paths] [n_vaults]   Seeded: results reproducible."""
import numpy as np, json, sys, os, itertools
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','out'); os.makedirs(OUT,exist_ok=True)
PATHS=int(sys.argv[1]) if len(sys.argv)>1 else 300
NV=int(sys.argv[2]) if len(sys.argv)>2 else 1200
T=60                       # crash horizon in days (as stress_test_crash.py)
MCR=1.5; ICR0=2.0; ICR_SPREAD=0.22; CAP=0.05      # CAP: daily liquidation capacity as share of opening debt value (repo value, r4 note)
SIG_K=0.049                # KAS daily close-to-close sd (MEASURED r4-market.md, KuCoin 1285 d)
JUMP_P=0.02; JUMP_SZ=-0.20 # ASSUMED jump overlay (repo uses 4%/day of -25% in crash); terminal drawdown is forced by drift correction
FLOOR=0.75; LIQ_BASE=0.04; LIQ_SLOPE=0.18          # FROZEN_PARAMETERS s4: demand 4%+18%*drawdown, floor 75%
def make_paths(rng,dk_target,ln_I_T,sig_I_ann,rho,jump=True):
    """KAS log path forced to end at ln(1-dk_target); index log path (pre-clip) bridged to ln_I_T with noise correlated rho to KAS noise."""
    zk=rng.standard_normal(T); nk=SIG_K*zk
    if jump: nk=nk+(rng.random(T)<JUMP_P)*JUMP_SZ
    nk=nk-nk.mean()                                  # zero-sum noise, then add linear drift to hit target
    lk=np.cumsum(nk)+np.arange(1,T+1)*(np.log(1-dk_target)/T)
    lk=lk-(lk[-1]-np.log(1-dk_target))*np.arange(1,T+1)/T      # exact terminal
    sd=sig_I_ann/np.sqrt(365)
    zi=rho*zk+np.sqrt(1-rho**2)*rng.standard_normal(T); ni=sd*zi; ni=ni-ni.mean()
    li=np.cumsum(ni); li=li-(li[-1])*np.arange(1,T+1)/T + np.arange(1,T+1)*(ln_I_T/T)
    return np.exp(lk),np.exp(li)        # K_t/K_0 , I_t/I_0 (I_0 = 1.0 = index at open)
def run_path(rng,K,I,lo,hi,breaker=None,q_oracle=0.0,idx_mode='clip'):
    """breaker: None | 'liq_halt' (pause halts liquidations when trunc(|I-1|*100)>10) | 'liq_continue' (pause has no effect on liquidations)
    q_oracle: daily hazard that oracle outage >6h trips the pause (halts liquidations) -- ASSUMED."""
    I=np.clip(I,lo,hi)
    icr0=np.maximum(ICR0*np.exp(ICR_SPREAD*rng.standard_normal(NV)),MCR*1.02)
    size=np.exp(rng.standard_normal(NV)*0.8); size/=size.sum()            # debt weights (open), sum=1 => opening debt value = 1.0 (USD at open)
    # collateral value at open = icr0*size ; debt value at t = size*I_t ; collateral value at t = icr0*size*K_t
    alive=np.ones(NV,bool); real_short=0.0; liq_debt=0.0; paused=False; by_idx=False; peakK=1.0
    for t in range(T):
        k=K[t]; i=I[t]; peakK=max(peakK,k)
        if not paused:
            if breaker and int(abs(i-1.0)*100)>10: paused=True; by_idx=True
            elif q_oracle>0 and rng.random()<q_oracle: paused=True; by_idx=False
        halt=paused and ((by_idx and breaker=='liq_halt') or (not by_idx))   # oracle-downtime pause assumed to halt liquidations
        if halt: continue
        icr=icr0*k/i
        cand=np.where(alive&(icr<MCR))[0]
        if len(cand)==0: continue
        cand=cand[np.argsort(icr[cand])]
        capleft=CAP          # USD collateral value that can be sold per day = CAP x opening debt value (=1.0)
        dd=1-k/peakK; disc=min(1-FLOOR,LIQ_BASE+LIQ_SLOPE*dd)
        for v in cand:
            cv=icr0[v]*size[v]*k          # collateral USD value now
            if cv>capleft: break          # whole-vault auctions only; wait for next day
            capleft-=cv
            proceeds=cv*(1-disc); debt=size[v]*i
            real_short+=max(0.0,debt-proceeds); liq_debt+=size[v]; alive[v]=False
    # end of horizon: latent shortfall on vaults still alive, marked as liquidated at final discount
    k=K[-1]; i=I[-1]; dd=1-k/max(peakK,1.0); disc=min(1-FLOOR,LIQ_BASE+LIQ_SLOPE*dd)
    cv=icr0*size*k; debt=size*i
    latent=np.maximum(0.0,debt-cv*(1-disc))[alive].sum()
    stuck=((icr0*k/i<MCR)&alive)
    return dict(unbacked=(real_short+latent), realised=real_short, latent=latent, liq_share=liq_debt, stuck_share=float(size[stuck].sum()),
                insolvent_share=float(size[alive&(icr0*k/i<1.0)].sum()), paused=paused, I_T=float(i))
def cell(dk,I_T,sig_I,rho,lo=0.1,hi=5.0,breaker=None,q=0.0,seed=1,paths=None,ln_raw=True):
    rng=np.random.default_rng(seed); n=paths or PATHS; res=[]
    for p in range(n):
        K,I=make_paths(rng,dk,np.log(I_T),sig_I,rho)
        res.append(run_path(rng,K,I,lo,hi,breaker,q))
    g=lambda k:np.array([r[k] for r in res],float)
    return dict(unbacked_mean=float(g('unbacked').mean()),unbacked_p95=float(np.percentile(g('unbacked'),95)),p_hole_gt5=float(np.mean(g('unbacked')>0.05)),
                liq_mean=float(g('liq_share').mean()),stuck_mean=float(g('stuck_share').mean()),insolvent_mean=float(g('insolvent_share').mean()),paused=float(g('paused').mean()),I_T_mean=float(g('I_T').mean()))
if __name__=='__main__':
    R={}
    DK=[0.30,0.50,0.70,0.85]; IT=[0.6,0.8,1.0,1.25,1.5,2.0,3.0,5.0,8.0]
    # A. grid, deterministic-terminal index, index noise 25% ann (hist 19-26% in HE variants), rho 0
    R['grid']={f'{dk}|{it}':cell(dk,it,0.25,0.0,seed=11) for dk in DK for it in IT}
    # B. clip sensitivity at the extreme: raw index 8x / 3x / 2x with different [lo,hi]
    R['clip']={}
    for lo,hi in [(0.1,5.0),(0.5,2.0),(0.8,1.25)]:
        for dk in (0.50,0.70):
            for it in (0.5,1.0,2.0,3.0,8.0):
                R['clip'][f'[{lo},{hi}]|{dk}|{it}']=cell(dk,it,0.25,0.0,lo=lo,hi=hi,seed=12)
    # C. circuit breaker variants (index tripping rule as coded: |I-1|>10% truncated), oracle hazard 1%/day
    R['breaker']={}
    for dk in (0.50,0.70):
        for it in (0.8,1.0,1.5,2.0):
            for name,b,q in [('none',None,0.0),('idx_trip_halts_liq','liq_halt',0.0),('idx_trip_liq_continue','liq_continue',0.0),('oracle1pct_halts_liq',None,0.01),('oracle5pct_halts_liq',None,0.05)]:
                R['breaker'][f'{name}|{dk}|{it}']=cell(dk,it,0.25,0.0,breaker=b,q=q,seed=13)
    # D. statistical joint draws: KAS terminal from a crash grid, index terminal ~ lognormal with correlation rho to KAS terminal log-return
    R['joint']={}
    rng=np.random.default_rng(99)
    for sig in (0.25,0.55):                      # annual index vol: HE-variant (hist 19-26%) / full-proxy variant (hist 55%+)
        for rho in (-0.5,0.0,0.3,0.6):           # corr(KAS, index) of 60d returns
            for dk in DK:
                lkT=np.log(1-dk); sK=SIG_K*np.sqrt(T)   # std of KAS 60d log-return, used to standardise
                zK=(lkT-(-0.0))/sK                       # crash is given: conditional mean of index move
                mu_cond=rho*(sig*np.sqrt(T/365))*zK*0.5   # conditional mean uses half-weight (crash tail partly idiosyncratic) -- ASSUMED shrink
                sd_cond=sig*np.sqrt(T/365)*np.sqrt(1-rho**2)
                n=PATHS; res=[]
                for p in range(n):
                    lI=mu_cond+sd_cond*rng.standard_normal()
                    K,I=make_paths(rng,dk,lI,sig,rho)
                    res.append(run_path(rng,K,I,0.1,5.0))
                g=lambda k:np.array([r[k] for r in res],float)
                R['joint'][f'sig{sig}|rho{rho}|{dk}']=dict(unbacked_mean=float(g('unbacked').mean()),p_hole_gt5=float(np.mean(g('unbacked')>0.05)),liq_mean=float(g('liq_share').mean()),I_T_mean=float(g('I_T').mean()),mu_cond=float(mu_cond))
    # E. named scenarios: component terminal multipliers (H,E,F,A) -> index by project formula, with KAS terminal change
    W=(0.4,0.3,0.2,0.1); idx=lambda h,e,f,a: min(max(sum(w*min(max(x,0.1),5.0) for w,x in zip(W,(h,e,f,a))),0.1),5.0)
    r=lambda x: x
    NAMED={'N0 KAS-only (index flat, existing simulators)':(0.70,(1,1,1,1)),
     'N1 stress_test_crash elasticities (H r^.4, F r^.6, A r^.3, E=1), KAS -70%':(0.70,(0.3**0.4,1,0.3**0.6,0.3**0.3)),
     'N1b same, KAS -85%':(0.85,(0.15**0.4,1,0.15**0.6,0.15**0.3)),
     'N2 energy x2, others flat, KAS -50%':(0.50,(1,2.0,1,1)),
     'N3 doc scenario 3 energy crisis (H.85,E4,F1.05,A.95), KAS -70%':(0.70,(0.85,4.0,1.05,0.95)),
     'N4 hashrate collapse -70%, fees -50%, adoption -30%, KAS -70%':(0.70,(0.3,1,0.5,0.7)),
     'N5 hashrate -60%, energy x1.5, fees -50%, adoption -20%, KAS -70%':(0.70,(0.4,1.5,0.5,0.8)),
     'N6 index up while KAS falls (H1.5,E1.3,F2,A1.3), KAS -60%':(0.60,(1.5,1.3,2.0,1.3)),
     'N7 doc scenario 2 bull (H4,E1.1,F5,A1.8), KAS x3':(-2.0,(4,1.1,5,1.8)),
     'N8 doc scenario 1 PoW ban (H.6,E1.15,F.5,A.9), KAS -60%':(0.60,(0.6,1.15,0.5,0.9)),
     'N9 favourable: index -30% via H -50%/F -50%... (H.5,E1,F.5,A1), KAS flat':(0.0,(0.5,1,0.5,1)),
     'N10 favourable: KAS +50%, index flat':(-0.5,(1,1,1,1))}
    R['named']={}
    for name,(dk,c) in NAMED.items():
        it=idx(*c)
        for brk,q,label in [(None,0.0,'no breaker'),('liq_halt',0.0,'idx breaker halts liq')]:
            v=cell(dk,it,0.25,0.0,breaker=brk,q=q,seed=14); v['I_T']=it; v['dk']=dk
            R['named'][f'{name} || {label}']=v
    json.dump(R,open(OUT+'/jointsim_results.json','w'),indent=1)
    print('done',len(R['grid']),len(R['clip']),len(R['breaker']),len(R['joint']))
