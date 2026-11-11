from an_common import *
D=load('E4'); d=D['res']; T=D['T']
def sel(**kw): return [x for x in d if all(x['cell'].get(k)==v for k,v in kw.items())]
def stat(xs,scen):
    b=[x for x in d if x['cell']['scen']==scen and x['cell']['pname']=='a_none'][0]['m']
    o={}
    o['rmax_mean']=100*np.mean([x['m']['rmaxseen'].mean() for x in xs]); o['rmax_p95']=100*np.mean([np.quantile(x['m']['rmaxseen'],.95) for x in xs])
    o['sd_logr']=np.mean([np.sqrt(np.maximum(0,x['m']['rsq']/T-(x['m']['rsum']/T)**2)).mean() for x in xs])
    o['flips_yr']=np.mean([x['m']['flips'].mean() for x in xs])/(T/365); o['active']=100*np.mean([x['m']['active_days'].mean() for x in xs])/T
    o['extra_int']=100*np.mean([x['m']['interest_extra'].mean() for x in xs])  # debt-years*pts
    o['Send']=np.mean([x['m']['Send'].mean() for x in xs]); o['phi_rng']=np.mean([ (x['m']['phimax']-x['m']['phimin']).mean() for x in xs])
    o['area_av']=100*np.mean([(b['area1']-x['m']['area1']).mean() for x in xs])/max(1e-9,b['area1'].mean())
    o['d95']=np.mean([x['m']['d95'].mean() for x in xs]); o['maxdep']=100*np.mean([x['m']['maxdep'].mean() for x in xs])
    return o
H='| %s | max r mean %% | max r p95 %% | sd log r | direction flips/yr | controller active %% days | extra interest (pts of debt over 2y) | free-ratio range | debt left | area>1pt avoided %% | max depth pts |'
for scen in ['quiet','liq20','drip']:
    print('\n#### scenario',scen,' (e_ctrl cells: 3 hl x 5 rmax x 3 eta x 3 eps_d = 135, 300 runs each; baseline none: area1 %.1f pt-days)'%[x for x in d if x['cell']['scen']==scen and x['cell']['pname']=='a_none'][0]['m']['area1'].mean())
    for var,vals in [('rmax',[.10,.25,.50,1.0,20.0]),('hl',[10,30,90]),('eta',[.05,.15,.40]),('eps_d',[.03,.10,.20])]:
        print(H%var); print('|---|---|---|---|---|---|---|---|---|---|---|')
        for v in vals:
            xs=sel(scen=scen,pname='e_ctrl',tag='E4',**{var:v}); o=stat(xs,scen)
            print('| %s | %.1f | %.1f | %.2f | %.1f | %.0f | %.2f | %.2f | %.2f | %+.0f | %.2f |'%(v,o['rmax_mean'],o['rmax_p95'],o['sd_logr'],o['flips_yr'],o['active'],o['extra_int'],o['phi_rng'],o['Send'],o['area_av'],o['maxdep']))
    xs=sel(scen=scen,pname='e0_fixed'); o=stat(xs,scen); print('e0 (free/paid split, fixed rate 3%%, no controller): area avoided %+.0f%%, maxdep %.2f, debt left %.2f, phi range %.2f'%(o['area_av'],o['maxdep'],o['Send'],o['phi_rng']))
    xs=sel(scen=scen,pname='a_none'); o=stat(xs,scen); print('a_none (all debt redeemable): maxdep %.2f debt left %.2f'%(o['maxdep'],o['Send']))
    print('noise/psi sweep (hl30 rmax50 eta.15 eps.1):'); 
    for su in [0.0,.15,.30]:
        for ps in [0.0,.1,.3]:
            xs=sel(scen=scen,tag='E4n',sig_u=su,psi=ps); o=stat(xs,scen)
            print('  sig_u %.2f psi %.1f: max r mean %.1f%% p95 %.1f%% sd log r %.2f flips/yr %.1f debt left %.2f area avoided %+.0f%% maxdep %.2f'%(su,ps,o['rmax_mean'],o['rmax_p95'],o['sd_logr'],o['flips_yr'],o['Send'],o['area_av'],o['maxdep']))
# rate path over 2 years, central cell
print('\n#### rate path (annual rate, %) every 60 days: p10 / median / p90 over 300 runs; hl30 eta.15 eps.1')
for scen in ['quiet','liq20','drip']:
    for rmax in [.10,.50,20.0]:
        x=sel(scen=scen,pname='e_ctrl',tag='E4',hl=30,eta=.15,eps_d=.10,rmax=rmax)[0]['m']['r_q']
        idx=list(range(0,T//10+1,6))
        print(scen,'rmax',rmax,' day:',[10*i for i in idx]); 
        for q,lab in [(0,'p10'),(1,'med'),(2,'p90')]: print('   ',lab,[round(100*float(x[q][i]),1) for i in idx])
# pure Monolith claim: below target for a year at hl 30
print('\nclosed-form check: r0=3%, hl=30d, continuous below-band for 365 days: r =', round(3*2**(365/30),0),'% (uncapped); with rmax 50% reached after', round(30*np.log2(50/3),0),'days')
# fraction of runs with sustained high rate in drip
for rmax in [.5,20.0]:
    xs=sel(scen='drip',pname='e_ctrl',tag='E4',rmax=rmax,hl=30,eta=.15,eps_d=.10)[0]['m']['rmaxseen']
    print('drip, rmax',rmax,'fraction of runs whose max rate >=10%%: %.2f, >=25%%: %.2f, >=50%%: %.2f'%((xs>=.1).mean(),(xs>=.25).mean(),(xs>=.5-1e-9).mean()))
