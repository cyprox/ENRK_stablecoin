from ratelib import *
import json,collections
meta=json.load(open('meta_rate.json')); out=open('out_rate.txt').read().splitlines()
st=collections.Counter(); bad=[]; maxerr=0; maxrel=0; errs=[]
for m,o in zip(meta,out):
    entry,r,dt,d,e,tag=m; acc=o.split()[1]=='ACCEPT'; msg=o[o.find('REJECT')+7:]
    ingd = 0<=r<=RMAX and dt>=DT_MIN and -1<=d<=1
    pred=step_safe(r,dt,d)
    expacc = isinstance(pred,int) and (entry=='raw' or ingd)
    if expacc!=acc: bad.append((m,o))
    kind='ACC' if acc else ('OVF' if 'too big' in msg else 'REJ')
    st[(entry,kind)]+=1
    if entry=='raw' and not acc and not isinstance(pred,int): st[('raw-fail-mode',pred)]+=1
    if entry=='guarded' and acc and tag in('rand-in',):
        ex=exact(r,dt,d); err=abs(Decimal(e)-ex); errs.append((float(err),r,dt,d))
for k in sorted(st,key=str): print(k,st[k])
print('MISMATCH engine vs int-mirror/guard prediction:',len(bad),bad[:3])
errs.sort(reverse=True); print('max abs err ppb vs exact (rand-in, guarded):',errs[:3])
print('mean',sum(e[0] for e in errs)/len(errs))
# relative error at various steps
for dt in (3600,86400,604800,1296000,10**7):
    w=0
    for r in (RMIN,50_000_000,500_000_000,RMAX):
        for d in(-1,1):
            ex=exact(r,dt,d); w=max(w,abs(Decimal(step(r,dt,d))-ex)/ex)
    print('dt',dt,'max rel err',float(w))
