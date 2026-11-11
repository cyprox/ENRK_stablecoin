from an_common import *
d=load('E2')['res']
# group by (f,Ka,Kc,g) -> baseline
G={}
for x in d:
    c=x['cell']; G.setdefault((c['f'],c['Ka'],c['Kc'],c['g']),{})[c['pname']]=x
names=[n for n in G[next(iter(G))]]
def table(sel,title):
    print('\n###',title)
    print('| policy | max depth pts | area>1pt (pt-days) | days<98% | days<95% | reserve spent (pts of debt) | area avoided/baseline | cost per pt-day avoided (pts debt) |')
    print('|---|---|---|---|---|---|---|---|')
    ks=[k for k in G if sel(k)]
    for n in names:
        md=[];ar=[];d98=[];d95=[];sp=[];av=[];ba=[]
        for k in ks:
            b=G[k]['a_none']['m']; p=G[k][n]['m']
            md.append(p['maxdep'].mean()*100); ar.append(p['area1'].mean()); d98.append(p['d98'].mean()); d95.append(p['d95'].mean()); sp.append(p['spent'].mean()*100)
            av.append((b['area1']-p['area1']).mean()); ba.append(b['area1'].mean())
        cost = np.mean(sp)/np.mean(av) if np.mean(av)>0.5 else float('nan')
        print('| %s | %.2f | %.1f | %.1f | %.2f | %.3f | %+.0f%% | %s |'%(n,np.mean(md),np.mean(ar),np.mean(d98),np.mean(d95),np.mean(sp),100*np.mean(av)/np.mean(ba),('%.4f'%cost) if cost==cost else 'n/a'))
if __name__=='__main__':
    table(lambda k:True,'ALL cells (f x Ka x Kc x g = 81 cells per policy, 300 runs each)')
    for f in [.1,.2,.3]: table(lambda k,f=f:k[0]==f,'f=%s'%f)
    for Kc in [.03,.1,.3]: table(lambda k,Kc=Kc:k[2]==Kc,'carry capital Kc=%s'%Kc)
    for Ka in [.02,.05,.15]: table(lambda k,Ka=Ka:k[1]==Ka,'arb capital Ka=%s'%Ka)
    for g in [.03,.06,.12]: table(lambda k,g=g:k[3]==g,'reserve inflow g=%s'%g)
