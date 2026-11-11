from an_common import *
D=load('E9'); d=D['res']; T=D['T']
def sel(**kw): return [x for x in d if all(x['cell'].get(k)==v for k,v in kw.items())]
def idx(day): return day//10
def st(xs):
    r360=np.mean([x['m']['r_q'][1][idx(360)] for x in xs])*100; r720=np.mean([x['m']['r_q'][1][idx(720)] for x in xs])*100
    return dict(rmax=100*np.mean([x['m']['rmaxseen'].mean() for x in xs]), r360=r360, r720=r720, p90_720=100*np.mean([x['m']['r_q'][2][idx(720)] for x in xs]),
                debt=np.mean([x['m']['Send'].mean() for x in xs]), xint=100*np.mean([x['m']['interest_extra'].mean() for x in xs]),
                flips=np.mean([x['m']['flips'].mean() for x in xs])/(T/365), act=100*np.mean([x['m']['active_days'].mean() for x in xs])/T)
for ps in [-0.4,-0.8,0.8]:
    print('\n#### persistent borrower preference shift (log phi* %+.1f from day 200; phi_target stays 30%%) - NOT a peg event (f=0). 300 runs/cell'%ps)
    e0=sel(pref_shift=ps,pname='e0_fixed')[0]['m']; print('fixed-rate split, no controller: debt left %.2f, free ratio end n/a'%e0['Send'].mean())
    print('| eta | rmax | max r mean %% | median r at day 360 %% | median r at day 720 %% | p90 r day 720 %% | debt left | extra interest pts of debt (2y) | active %% of days |'); print('|---|---|---|---|---|---|---|---|---|')
    for eta in [0.0,.02,.05,.15,.40]:
        for rmax in [.10,.25,.50,1.0,20.0]:
            o=st(sel(pref_shift=ps,pname='e_ctrl',eta=eta,rmax=rmax,hl=30,eps_d=.10))
            print('| %.2f | %s | %.1f | %.1f | %.1f | %.1f | %.2f | %.2f | %.0f |'%(eta,'none(20)' if rmax==20 else rmax,o['rmax'],o['r360'],o['r720'],o['p90_720'],o['debt'],o['xint'],o['act']))
    print('half-life effect (eta=.02, rmax none):',{hl:round(st(sel(pref_shift=ps,pname='e_ctrl',eta=.02,rmax=20.0,hl=hl,eps_d=.10))['r360'],1) for hl in [10,30,90]},' median r at day 360 (%)')
    print('demand elasticity effect (eta=.02, hl30, rmax none) debt left:',{e:round(st(sel(pref_shift=ps,pname='e_ctrl',eta=.02,rmax=20.0,hl=30,eps_d=e))['debt'],2) for e in [.03,.10,.20]})
