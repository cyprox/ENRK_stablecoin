import time, numpy as np
from peg_model import *
cells=[dict(f=0.2,pol=p,Ka=0.05) for p in range(4)]+[dict(f=0.2,pol=4),dict(f=0.2,pol=5),dict(ell=0.10,absorb=1),dict(ell=0.10)]
t0=time.time(); o=simulate(cells,R=300,T=600); print('t',time.time()-t0)
for i,c in enumerate(cells):
    print(i,c.get('pol'),c.get('ell'), 'maxdep %.3f area %.1f d99 %.1f spent %.4f Rshock %.3f Rmin %.3f absorbed %.3f'%tuple(o[k][i].mean() for k in ['maxdep','area','d99','spent','Rshock','Rmin_after','absorbed']), 'rmax %.3f'%o['rmaxseen'][i].mean())
