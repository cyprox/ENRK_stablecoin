"""Why: long-run drift/vol/jumps of the energy proxies (FRED monthly) to calibrate the energy leg of joint scenarios. numpy only."""
import numpy as np, datetime as dt, os, json
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','raw')
def load(id):
    out=[]
    for l in open(f'{R}/fred_{id}.csv').read().split('\n')[1:]:
        if l.strip() and l.split(',')[1] not in ('','.'): out.append((l.split(',')[0],float(l.split(',')[1])))
    return out
res={}
for id in ('PNRGINDEXM','APU000072610','POILBREUSDM'):
    d=load(id); x=np.array([v for _,v in d]); r=np.diff(np.log(x))
    res[id]=dict(first=d[0],last=d[-1],n_months=len(d),drift_ann_log=float(r.mean()*12),vol_ann=float(r.std(ddof=1)*np.sqrt(12)),
        worst_month=float(r.min()),best_month=float(r.max()),
        worst_12m=float(min(np.log(x[i+12]/x[i]) for i in range(len(x)-12))),best_12m=float(max(np.log(x[i+12]/x[i]) for i in range(len(x)-12))),
        n_months_abs_gt_15pct=int((abs(r)>.15).sum()),
        frac_12m_up_gt_50pct=float(np.mean([x[i+12]/x[i]>1.5 for i in range(len(x)-12)])))
    # since 2021
    d21=[v for k,v in d if k>='2021-01-01']; r21=np.diff(np.log(d21)); res[id]['since2021_drift_ann_log']=float(r21.mean()*12); res[id]['since2021_vol_ann']=float(r21.std(ddof=1)*np.sqrt(12))
a=dict(load('PNRGINDEXM')); b=dict(load('APU000072610')); ks=sorted(set(a)&set(b))
ra=np.diff(np.log([a[k] for k in ks])); rb=np.diff(np.log([b[k] for k in ks])); res['corr_energyidx_vs_retail_elec_monthly']=float(np.corrcoef(ra,rb)[0,1])
# peak move within 2021-2022
e=[(k,v) for k,v in load('PNRGINDEXM') if '2021-01-01'<=k<='2023-03-01']; res['energy_idx_2021_2023']=dict(min=min(e,key=lambda t:t[1]),max=max(e,key=lambda t:t[1]))
json.dump(res,open(os.path.join(R,'..','out','energy_stats.json'),'w'),indent=1,default=str); print(json.dumps(res,indent=0,default=str))
