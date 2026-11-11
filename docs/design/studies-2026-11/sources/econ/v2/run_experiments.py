"""Why: grids E1-E7 for the peg-defense reserve study (ledger P6/P7). Usage: python3 run_experiments.py E1 [E2 ...]  -> results/<E>.pkl"""
import sys, pickle, itertools, os, time
import numpy as np
from peg_model import *

KEYS = ['maxdep','area','area1','d99','d98','d95','span99','spent','rebate_cost','Rshock','Rmin_after','Rend','absorbed','ell_net','sumy','sumy_false',
        'sumy_post','false_pay','pay_man','sumy_man','wash_cost','flash_pay','redeemed','Send','interest_extra','rmaxseen','rsum','rsq',
        'flips','active_days','phimin','phimax','lam_peak','Hc_peak','pay_total']
R = 300
os.makedirs('results', exist_ok=True)

def run(cells, T, seed=1, store_r=False, chunk=40):
    res = []
    for i in range(0, len(cells), chunk):
        sub = cells[i:i + chunk]
        o = simulate(sub, R=R, T=T, seed=seed, store_r=store_r)
        for j, c in enumerate(sub):
            d = {k: o[k][j].copy() for k in KEYS}
            if store_r:
                rp = o['rpath'][:, j, :]; pp = o['ppath'][:, j, :]
                d['r_q'] = np.quantile(rp, [0.1, 0.5, 0.9], axis=1)
                d['p_q'] = np.quantile(pp, [0.1, 0.5, 0.9], axis=1)
            res.append(dict(cell=c, m=d))
    return res

def save(name, res, T):
    pickle.dump(dict(res=res, T=T, R=R), open(f'results/{name}.pkl', 'wb'))
    print(name, len(res), 'cells x', R, 'runs, T =', T, flush=True)

POLS_LIQ = [('a_none', dict(pol=NONE)), ('b_ORA', dict(pol=REBATE, trig=ORA)), ('b_RV', dict(pol=REBATE, trig=RV)),
            ('c_y20', dict(pol=RESYIELD, ymax_c=0.2)), ('c_y50', dict(pol=RESYIELD, ymax_c=0.5)), ('c_y100', dict(pol=RESYIELD, ymax_c=1.0)),
            ('d_ORA_y20', dict(pol=DEVYIELD, trig=ORA, ymax_d=0.2)), ('d_ORA_y50', dict(pol=DEVYIELD, trig=ORA, ymax_d=0.5)),
            ('d_ORA_y100', dict(pol=DEVYIELD, trig=ORA, ymax_d=1.0)), ('d_RV_y50', dict(pol=DEVYIELD, trig=RV, ymax_d=0.5)),
            ('e0_fixed', dict(pol=FREEFIX)), ('e_ctrl', dict(pol=CTRL))]

def E1():
    cells = []
    for f, D, Ka, c, k in itertools.product([.1, .2, .3], [1, 2, 4], [.02, .05, .15], [.0025, .005, .01], [.01, .03, .08]):
        cells.append(dict(tag='E1', f=f, D=D, Ka=Ka, c=c, kappa=k))
    save('E1', run(cells, 600), 600)

def E2(shield=1.0, name='E2'):
    cells = []
    for f, Ka, Kc, g in itertools.product([.1, .2, .3], [.02, .05, .15], [.03, .1, .3], [.03, .06, .12]):
        for nm, pc in POLS_LIQ:
            cells.append(dict(tag=name, pname=nm, f=f, Ka=Ka, Kc=Kc, g=g, shield=shield, **pc))
    save(name, run(cells, 600), 600)

def E2s0(): E2(0.0, 'E2s0')
def E2s5(): E2(0.5, 'E2s5')

def E3():
    cells = []
    for f in [0.0, 0.2]:
        cells.append(dict(tag='E3', pname='a_none', f=f))
        for so, dl, y, th in itertools.product([.003, .01, .03, .05], [0, 1, 3], [.2, .5, 1.0], [.01, .02, .04]):
            cells.append(dict(tag='E3', pname='d_ORA', f=f, pol=DEVYIELD, trig=ORA, so=so, delay=dl, ymax_d=y, th_d=th))
        for so, dl, th in itertools.product([.003, .01, .03, .05], [0, 1, 3], [.005, .01, .03]):
            cells.append(dict(tag='E3', pname='b_ORA', f=f, pol=REBATE, trig=ORA, so=so, delay=dl, th_b=th))
    save('E3', run(cells, 600), 600)

def E4():
    cells = []
    scen = {'quiet': dict(f=0.0, ts=200), 'liq20': dict(f=0.2, ts=200), 'drip': dict(f=0.0, ts=200, drip=0.003, drip_T=120)}
    for sn, sc in scen.items():
        cells.append(dict(tag='E4', scen=sn, pname='a_none', **sc))
        cells.append(dict(tag='E4', scen=sn, pname='e0_fixed', pol=FREEFIX, **sc))
        for hl, rmax, eta, eps in itertools.product([10, 30, 90], [.10, .25, .50, 1.0, 20.0], [.05, .15, .40], [.03, .10, .20]):
            cells.append(dict(tag='E4', scen=sn, pname='e_ctrl', pol=CTRL, hl=hl, rmax=rmax, eta=eta, eps_d=eps, **sc))
        for su, ps in itertools.product([0.0, .15, .30], [0.0, .1, .3]):
            cells.append(dict(tag='E4n', scen=sn, pname='e_ctrl', pol=CTRL, sig_u=su, psi=ps, **sc))
    save('E4', run(cells, 730, store_r=True), 730)

def E5():
    cells = []
    cfgs = [('a_none', dict()), ('f_absorb', dict(absorb=1)), ('d_ORA', dict(pol=DEVYIELD, ymax_d=.5)),
            ('d_then_absorb', dict(pol=DEVYIELD, ymax_d=.5, absorb=1)), ('d_fence50_absorb', dict(pol=DEVYIELD, ymax_d=.5, absorb=1, nu=.5)),
            ('c_y50', dict(pol=RESYIELD, ymax_c=.5)), ('b_ORA', dict(pol=REBATE)), ('c_then_absorb', dict(pol=RESYIELD, ymax_c=.5, absorb=1))]
    for ell, g, rec in itertools.product([.02, .03, .10, .14, .20, .26], [.03, .06, .12], [0.0, 0.5]):
        for n, cf in cfgs:
            cells.append(dict(tag='E5', pname=n, ell=ell, g=g, rec=rec, **cf))
    for n, cf in cfgs:  # fence sweep + sequence
        for ell, g, dsol in itertools.product([.03, .10, .20], [.06], [30, 90, 180]):
            cells.append(dict(tag='E5seq', pname=n, f=.3, ell=ell, g=g, dsol=dsol, **cf))
    for ell, nu in itertools.product([.03, .10, .20], [0, .25, .5, .75, 1.0]):
        cells.append(dict(tag='E5fence', pname='d_ORA_fence', f=.3, ell=ell, g=.06, dsol=90, pol=DEVYIELD, ymax_d=.5, absorb=1, nu=nu))
    save('E5', run(cells, 800), 800)

def E6():
    cells = []
    base = dict(f=0.0, ts=500, man_start=200)
    for T_, dl in itertools.product([5, 20], [.03, .06, .10]):
        mk = dict(man_T=T_, man_delta=dl, **base)
        cells.append(dict(tag='E6', pname='d_ORA_y50', pol=DEVYIELD, ymax_d=.5, **mk))
        cells.append(dict(tag='E6', pname='d_ORA_y100', pol=DEVYIELD, ymax_d=1.0, **mk))
        cells.append(dict(tag='E6', pname='b_ORA', pol=REBATE, **mk))
        cells.append(dict(tag='E6', pname='c_y50', pol=RESYIELD, ymax_c=.5, **mk))
        cells.append(dict(tag='E6', pname='e_ctrl', pol=CTRL, **mk))
    for T_, w in itertools.product([5, 20], [.005, .02, .05]):
        mk = dict(wash_T=T_, wash=w, man_start=200, man_T=0, **{k: v for k, v in base.items() if k != 'man_start'})
        cells.append(dict(tag='E6w', pname='d_RV_y50', pol=DEVYIELD, trig=RV, ymax_d=.5, **mk))
        cells.append(dict(tag='E6w', pname='b_RV', pol=REBATE, trig=RV, **mk))
    for T_, sh in itertools.product([20, 60], [.05, .10, .20]):
        cells.append(dict(tag='E6phi', pname='e_ctrl', pol=CTRL, phi_shift=sh, man_T=T_, **base))
    for pn, pc in [('a_none', dict()), ('d_ORA_y50', dict(pol=DEVYIELD, ymax_d=.5)), ('c_y50', dict(pol=RESYIELD, ymax_c=.5)), ('b_ORA', dict(pol=REBATE)),
                   ('d_RV_y50', dict(pol=DEVYIELD, trig=RV, ymax_d=.5)), ('e_ctrl', dict(pol=CTRL))]:
        for so in [.003, .01, .03, .05]:
            cells.append(dict(tag='E6quiet', pname=pn, so=so, **base, **pc))
    save('E6', run(cells, 600), 600)

def E7():
    cells = []
    for f, lm, fl in itertools.product([0.0, .2], [0, 7], [0.0, .1, .3]):
        for pn, pc in [('c_y20', dict(pol=RESYIELD, ymax_c=.2)), ('c_y50', dict(pol=RESYIELD, ymax_c=.5)), ('d_ORA_y50', dict(pol=DEVYIELD, ymax_d=.5))]:
            cells.append(dict(tag='E7', pname=pn, f=f, lock_min=lm, flash=fl, **pc))
    save('E7', run(cells, 600), 600)

def E9():
    cells = []
    for ps in [-0.4, -0.8, 0.8]:
        for hl, rmax, eta, eps in itertools.product([10, 30, 90], [.10, .25, .50, 1.0, 20.0], [0.0, .02, .05, .15, .40], [.03, .10, .20]):
            cells.append(dict(tag='E9', pref_shift=ps, pol=CTRL, pname='e_ctrl', hl=hl, rmax=rmax, eta=eta, eps_d=eps, f=0.0, ts=200))
        cells.append(dict(tag='E9', pref_shift=ps, pol=FREEFIX, pname='e0_fixed', f=0.0, ts=200))
    save('E9', run(cells, 730, store_r=True), 730)

def E8():
    cells = []
    for dr, Ka, Kc, g in itertools.product([.002, .004], [.02, .05], [.03, .1, .3], [.06, .12]):
        for nm, pc in POLS_LIQ:
            cells.append(dict(tag='E8', pname=nm, f=0.0, ts=365, drip=dr, drip_T=120, Ka=Ka, Kc=Kc, g=g, **pc))
    save('E8', run(cells, 700), 700)

if __name__ == '__main__':
    for n in sys.argv[1:]:
        t0 = time.time(); globals()[n](); print('  time %.0fs' % (time.time() - t0), flush=True)
