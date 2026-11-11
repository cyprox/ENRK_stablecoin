import sys; sys.path.insert(0,'v1c'); sys.dont_write_bytecode=True
import numpy as np, stress_fee as N
from multiprocessing import Pool
def one(a):
    i,red,s,r=a
    fr=dict(auction_end_price=.75,enable_redemption=red)
    res=N.run(N.Scenario(name='g',seed=N.SEED+i,pre_days=365,junior_ledger=True,total_drawdown=.85,crash_days=60,index_mode='flat',stability_fee=r,kfiat_share=s,dist_rule='D1',surplus_rule='S1',**fr))
    return res.unbacked_usd_pct,res.enrk_loss_pct,res.kfiat_loss_pct
if __name__=='__main__':
    n=250
    with Pool(3) as p:
        for red in (True,False):
            for s,r in ((0,0),(.3,0),(.5,0)):
                o=np.array(p.map(one,[(i,red,s,r) for i in range(n)]))
                print('redemption',red,'s',s,'r',r,'unbacked mean %.2f ENRK p95 %.1f kFIAT mean %.1f'%(o[:,0].mean(),np.quantile(o[:,1],.95,method='higher'),o[:,2].mean()))
