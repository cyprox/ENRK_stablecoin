from an_common import *
d=load('E6')['res']; E7=load('E7')['res']
def sel(**kw): return [x for x in d if all(x['cell'].get(k)==v for k,v in kw.items())]
Rman=0.06*200/365
print('### E6 attacks. No real depeg (f=0). Reserve at attack start ~ %.2f pts of debt (6%%/yr x 200 d). 300 runs/cell, oracle noise sd 1%%.'%(100*Rman))
print('\n#### E6a oracle manipulation: observed ENRK price pushed DOWN by delta for T days. payout = reserve outflow during the window (pts of debt). Attacker pre-locked position A (share of supply), opportunity cost 15%/yr on A. Dv* = largest oracle-venue depth (supply fraction that moves the venue price 100%) at which the attack is still profitable under cost/day = 0.5*delta^2*Dv*supply (ASSUMED cost model).')
print('| policy | delta | T d | reserve outflow in window pts | = % of reserve | Dv* for A=1%% | A=5%% | A=20%% | honest-locker share of outflow (A=5%%) |'); print('|---|---|---|---|---|---|---|---|---|')
for pn in ['d_ORA_y50','d_ORA_y100','b_ORA','c_y50','e_ctrl']:
    for T_ in [5,20]:
        for dl in [.03,.06,.10]:
            m=sel(tag='E6',pname=pn,man_T=T_,man_delta=dl)[0]['m']
            out=100*m['pay_man'].mean()+100*m['rebate_cost'].mean()*(pn=='b_ORA')
            if pn=='b_ORA': out=100*m['rebate_cost'].mean()
            sy=m['sumy_man'].mean(); lam=m['lam_peak'].mean()
            dv=[]
            for A in [.01,.05,.20]:
                gross=A*sy; opp=.15*A*T_/365; dv.append(max(0,2*(gross-opp)/(dl**2*T_)))
            share=0.05/(0.05+lam+1e-9) if sy>0 else 0
            print('| %s | %.0f%% | %d | %.3f | %.0f%% | %.3f | %.3f | %.3f | %.0f%% |'%(pn,100*dl,T_,out,100*out/(100*Rman),dv[0],dv[1],dv[2],100*(1-share) if sy>0 else 0))
print('\n(c_y50 and e_ctrl have no oracle input: outflow is the same as the unmanipulated baseline for the window. Dv* ~ 0 means: unprofitable at any venue depth.)')
print('\n#### E6b wash trading to farm a volume trigger (d_RV: yield when 7-day redemption volume > 1%% of supply; b_RV: rebate). Attacker pays mint 2%% + redeem 1%% = 3%% of wash volume (no rebate assumed on its own redemptions).')
print('| policy | wash vol/day (% supply) | days | wash cost pts of debt | total payout over run pts | payout/wash cost | attacker A=5%% locked gross pts | net pts |'); print('|---|---|---|---|---|---|---|---|')
for pn in ['d_RV_y50','b_RV']:
    for T_ in [5,20]:
        for w in [.005,.02,.05]:
            m=sel(tag='E6w',pname=pn,wash_T=T_,wash=w)[0]['m']
            wc=100*m['wash_cost'].mean(); pay=100*m['spent'].mean(); gross=100*0.05*m['sumy'].mean() if pn=='d_RV_y50' else 0
            print('| %s | %.1f | %d | %.3f | %.3f | %.2f | %.4f | %+.4f |'%(pn,100*w,T_,wc,pay,pay/wc if wc>0 else 0,gross,gross-wc))
print('\n#### E6c free-ratio manipulation of (e): attacker shifts the observed free-debt ratio down by `shift` (share of supply) for T days (e.g. by moving its own debt to paid mode). Damage = extra interest paid by all paid borrowers + debt contraction; cost to attacker = interest on its own shifted debt.')
print('| shift | T d | max rate %% | extra interest pts of debt | debt left | attacker interest cost pts (shift*r*T) |'); print('|---|---|---|---|---|---|')
for T_ in [20,60]:
    for sh in [.05,.10,.20]:
        m=sel(tag='E6phi',pname='e_ctrl',man_T=T_,phi_shift=sh)[0]['m']
        r_avg=0.03*1.5
        print('| %.0f%% | %d | %.1f | %.3f | %.3f | %.4f |'%(100*sh,T_,100*m['rmaxseen'].mean(),100*m['interest_extra'].mean(),m['Send'].mean(),100*sh*r_avg*T_/365))
print('\n#### E6d false payout from ordinary oracle noise (no manipulation, no real depeg), 600 days, pts of debt paid out of the reserve')
print('| policy | noise 0.3%% | 1%% | 3%% | 5%% |'); print('|---|---|---|---|---|')
for pn in ['a_none','d_ORA_y50','b_ORA','c_y50','d_RV_y50','e_ctrl']:
    row=[]
    for so in [.003,.01,.03,.05]:
        m=sel(tag='E6quiet',pname=pn,so=so)[0]['m']; row.append(100*(m['spent'].mean()))
    print('| %s | %.3f | %.3f | %.3f | %.3f |'%((pn,)+tuple(row)))
print('\n### E7 flash holders / snapshot accrual (payout accrues per day on balance with no minimum lock). flash = borrowed ENRK share of supply counted as locked; lock_min=7 disables it. Cost 600 days.')
print('| policy | f | flash | lock_min | total outflow pts | of which flash holders pts | outflow multiplier vs no flash | area>1pt |'); print('|---|---|---|---|---|---|---|---|')
for x in E7:
    c=x['cell']; m=x['m']
    b=[y for y in E7 if y['cell']['pname']==c['pname'] and y['cell']['f']==c['f'] and y['cell']['flash']==0 and y['cell']['lock_min']==c['lock_min']][0]['m']
    print('| %s | %.1f | %.1f | %d | %.3f | %.3f | %.2fx | %.1f |'%(c['pname'],c['f'],c['flash'],c['lock_min'],100*m['spent'].mean(),100*m['flash_pay'].mean(),m['spent'].mean()/max(1e-12,b['spent'].mean()),m['area1'].mean()))
print('\nflash economics per day (analytic): payout per unit = ymax/365 = %.3f%%/day at 50%%/yr, %.3f%%/day at 100%%/yr; break-even flash-loan fee per day-unit equals that'%(50/365,100/365))
