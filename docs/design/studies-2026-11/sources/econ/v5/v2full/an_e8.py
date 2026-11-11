from an_common import *
G={}
for x in load('E8')['res']:
    c=x['cell']; G.setdefault((c['drip'],c['Ka'],c['Kc'],c['g']),{})[c['pname']]=x
names=[n for n in G[next(iter(G))]]
def row(n,sel):
    ks=[k for k in G if sel(k)]
    b=lambda k,m:G[k]['a_none']['m'][m].mean()
    av=np.mean([b(k,'area1')-G[k][n]['m']['area1'].mean() for k in ks]); ba=np.mean([b(k,'area1') for k in ks])
    sp=np.mean([G[k][n]['m']['spent'].mean() for k in ks])*100
    return 100*av/ba, 100*np.mean([G[k][n]['m']['maxdep'].mean()-b(k,'maxdep') for k in ks]), sp, sp/av if av>1 else float('nan'), np.mean([G[k][n]['m']['d95'].mean() for k in ks]), np.mean([b(k,'d95') for k in ks]), np.mean([G[k][n]['m']['Rend'].mean() for k in ks])*100, np.mean([G[k][n]['m']['Send'].mean() for k in ks])
print('### persistent sell pressure (drip 0.2-0.4%% of supply/day for 120 days); mean over 24 cells (drip x Ka x Kc x g), 300 runs each')
print('| policy | area>1pt avoided %% | change max depth pts | reserve spent pts | cost per pt-day | days<95%% | (baseline days<95%%) | reserve left pts | supply at end |'); print('|---|---|---|---|---|---|---|---|---|')
for n in names:
    r=row(n,lambda k:True); print('| %s | %+.0f | %+.2f | %.2f | %.3f | %.1f | %.1f | %.1f | %.2f |'%((n,)+r))
print('\nby drip rate, key policies')
for dr in [.002,.004]:
    for n in ['a_none','b_ORA','c_y50','d_ORA_y50','d_ORA_y100','d_RV_y50','e_ctrl']:
        r=row(n,lambda k:k[0]==dr); print('drip',dr,n,'avoided %+.0f%% dmaxdep %+.2f spent %.2f cost %.3f d95 %.1f (base %.1f) Rleft %.1f'%((r[0],r[1],r[2],r[3],r[4],r[5],r[6])))
