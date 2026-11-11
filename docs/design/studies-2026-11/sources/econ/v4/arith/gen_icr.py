import random, json, sys
random.seed(20261111)
I64=2**63-1; S=10**8
C_MAX=10**16; P_MAX=5*10**8; D_MAX=4*10**18
def tdiv(a,b):
    q=abs(a)//abs(b); return q if (a<0)==(b<0) else -q
class Ov(Exception): pass
def chk(x):
    if x>I64 or x< -I64-1: raise Ov()
    return x
def unguarded(c,p,d):
    try:
        t=chk(c*p); t=chk(t*100)
        t=tdiv(t,S)
        if d==0: return 'DIV0'
        return tdiv(t,d)
    except Ov: return 'OVF'
def inb(c,p,d): return 0<=c<=C_MAX and 0<p<=P_MAX and 0<d<=D_MAX
def ref(c,p,d):  # bigint, exact
    return (c*p*100)//(S*d)
def lu(lo,hi): # log-uniform int
    import math
    return int(math.exp(random.uniform(math.log(lo),math.log(hi))))
cases=[]; meta=[]
def add(c,p,d,tag):
    for entry in ('unguarded','guarded'):
        if d==0: r=0
        else:
            r=ref(c,p,d)
            if not (-I64-1<=r<=I64): r=0
        meta.append((entry,c,p,d,r,tag)); cases.append(f"{entry} {c} {p} {d} {r}")
# random in-range log-uniform
for _ in range(1500): add(lu(1,C_MAX), lu(1,P_MAX), lu(1,D_MAX),'rand-in')
# realistic: KAS price ~0.0295..1.0 (p 2.9e6..1e8), c 1..1e7 KAS, debt 1..1e9 units(1e8 scale)
for _ in range(800): add(lu(10**8,10**15), lu(2*10**6,10**8), lu(10**6,10**15),'realistic')
# beyond guard bounds
for _ in range(500): add(lu(1,I64), lu(1,I64), lu(1,I64),'rand-wide')
# extremes
ex=[0,1,2,I64,I64-1,C_MAX,C_MAX+1,P_MAX,P_MAX+1,D_MAX,D_MAX+1,2**32,2**31,10**8,10**8-1,10**8+1]
for c in ex:
  for p in ex:
    for d in (0,1,2,I64,D_MAX,D_MAX+1,10**8,150):
      add(c,p,d,'extreme')
# negatives
for _ in range(100): add(-lu(1,10**12), lu(1,10**8), lu(1,10**12),'neg-c'); add(lu(1,10**12), -lu(1,10**8), lu(1,10**12),'neg-p'); add(lu(1,10**12), lu(1,10**8), -lu(1,10**12),'neg-d')
# exact unguarded boundary: largest c with c*p*100<=I64 at several p
for p in (2950000,10**7,10**8,5*10**8,10**9):
    cm=I64//(p*100)
    for c in (cm,cm+1): add(c,p,10**9,'unguarded-boundary')
# rounding vs exact (ICR just at 150): c*p*100/(S*d) near 150
for _ in range(200):
    d=lu(10**6,10**12); p=lu(10**6,10**8); c=(150*S*d)//(p*100)+random.choice((-1,0,1)); 
    if c>0: add(c,p,d,'near-MCR')
open('cases_icr.txt','w').write('\n'.join(cases)+'\n')
json.dump(meta,open('meta_icr.json','w'))
print(len(cases))
