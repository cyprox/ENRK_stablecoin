from ratelib import *
import json
random.seed(7)
def lu(lo,hi): return int(math.exp(random.uniform(math.log(lo),math.log(hi))))
cases=[];meta=[]
def add(r,dt,d,tag):
    for entry in('raw','guarded'):
        m=step_safe(r,dt,d); e=m if isinstance(m,int) else 0
        meta.append((entry,r,dt,d,e,tag)); cases.append(f"{entry} {r} {dt} {d} {e}")
for _ in range(1500): add(random.randint(RMIN,RMAX),lu(DT_MIN,10**8),random.choice((-1,0,1)),'rand-in')
for _ in range(800): add(lu(1,I64),lu(1,10**10),random.choice((-1,0,1,2,-2)),'rand-wide')
for r in (0,1,RMIN-1,RMIN,RMAX,RMAX+1,6*10**9,I64//2,I64):
    for dt in (0,1,DT_MIN-1,DT_MIN,DT_MAX,DT_MAX+1,10**9,I64//LN2_Q,I64//LN2_Q+1,I64):
        for d in (-1,0,1,2):
            add(r,dt,d,'extreme')
# overflow ceiling of r*e at x_max
xm=tdiv(mul(DT_MAX,LN2_Q),H); em=exp_q(xm)
rc=I64//em
for r in (rc,rc+1): add(r,DT_MAX,1,'ceiling')
open('cases_rate.txt','w').write('\n'.join(cases)+'\n'); json.dump(meta,open('meta_rate.json','w'))
print(len(cases),'e_max',em,'r ceiling',rc)
