from an_common import *
def groups(name):
    G={}
    for x in load(name)['res']:
        c=x['cell']; G.setdefault((c['f'],c['Ka'],c['Kc'],c['g']),{})[c['pname']]=x
    return G
def row(G,n,sel=lambda k:True):
    ks=[k for k in G if sel(k)]
    av=np.mean([(G[k]['a_none']['m']['area1']-G[k][n]['m']['area1']).mean() for k in ks]); ba=np.mean([G[k]['a_none']['m']['area1'].mean() for k in ks])
    sp=np.mean([G[k][n]['m']['spent'].mean() for k in ks])*100
    md=np.mean([G[k][n]['m']['maxdep'].mean() for k in ks])*100; mb=np.mean([G[k]['a_none']['m']['maxdep'].mean() for k in ks])*100
    Rs=np.mean([G[k][n]['m']['Rshock'].mean() for k in ks])*100
    # fraction of cells where CI of avoided area excludes 0 and is positive
    pos=np.mean([ (lambda d: d.mean()-1.96*d.std(ddof=1)/np.sqrt(len(d))>0)(G[k]['a_none']['m']['area1']-G[k][n]['m']['area1']) for k in ks])
    neg=np.mean([ (lambda d: d.mean()+1.96*d.std(ddof=1)/np.sqrt(len(d))<0)(G[k]['a_none']['m']['area1']-G[k][n]['m']['area1']) for k in ks])
    return av/ba*100, md-mb, sp, (sp/av if av>0.3 else float('nan')), Rs, pos*100, neg*100
names=['b_ORA','b_RV','c_y20','c_y50','d_ORA_y20','d_ORA_y50','d_ORA_y100','d_RV_y50','e0_fixed','e_ctrl']
for nm,lab in [('E2','shield=1 (locked ENRK cannot sell in the shock)'),('E2s5','shield=0.5'),('E2s0','shield=0 (locked holders sell like everyone)')]:
    G=groups(nm)
    print('\n### liquidity shocks, %s; mean over f{10,20,30} x Ka x Kc x g = 81 cells'%lab)
    print('| policy | area>1pt avoided %% | change in max depth (pts) | reserve spent (pts debt) | cost per pt-day avoided | reserve at shock (pts) | cells helped (CI>0) %% | cells harmed %% |'); print('|---|---|---|---|---|---|---|---|')
    for n in names:
        r=row(G,n); print('| %s | %+.0f | %+.2f | %.3f | %.4f | %.1f | %.0f | %.0f |'%((n,)+r))
G=groups('E2')
print('\n### d_ORA_y50 and c_y50 and b_ORA by carry capital Kc (shield=1 and 0)')
for nm in ['E2','E2s0']:
    G=groups(nm)
    for Kc in [.03,.1,.3]:
        for n in ['b_ORA','c_y50','d_ORA_y50','d_ORA_y100']:
            r=row(G,n,lambda k:k[2]==Kc); print(nm,'Kc',Kc,n,'avoided %+.0f%% dmaxdep %+.2f spent %.3f cost %.4f'%(r[0],r[1],r[2],r[3]))
print('\n### by arb capital Ka (shield=1)')
G=groups('E2')
for Ka in [.02,.05,.15]:
    for n in ['b_ORA','c_y50','d_ORA_y50']:
        r=row(G,n,lambda k:k[1]==Ka); print('Ka',Ka,n,'avoided %+.0f%% dmaxdep %+.2f spent %.3f cost %.4f'%(r[0],r[1],r[2],r[3]))
print('\n### by reserve inflow g (shield=1): reserve at shock and (c) spending')
for g in [.03,.06,.12]:
    for n in ['c_y50','d_ORA_y50','b_ORA']:
        r=row(G,n,lambda k:k[3]==g); print('g',g,n,'avoided %+.0f%% spent %.3f Rshock %.1f'%(r[0],r[2],r[4]))
