"""Why: seed robustness of the E2 headline numbers (ledger P6)."""
import warnings, itertools; warnings.filterwarnings('ignore')
import numpy as np
from run_experiments import POLS_LIQ
from peg_model import *
for seed in [1,2,3]:
    cells=[]
    for nm,pc in POLS_LIQ: cells.append(dict(pname=nm,f=.2,Ka=.05,Kc=.1,g=.06,**pc))
    o=simulate(cells,R=300,T=600,seed=seed)
    base=o['area1'][0].mean()
    print('seed',seed,' '.join('%s:%+.0f%%'%(c['pname'],100*(base-o['area1'][i].mean())/base) for i,c in enumerate(cells) if c['pname'] in ('b_ORA','c_y50','d_ORA_y50','d_RV_y50','e_ctrl')))
