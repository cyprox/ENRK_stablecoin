"""Why: reconstruct the ENRK peg index historically with the project formula and compare with KAS/USD (task A4 part 3).
Inputs: ../daily.csv (from build_dataset.py). Outputs: ../out/*.csv, ../out/history_summary.json. numpy only."""
import csv, json, os, sys, datetime as dt
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.join(HERE,'..'); OUT=os.path.join(ROOT,'out'); os.makedirs(OUT,exist_ok=True)
rows=list(csv.DictReader(open(ROOT+'/daily.csv')))
def col(k):
    x=np.array([float(r[k]) if r[k] not in ('','None') else np.nan for r in rows])
    # forward-fill (monthly energy has no value for the latest month)
    for i in range(1,len(x)):
        if np.isnan(x[i]): x[i]=x[i-1]
    return x
dates=[dt.date.fromisoformat(r['date']) for r in rows]
K=col('kas'); H=col('hashrate_PHs'); TX=col('tx_regular'); AD=col('active_addr_hoursum'); EN=col('energy_idx'); EL=col('elec_usd_kwh')
def trail(x,n):  # trailing mean (no look-ahead)
    c=np.cumsum(np.insert(x,0,0)); out=np.empty_like(x)
    for i in range(len(x)):
        j=max(0,i-n+1); out[i]=(c[i+1]-c[j])/(i+1-j)
    return out
F=trail(TX,7)      # stand-in for weekly fees (docs: weekly 7d aggregation)
A=trail(AD,30)     # stand-in for adoption (docs: monthly)
W=dict(h=.40,e=.30,f=.20,a=.10)
clip=lambda x,lo=.1,hi=5.: np.minimum(np.maximum(x,lo),hi)
def baseline(x,mode):
    if mode=='launch': return np.full_like(x,x[:7].mean())          # first week of window (docs: protocol launch / first week)
    if mode=='fullmean': return np.full_like(x,x.mean())            # hindsight "historical average" (kaspa_adapter comment)
    if mode=='trail365':
        b=trail(x,365); return b                                    # my construction, not in code
def peg(mode,energy='idx',proxies='full'):
    e=EN if energy=='idx' else EL
    comps=dict(h=clip(H/baseline(H,mode)),e=clip(e/baseline(e,mode)),f=clip(F/baseline(F,mode)),a=clip(A/baseline(A,mode)))
    if proxies=='HE': comps['f']=np.ones_like(H); comps['a']=np.ones_like(H)   # fees/adoption proxies are spam-contaminated -> held at 1.0
    raw=sum(W[k]*comps[k] for k in W)
    return clip(raw),comps,raw
S={}
def stats(name,I,start=0,ret_lag=7):
    k=np.log(K[start:]); i=np.log(I[start:]); n=len(k)
    dk=np.diff(k); di=np.diff(i)
    wk=k[ret_lag::ret_lag]-k[:-ret_lag:ret_lag][:len(k[ret_lag::ret_lag])]; wi=i[ret_lag::ret_lag]-i[:-ret_lag:ret_lag][:len(i[ret_lag::ret_lag])]
    m=min(len(wk),len(wi)); wk,wi=wk[:m],wi[:m]
    r={}
    r['n_days']=n; r['start']=str(dates[start]); r['end']=str(dates[-1])
    r['vol_ann_KAS_daily']=float(dk.std(ddof=1)*np.sqrt(365)); r['vol_ann_index_daily']=float(di.std(ddof=1)*np.sqrt(365))
    r['vol_ann_KAS_weekly']=float(wk.std(ddof=1)*np.sqrt(52)); r['vol_ann_index_weekly']=float(wi.std(ddof=1)*np.sqrt(52))
    r['corr_daily_ret']=float(np.corrcoef(dk,di)[0,1]); r['corr_weekly_ret']=float(np.corrcoef(wk,wi)[0,1])
    r['corr_log_levels']=float(np.corrcoef(k,i)[0,1])
    # 30-day horizon overlapping returns
    h=30; k30=k[h:]-k[:-h]; i30=i[h:]-i[:-h]
    r['corr_30d_ret']=float(np.corrcoef(k30,i30)[0,1])
    r['mean_ann_log_ret_index']=float(di.mean()*365); r['mean_ann_log_ret_KAS']=float(dk.mean()*365)
    r['index_first']=float(I[start]); r['index_last']=float(I[-1]); r['index_min']=float(I[start:].min()); r['index_max']=float(I[start:].max())
    r['frac_days_index_outside_0.89_1.11']=float(np.mean((I[start:]<0.89)|(I[start:]>1.11)))
    # rolling 90d corr of weekly returns
    rc=[]
    for s in range(0,len(wk)-13):
        a,b=wk[s:s+13],wi[s:s+13]
        if a.std()>0 and b.std()>0: rc.append(np.corrcoef(a,b)[0,1])
    rc=np.array(rc); r['rolling_13w_corr_min_med_max']=[float(rc.min()),float(np.median(rc)),float(rc.max())]; r['rolling_13w_corr_frac_negative']=float(np.mean(rc<0))
    # opposite direction
    r['frac_days_opposite_sign']=float(np.mean(np.sign(dk)!=np.sign(di)))  # note: index is smooth, many zero days
    nz=(di!=0)&(dk!=0); r['frac_days_opposite_sign_nonzero']=float(np.mean(np.sign(dk[nz])!=np.sign(di[nz])))
    r['frac_weeks_opposite_sign']=float(np.mean(np.sign(wk)!=np.sign(wi)))
    r['frac_30d_opposite_sign']=float(np.mean(np.sign(k30)!=np.sign(i30)))
    r['frac_30d_adverse_idx_up_KAS_down']=float(np.mean((i30>0)&(k30<0)))
    r['frac_30d_adverse_idx_up5_KAS_down10']=float(np.mean((i30>np.log(1.05))&(k30<np.log(.9))))
    r['frac_30d_favourable_idx_down_KAS_up']=float(np.mean((i30<0)&(k30>0)))
    # lead/lag on weekly returns: corr(KAS_t , I_{t+lag}) lag>0 means KAS leads index
    ll={}
    for lag in range(-6,7):
        if lag>=0: a,b=wk[:len(wk)-lag],wi[lag:]
        else: a,b=wk[-lag:],wi[:len(wi)+lag]
        ll[lag]=float(np.corrcoef(a,b)[0,1])
    r['leadlag_weekly_KASlead_positive']=ll
    # worst KAS drawdown episodes (peak-to-trough)
    P=K[start:]; peak=np.maximum.accumulate(P); dd=P/peak-1
    eps=[]; i0=0; inep=False
    for t in range(len(P)):
        if dd[t]==0:
            if inep and (P[tp]/P[pk]-1)<-0.4: eps.append((pk,tp))
            inep=False; pk=t
        else:
            if not inep or P[t]<P[tp]: tp=t
            inep=True
    if inep and (P[tp]/P[pk]-1)<-0.4: eps.append((pk,tp))
    eps=sorted(eps,key=lambda e:P[e[1]]/P[e[0]])[:6]
    er=[]
    for pk,tp in eps:
        a=start+pk; b=start+tp
        kk=np.diff(np.log(K[a:b+1])); ii=np.diff(np.log(I[a:b+1]))
        c=float(np.corrcoef(kk,ii)[0,1]) if len(kk)>5 and ii.std()>0 else None
        er.append(dict(peak=str(dates[a]),trough=str(dates[b]),days=b-a,kas_change=float(K[b]/K[a]-1),index_change=float(I[b]/I[a]-1),corr_daily=c,
                       icr_ratio_vs_open=float((K[b]/K[a])/(I[b]/I[a]))))
    r['worst_kas_drawdowns']=er
    return r
def icr_study(name,I,start,horizons=(90,180,365),icr0=2.0,mcr=1.5):
    res={}
    n=len(K)
    for hz in horizons:
        mins=[];minsK=[];fin=[]
        for s in range(start,n-hz):
            rel=(K[s:s+hz+1]/K[s])/(I[s:s+hz+1]/I[s]); relK=K[s:s+hz+1]/K[s]
            mins.append(icr0*rel.min()); minsK.append(icr0*relK.min()); fin.append(icr0*rel[-1])
        mins=np.array(mins);minsK=np.array(minsK);fin=np.array(fin)
        res[hz]=dict(n_starts=len(mins),frac_hit_MCR_joint=float(np.mean(mins<mcr)),frac_hit_MCR_KASonly=float(np.mean(minsK<mcr)),
            frac_hit_MCR_joint_not_KASonly=float(np.mean((mins<mcr)&(minsK>=mcr))),frac_hit_MCR_KASonly_not_joint=float(np.mean((mins>=mcr)&(minsK<mcr))),
            frac_below_100_joint=float(np.mean(mins<1.0)),frac_below_100_KASonly=float(np.mean(minsK<1.0)),
            median_min_ICR_joint=float(np.median(mins)),median_min_ICR_KASonly=float(np.median(minsK)),
            p10_min_ICR_joint=float(np.percentile(mins,10)),p10_min_ICR_KASonly=float(np.percentile(minsK,10)))
    return res
allres={}
# 1) code-literal launch baseline: show saturation
for proxies in ('HE','full'):
  for energy in ('idx','elec'):
    for mode in ('launch','fullmean','trail365'):
        I,c,raw=peg(mode,energy,proxies)
        start=0 if mode!='trail365' else 365
        key=f'{mode}|energy={energy}|proxies={proxies}'
        r=stats(key,I,start); r['icr']=icr_study(key,I,start)
        r['frac_days_component_at_clip_5']={k:float(np.mean(v[start:]>=5.0)) for k,v in c.items()}
        r['frac_days_component_at_clip_0.1']={k:float(np.mean(v[start:]<=0.1)) for k,v in c.items()}
        r['frac_days_total_at_clip_5']=float(np.mean(I[start:]>=5.0))
        allres[key]=r
        with open(f'{OUT}/index_{mode}_{energy}_{proxies}.csv','w') as f:
            f.write('date,kas,index,h,e,f,a\n')
            for t in range(len(K)): f.write(f'{dates[t]},{K[t]},{I[t]:.5f},{c["h"][t]:.4f},{c["e"][t]:.4f},{c["f"][t]:.4f},{c["a"][t]:.4f}\n')
# 2) component-level stats on log returns (full window, unscaled) for scenario calibration
comp={}
for nm,x in (('hashrate',H),('energy_idx',EN),('electricity',EL),('fees_proxy_tx7d',F),('adoption_proxy_ad30d',A),('KAS',K)):
    lx=np.log(x); d1=np.diff(lx); w=lx[7::7]-lx[:-7:7][:len(lx[7::7])]
    comp[nm]=dict(vol_ann_daily=float(d1.std(ddof=1)*np.sqrt(365)),vol_ann_weekly=float(w.std(ddof=1)*np.sqrt(52)),mean_ann_log=float(d1.mean()*365),
                  first=float(x[0]),last=float(x[-1]),corr_weekly_with_KAS=float(np.corrcoef(w[:len(w)],(np.log(K)[7::7]-np.log(K)[:-7:7])[:len(w)])[0,1]))
allres['components']=comp
json.dump(allres,open(OUT+'/history_summary.json','w'),indent=1)
for k,v in allres.items():
    if k=='components': continue
    print(k, {x:round(v[x],3) for x in ('vol_ann_KAS_weekly','vol_ann_index_weekly','corr_weekly_ret','corr_30d_ret','corr_log_levels','frac_30d_opposite_sign','frac_30d_adverse_idx_up_KAS_down','frac_days_index_outside_0.89_1.11','index_min','index_max')}, [round(x,2) for x in v['rolling_13w_corr_min_med_max']], v['frac_days_component_at_clip_5'])
