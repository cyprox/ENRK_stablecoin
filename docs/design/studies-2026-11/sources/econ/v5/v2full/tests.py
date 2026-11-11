"""Why: sanity/invariant checks of peg_model (ledger P6/P7). Prints PASS/FAIL lines."""
import numpy as np, warnings
warnings.filterwarnings('ignore')
from peg_model import *
def chk(name, ok, info=''): print(('PASS ' if ok else 'FAIL ')+name, info)
o = simulate([dict(f=0.0), dict(f=0.2, Ka=10.0), dict(f=0.2, Ka=0.01), dict(f=0.1), dict(f=0.3), dict(f=0.2, c=0.0, fee=0.0, Ka=10.0, D=50.0)], R=300, T=500)
chk('quiet market: p stays within 3 pts (max dep mean %.2f pts)' % (100*o['maxdep'][0].mean()), o['maxdep'][0].mean() < 0.03)
chk('unlimited arb capital: max depth below f-driven depth (%.2f vs %.2f pts)' % (100*o['maxdep'][1].mean(), 100*o['maxdep'][3].mean()), o['maxdep'][1].mean() < o['maxdep'][3].mean()+0.02)
chk('arb capital 0.01 gives deeper depeg than 10 (%.2f > %.2f)' % (100*o['maxdep'][2].mean(), 100*o['maxdep'][1].mean()), o['maxdep'][2].mean() > o['maxdep'][1].mean())
chk('depth rises with f: 10%% %.2f < 30%% %.2f' % (100*o['maxdep'][3].mean(), 100*o['maxdep'][4].mean()), o['maxdep'][3].mean() < o['maxdep'][4].mean())
chk('no fee, no friction, deep market, huge capital: depth ~ 0 (%.3f pts)' % (100*o['maxdep'][5].mean()), o['maxdep'][5].mean() < 0.01)
# reserve conservation: no policy, no shock, g=6%: Rsv/S at 365 d ~ 6% (S constant)
o2 = simulate([dict(f=0.0, g=0.06, ts=400)], R=300, T=365)
chk('reserve accrual: %.2f pts after 1 y at g=6%%' % (100*o2['Rend'][0].mean()), abs(o2['Rend'][0].mean()-0.06) < 0.003)
# reserve accounting under spending: Rsv = inflow - spent - absorbed
o3 = simulate([dict(f=0.2, pol=DEVYIELD, ymax_d=1.0, th_d=0.0, g=0.06), dict(ell=0.1, absorb=1)], R=300, T=500)
chk('spending never exceeds inflow+0: min reserve ratio >= 0 (%.4f)' % o3['Rmin_after'].min(), o3['Rmin_after'].min() >= -1e-12)
chk('absorption <= loss: absorbed %.3f <= 0.10 and <= reserve at shock %.3f' % (o3['absorbed'][1].mean(), o3['Rshock'][1].mean()), o3['absorbed'][1].mean() <= 0.1 + 1e-9 and o3['absorbed'][1].mean() <= o3['Rshock'][1].mean()*1.05)
# determinism and pairing
a = simulate([dict(f=0.2)], R=50, T=450, seed=5); b = simulate([dict(f=0.2), dict(f=0.2, pol=REBATE)], R=50, T=450, seed=5)
chk('same seed -> identical baseline irrespective of other cells', np.allclose(a['area'][0], b['area'][0]))
# ordering in cell does not change results
c = simulate([dict(f=0.2, pol=REBATE), dict(f=0.2)], R=50, T=450, seed=5)
chk('cell order irrelevant', np.allclose(c['area'][1], a['area'][0]) and np.allclose(c['area'][0], b['area'][1]))
# controller: fixed-point at equilibrium without noise/shock
o4 = simulate([dict(pol=CTRL, sig_u=0.0, f=0.0)], R=50, T=400)
chk('controller idle at equilibrium: rate stays 3%% (max %.3f)' % o4['rmaxseen'][0].max(), o4['rmaxseen'][0].max() < 0.0301)
# controller exp growth: eta=0, pref -0.8 -> uncapped growth rate doubling per half-life while below band
o5 = simulate([dict(pol=CTRL, eta=0.0, eps_d=0.0, pref_shift=-2.0, sig_u=0.0, f=0.0, ts=10, hl=30.0, rmax=1000.0)], R=20, T=200, store_r=True)
r = o5['rpath'][:, 0, 0]
chk('controller growth: r(day 90)/r(day 60)=%.2f (expect 2.0 after half-life 30 d)' % (r[9]/r[6]), abs(r[9]/r[6]-2.0) < 0.05)
o6 = simulate([dict(pol=CTRL, eta=0.0, eps_d=0.0, pref_shift=-2.0, sig_u=0.0, f=0.0, ts=10, hl=30.0, rmax=0.20)], R=20, T=300)
chk('explicit max rate binds: max %.3f == 0.20' % o6['rmaxseen'][0].max(), abs(o6['rmaxseen'][0].max()-0.20) < 1e-9)
