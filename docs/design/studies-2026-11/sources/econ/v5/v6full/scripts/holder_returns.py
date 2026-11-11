"""Why: distribution of ENRK holder USD return (= index change, with L=$1/unit constant) over rolling windows of the reconstructed index
and of the energy-only legs. numpy only; reads out/index_*.csv and raw FRED csv."""
import csv, numpy as np, json, os
H=os.path.dirname(os.path.abspath(__file__)); O=H+'/../out'; R=H+'/../raw'
res={}
for f in ['trail365_idx_HE','fullmean_idx_HE','launch_idx_HE','trail365_elec_HE','trail365_idx_full','fullmean_idx_full']:
    rows=list(csv.DictReader(open(f'{O}/index_{f}.csv'))); I=np.array([float(r['index']) for r in rows]); K=np.array([float(r['kas']) for r in rows])
    if f.startswith('trail'): I,K=I[365:],K[365:]
    d={}
    for w in (90,365):
        r=I[w:]/I[:-w]-1; rk=K[w:]/K[:-w]-1
        d[w]=dict(n=len(r),p5=float(np.percentile(r,5)),p25=float(np.percentile(r,25)),median=float(np.median(r)),p75=float(np.percentile(r,75)),p95=float(np.percentile(r,95)),
                  frac_neg=float((r<0).mean()),KAS_median=float(np.median(rk)),KAS_p5=float(np.percentile(rk,5)),KAS_p95=float(np.percentile(rk,95)),
                  borrower_icr_ratio_median=float(np.median((1+rk)/(1+r))), frac_icr_ratio_below_075=float(np.mean(((1+rk)/(1+r))<0.75)))
    res[f]=d
def load(id):
    return [(l.split(',')[0],float(l.split(',')[1])) for l in open(f'{R}/fred_{id}.csv').read().split('\n')[1:] if l.strip() and l.split(',')[1] not in ('','.')]
for id in ('PNRGINDEXM','APU000072610'):
    x=np.array([v for _,v in load(id)]); r=x[12:]/x[:-12]-1
    res['12m_'+id]=dict(n=len(r),p5=float(np.percentile(r,5)),median=float(np.median(r)),p95=float(np.percentile(r,95)),min=float(r.min()),max=float(r.max()),frac_neg=float((r<0).mean()))
json.dump(res,open(O+'/holder_returns.json','w'),indent=1)
for k,v in res.items(): print(k, json.dumps(v)[:700])
