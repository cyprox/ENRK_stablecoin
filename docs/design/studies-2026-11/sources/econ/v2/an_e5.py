from an_common import *
d=load('E5')['res']
def sel(**kw): return [x for x in d if all(x['cell'].get(k)==v for k,v in kw.items())]
cfgs=['a_none','f_absorb','d_ORA','d_then_absorb','d_fence50_absorb','c_y50','c_then_absorb','b_ORA']
def line(x):
    m=x['m']; return '%.1f [%.1f-%.1f] | %.0f | %.1f | %.1f | %.2f | %.2f | %.2f'%(100*m['maxdep'].mean(),100*np.quantile(m['maxdep'],.05),100*np.quantile(m['maxdep'],.95),m['d95'].mean(),100*m['ell_net'].mean(),100*m['Send'].mean(),100*m['spent'].mean(),100*m['Rshock'].mean(),100*m['Rmin_after'].mean())
H='| config | max depth pts [p5-p95] | days<95%% | residual ENRK loss pts of debt | debt (supply) left pts | reserve spent pts | reserve at shock pts | lowest reserve ratio after shock pts |'
print('### E5 solvency shock (collateral shortfall l, T3 loss levels: 2.07=orig85 mean unbacked, 3.0=orig85 ENRK p95, 10.2=flat85 mean, 13.8=flat85 p95, 19.6=x2 mean, 26.5=x3 mean). Shock at day ~365, reserve inflow g/yr, 300 runs/cell. "l" is % of debt; residual = shortfall left on ENRK holders after the reserve (pro rata).')
for rec in [0.5,0.0]:
  for g in [.06,.12,.03]:
    print('\n#### recoverable share rec=%s, g=%s/yr'%(rec,g)); 
    for ell in [.02,.03,.10,.14,.20,.26]:
        print('\nl = %.0f%%'%(100*ell)); print(H); print('|---|---|---|---|---|---|---|---|')
        for c in cfgs:
            x=sel(tag='E5',pname=c,ell=ell,g=g,rec=rec)[0]; print('| %s | %s |'%(c,line(x)))
print('\n### E5fence: liquidity shock f=30%% at ~day 365, then solvency l at +90 d; d_ORA yield (ymax 50%%) with a ring-fence nu of the cumulative inflow untouchable by incentives; absorption uses all reserve; g=6%%')
print('| l | nu | max depth pts | days<95%% | residual ENRK loss pts | reserve spent on incentives pts | lowest reserve ratio after shock pts |'); print('|---|---|---|---|---|---|---|')
for ell in [.03,.10,.20]:
    for nu in [0,.25,.5,.75,1.0]:
        m=sel(tag='E5fence',ell=ell,nu=nu)[0]['m']; print('| %.0f%% | %.2f | %.1f | %.0f | %.2f | %.2f | %.2f |'%(100*ell,nu,100*m['maxdep'].mean(),m['d95'].mean(),100*m['ell_net'].mean(),100*m['spent'].mean(),100*m['Rmin_after'].mean()))
print('\n### E5seq: liquidity shock f=30%% then solvency l after dsol days (g=6%%): configs')
for ell in [.03,.10,.20]:
    for dsol in [30,90,180]:
        print('\nl=%.0f%% dsol=%d'%(100*ell,dsol)); print(H); print('|---|---|---|---|---|---|---|---|')
        for c in cfgs:
            x=sel(tag='E5seq',pname=c,ell=ell,dsol=dsol)[0]; print('| %s | %s |'%(c,line(x)))
