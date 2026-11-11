from an_common import *
d=load('E3')['res']
base={f:[x for x in d if x['cell']['pname']=='a_none' and x['cell']['f']==f][0] for f in (0.0,0.2)}
def sel(**kw): return [x for x in d if all(x['cell'].get(k)==v for k,v in kw.items())]
print('### E3 oracle quality, policy d_ORA (yield on locked ENRK, trigger = ENRK oracle price). 300 runs/cell. spent and false payout in pts of debt (600 days, reserve inflow 6%/yr)')
print('Quiet market (f=0): payouts are pure oracle-error subsidy (true |dev|<1% on almost all days).')
print('| noise sd | delay d | ymax | th | quiet: spent pts | quiet: payout while true dev<1% pts | f=20%: area>1pt avoided % | f=20%: spent pts | f=20% false-payout share |'); print('|---|---|---|---|---|---|---|---|---|')
for so in [.003,.01,.03,.05]:
  for dl in [0,1,3]:
    for y in [.5]:
      for th in [.02]:
        q=sel(pname='d_ORA',f=0.0,so=so,delay=dl,ymax_d=y,th_d=th)[0]['m']; s=sel(pname='d_ORA',f=0.2,so=so,delay=dl,ymax_d=y,th_d=th)[0]['m']
        av=100*(base[0.2]['m']['area1']-s['area1']).mean()/base[0.2]['m']['area1'].mean()
        print('| %.1f%% | %d | %.0f%% | %.0f%% | %.3f | %.3f | %+.0f | %.3f | %.0f%% |'%(100*so,dl,100*y,100*th,100*q['spent'].mean(),100*q['false_pay'].mean(),av,100*s['spent'].mean(),100*s['false_pay'].mean()/max(1e-12,s['spent'].mean())))
print('\nthreshold sweep at sd 1%, delay 0, ymax 50%/100% (quiet spent pts / f=20% area avoided %):')
for y in [.5,1.0]:
  for th in [.01,.02,.04]:
    q=sel(pname='d_ORA',f=0.0,so=.01,delay=0,ymax_d=y,th_d=th)[0]['m']; s=sel(pname='d_ORA',f=0.2,so=.01,delay=0,ymax_d=y,th_d=th)[0]['m']
    print(' ymax',y,'th',th,'quiet spent %.4f  avoided %+.0f%%  f20 spent %.3f'%(100*q['spent'].mean(),100*(base[0.2]['m']['area1']-s['area1']).mean()/base[0.2]['m']['area1'].mean(),100*s['spent'].mean()))
print('\n### policy b_ORA (rebate of redemption fee when oracle shows dev > th)')
print('| noise sd | delay | th | quiet: rebate cost pts | f=20%: area avoided % | f=20%: cost pts |'); print('|---|---|---|---|---|---|')
for so in [.003,.01,.03,.05]:
  for dl in [0,3]:
    for th in [.01]:
        q=sel(pname='b_ORA',f=0.0,so=so,delay=dl,th_b=th)[0]['m']; s=sel(pname='b_ORA',f=0.2,so=so,delay=dl,th_b=th)[0]['m']
        print('| %.1f%% | %d | %.1f%% | %.4f | %+.0f | %.3f |'%(100*so,dl,100*th,100*q['rebate_cost'].mean(),100*(base[0.2]['m']['area1']-s['area1']).mean()/base[0.2]['m']['area1'].mean(),100*s['spent'].mean()))
print('\nquiet-market redemptions caused by rebate (share of supply), b_ORA th 1%:', {so:round(float(sel(pname='b_ORA',f=0.0,so=so,delay=0,th_b=.01)[0]['m']['redeemed'].mean()),4) for so in [.003,.01,.03,.05]}, 'none:', round(float(base[0.0]['m']['redeemed'].mean()),4))
