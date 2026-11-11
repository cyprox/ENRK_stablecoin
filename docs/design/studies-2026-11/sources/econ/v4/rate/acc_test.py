import random, math, json, subprocess, collections
random.seed(3)
I64=2**63-1; Y=31536000; G=10**9
def lu(lo,hi): return int(math.exp(random.uniform(math.log(lo),math.log(hi))))
def naive(d,r,t):
    x=d*r
    if x>I64: return None
    x*=t
    if x>I64: return None
    return x//Y//G
def split(d,r,t):
    a=(d//G)*r+(d%G)*r//G
    return (a//Y)*t+(a%Y)*t//Y
cases=[];meta=[]
def add(d,r,t,tag):
    ref=d*r*t//(Y*G)
    n=naive(d,r,t); 
    meta.append(('naive_e',d,r,t,n,ref,tag)); cases.append(f"naive_e {d} {r} {t} {n if n is not None else 0}")
    s=split(d,r,t)
    meta.append(('split_e',d,r,t,s,ref,tag)); cases.append(f"split_e {d} {r} {t} {s}")
for _ in range(1500): add(lu(1,10**18),random.randint(5_000_000,10**9),lu(3600,63072000),'rand')
for _ in range(700): add(lu(10**8,10**14),random.randint(5_000_000,10**9),lu(3600,10**7),'realistic')   # 1..1e6 ENRK at 1e8 scale
for d in (0,1,10**8,10**12,10**18,10**18+1):
  for r in (0,5_000_000,10**9,10**9+1):
    for t in (0,3600,Y,63072000,63072001):
      add(d,r,t,'extreme')
open('cases_acc.txt','w').write('\n'.join(cases)+'\n'); json.dump(meta,open('meta_acc.json','w'))
