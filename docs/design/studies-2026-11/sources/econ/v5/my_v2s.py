import sys; sys.path.insert(0,'.'); sys.dont_write_bytecode=True
import numpy as np
from peg_model import *
cells=[]; 
for f in (.1,.2,.3):
    for nm,pc in (('a',dict(pol=NONE)),('b',dict(pol=REBATE,trig=ORA)),('c50',dict(pol=RESYIELD,ymax_c=.5)),('d50',dict(pol=DEVYIELD,trig=ORA,ymax_d=.5))):
        cells.append(dict(tag='E2',pname=nm,f=f,Ka=.05,Kc=.1,g=.06,shield=1.0,**pc))
o=simulate(cells,R=300,T=600,seed=int(sys.argv[1]),store_r=False)
for j,c in enumerate(cells):
    print(c['f'],c['pname'],'maxdep %.2f area1 %.1f d98 %.2f spent %.3f'%(o['maxdep'][j].mean()*100,o['area1'][j].mean(),o['d98'][j].mean(),o['spent'][j].mean()*100))
