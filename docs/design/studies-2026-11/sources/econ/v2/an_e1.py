from an_common import *
import sys
d=load('E1')['res']
print('E1 baseline liquidity shock, no policy (300 runs/cell). Metric means over cells of grid.')
def agg(sel, label):
    r=[x for x in d if sel(x['cell'])]
    for k in ['maxdep','area','d99','d95']:
        pass
    v={k:np.mean([x['m'][k].mean() for x in r]) for k in ['maxdep','area','d99','d98','d95']}
    return label, len(r), v
for var,vals in [('f',[.1,.2,.3]),('D',[1,2,4]),('Ka',[.02,.05,.15]),('c',[.0025,.005,.01]),('kappa',[.01,.03,.08])]:
    print('\nby',var)
    print('| %s | cells | max depth pts | area pt-days | days<99%% | days<98%% | days<95%% |'%var); print('|---|---|---|---|---|---|---|')
    for v in vals:
        l,n,m=agg(lambda c:c[var]==v, v)
        print('| %s | %d | %.2f | %.0f | %.1f | %.1f | %.1f |'%(v,n,100*m['maxdep'],m['area'],m['d99'],m['d98'],m['d95']))
print('\ncentral cell (D2 Ka.05 c.005 kappa.03) by f')
for f in [.1,.2,.3]:
    x=[x for x in d if x['cell']['f']==f and x['cell']['D']==2 and x['cell']['Ka']==.05 and x['cell']['c']==.005 and x['cell']['kappa']==.03][0]['m']
    print(f, 'maxdep %.2f pts [p5 %.2f p95 %.2f] area %.0f days<99 %.1f days<95 %.1f'%(100*x['maxdep'].mean(),100*np.quantile(x['maxdep'],.05),100*np.quantile(x['maxdep'],.95),x['area'].mean(),x['d99'].mean(),x['d95'].mean()))
