"""Why: transparent daily peg-dynamics model of ENRK market price vs index peg, for ledger P6/P7 verification (no design decision).
Every output is a MODEL OUTPUT under the ASSUMED parameters in DEFAULTS. Vectorised over (cells x runs); runs share noise across cells (paired)."""
import numpy as np

NONE, REBATE, RESYIELD, DEVYIELD, CTRL, FREEFIX = 0, 1, 2, 3, 4, 5
POLNAMES = {0: 'a_none', 1: 'b_rebate', 2: 'c_reserve_yield', 3: 'd_dev_yield', 4: 'e_controller', 5: 'e0_free_paid_fixed'}
ORA, RV = 0, 1

DEFAULTS = dict(
    pol=NONE, trig=ORA, absorb=0, nu=0.0,
    # shocks
    f=0.0, ts=365, ell=0.0, dsol=0, fp0=0.10, chi=0.0, rec=0.5, Trec=60,
    # market structure (ASSUMED)
    D=2.0, Ka=0.05, kappa=0.03, c=0.005, fee=0.01, mfee=0.02, sI=0.003,
    Kc=0.03, hreq=0.20, tau=30.0, hz=0.2,
    lam_max=0.5, yh=0.10, s_l=0.10,
    g=0.06,
    # policies
    rho_level=1.0, th_b=0.01, ymax_c=0.20, Rref=0.10, ymax_d=0.50, th_d=0.02, w_d=0.03, vthr=0.01,
    so=0.01, delay=0,
    man_delta=0.0, man_start=200, man_T=0, wash=0.0, wash_T=0, flash=0.0, lock_min=0, phi_shift=0.0, drip=0.0, drip_T=0, shield=1.0, pref_shift=0.0,
    # controller / free-paid (ASSUMED)
    phi0=0.30, band=0.05, hl=30.0, rmin=0.005, rmax=0.50, req=0.03, eta=0.15, psi=0.10,
    s_phi=0.05, eps_d=0.10, s_d=0.05, sig_u=0.15, rho_u=0.97,
)
HET = dict(Ka=0.3, D=0.2, kappa=0.2, Kc=0.3)  # lognormal sd of per-run multipliers (ASSUMED)


def simulate(cells, R=300, T=730, seed=1, store_r=False):
    C = len(cells)
    cs = [{**DEFAULTS, **c} for c in cells]
    P = lambda k: np.array([c[k] for c in cs], float)[:, None]
    rng = np.random.default_rng(seed)
    # run heterogeneity and shock-day offsets: shared by all cells (pairing)
    het = {k: np.exp(HET[k] * rng.standard_normal(R))[None, :] for k in HET}
    off = rng.integers(-30, 31, R)[None, :]
    D = P('D') * het['D']; Ka = P('Ka') * het['Ka']; kap = P('kappa') * het['kappa']; Kc = P('Kc') * het['Kc']
    pol = P('pol'); trig = P('trig'); isE = ((pol == CTRL) | (pol == FREEFIX)).astype(float)
    ts = (P('ts') + off).astype(int); ts2 = ts + P('dsol').astype(int)
    f = P('f'); ell = P('ell'); c_ = P('c'); fee = P('fee'); mfee = P('mfee'); sI = P('sI')
    g = P('g'); nu = P('nu'); absorb = P('absorb'); rec = P('rec'); Trec = P('Trec'); fp0 = P('fp0'); chi = P('chi')
    hreq = P('hreq'); tau = P('tau'); hz = P('hz'); lam_max = P('lam_max'); yh = P('yh'); s_l = P('s_l')
    rho_level = P('rho_level'); th_b = P('th_b'); ymax_c = P('ymax_c'); Rref = P('Rref'); ymax_d = P('ymax_d')
    th_d = P('th_d'); w_d = P('w_d'); vthr = P('vthr'); so = P('so'); delay = P('delay').astype(int)
    man_delta = P('man_delta'); man_start = P('man_start'); man_T = P('man_T'); wash = P('wash'); wash_T = P('wash_T')
    flash = P('flash') * (P('lock_min') == 0); phi_shift = P('phi_shift'); shield = P('shield'); pref_shift = P('pref_shift'); drip = P('drip'); drip_T = P('drip_T')
    phi0 = P('phi0'); band = P('band'); k_ctrl = np.log(2) / P('hl'); rmin = P('rmin'); rmax = P('rmax'); req = P('req')
    eta = P('eta'); psi = P('psi'); s_phi = P('s_phi'); eps_d = P('eps_d'); s_d = P('s_d'); sig_u = P('sig_u'); rho_u = P('rho_u')
    shape = (C, R)
    Z = lambda v=0.0: np.full(shape, v)
    ci, ri = np.meshgrid(np.arange(C), np.arange(R), indexing='ij')
    H = np.ones((8, C, R))
    S = Z(1.0); F = phi0 * S; Pd = S - F; Rsv = Z(); cum_in = Z(); I = Z(); lam = Z(); Hc = Z(); u = Z()
    Kfree = Ka * np.ones(shape); ret = [Z(), Z(), Z()]
    Qred = Z(10.0); a_inf = Z(1.0); ell_net = Z(); a = Z(1.0); Labs = Z(); S_sh = Z(1.0)
    logr = np.log(req) * np.ones(shape); r = req * np.ones(shape); p = Z(1.0); v7 = Z(); a_r_prev = Z()
    first_event = np.minimum(ts, np.where(ell > 0, ts2, 10**6)); first_event = np.where((f > 0) | (ell > 0), first_event, ts)
    out = {k: Z() for k in ['maxdep', 'area', 'd99', 'd98', 'd95', 'spent', 'rebate_cost', 'sumy', 'sumy_false', 'false_pay',
                            'pay_total', 'Rshock', 'Rmin_after', 'absorbed', 'ell_net', 'redeemed', 'interest_extra', 'rmaxseen',
                            'rsum', 'rsq', 'flips', 'active_days', 'phimin', 'phimax', 'sumy_post', 'pay_man', 'sumy_man', 'wash_cost',
                            'flash_pay', 'Hc_peak', 'lam_peak', 'nrec_days', 'area1']}
    out['Rmin_after'] += 9.0; out['phimin'] += 9.0
    first99 = Z(-1.0); last99 = Z(-1.0); prevdir = Z(); sumlogdiff = Z(); Rend_init = Z()
    rpath = np.zeros((T // 10 + 1, C, R)) if store_r else None
    ppath = np.zeros((T // 5 + 1, C, R)) if store_r else None
    lampath = np.zeros((T // 5 + 1, C, R)) if store_r else None
    for t in range(T):
        z = rng.standard_normal((3, R))[None, :, :]
        # reserve inflow (3-12%/yr of debt, econ-m1)
        inflow = g / 365 * S; Rsv += inflow; cum_in += inflow
        # observed price (delay, noise, manipulation)
        H[t % 8] = p
        dl = H[(t - delay) % 8, ci, ri]
        manwin = (t >= man_start) & (t < man_start + man_T)
        pobs = dl * np.exp(so * z[:, 1:2, :][:, 0, :]) - man_delta * manwin
        dev_obs = 1 - pobs
        washnow = wash * ((t >= man_start) & (t < man_start + wash_T))
        # triggers
        v7eff = v7 + washnow * 7
        rho_act = np.where(trig == ORA, dev_obs > th_b, v7eff > vthr) * (pol == REBATE)
        y = np.zeros(shape)
        y = np.where(pol == RESYIELD, ymax_c * np.minimum(1, (Rsv / S) / Rref), y)
        yd = np.where(trig == ORA, ymax_d * np.clip((dev_obs - th_d) / w_d, 0, 1), ymax_d * np.clip((v7eff - vthr) / vthr, 0, 1))
        y = np.where(pol == DEVYIELD, yd, y)
        base = lam * S + Hc + flash * S
        due = y / 365 * base
        Sp = np.maximum(0, Rsv - nu * cum_in)
        pay = np.minimum(due, Sp)
        yeff = np.where(due > 0, y * pay / np.where(due > 0, due, 1), y * (Sp > 0))
        Rsv -= pay
        truedev = np.abs(1 - p)
        out['spent'] += pay; out['pay_total'] += pay
        out['false_pay'] += pay * (truedev < 0.01)
        out['sumy'] += yeff / 365; out['sumy_false'] += yeff / 365 * (truedev < 0.01)
        out['sumy_post'] += yeff / 365 * (t >= first_event)
        out['pay_man'] += pay * manwin; out['sumy_man'] += yeff / 365 * manwin
        out['flash_pay'] += (yeff / 365 * flash * S)
        out['wash_cost'] += washnow * 0.03
        # locking dynamics
        lam_star = lam_max * yeff / (yeff + yh)
        lam += s_l * (lam_star - lam)
        out['lam_peak'] = np.maximum(out['lam_peak'], lam); out['Hc_peak'] = np.maximum(out['Hc_peak'], Hc)
        # snapshots at first event
        atfirst = (t == first_event)
        out['Rshock'] = np.where(atfirst, Rsv, out['Rshock'])
        # shocks
        flow = np.zeros(shape)
        fl_act = ((t == ts) | (t == ts + 1)) & (f > 0)
        flow += fl_act * f / 2 * (1 - lam * shield)
        sol = (t == ts2) & (ell > 0)
        used = absorb * np.minimum(Rsv, ell * S) * sol
        Rsv -= used
        Labs = np.where(sol, ell * S - used, Labs)
        S_sh = np.where(sol, S, S_sh)
        ell_net = Labs / S_sh
        out['absorbed'] += used / S
        Es = np.maximum(0.2, 1 - ell / 0.29)  # calibrated on ONE figure: 26% of redemption demand finds no vault at 7.5% residual loss (FROZEN s5/s7)
        Xnow = np.where(isE > 0, F, S)
        Qred = np.where(sol, Es * Xnow, Qred)
        a_inf = np.where(ell > 0, np.maximum(0.05, 1 - Labs * (1 - rec) / S), 1.0)
        solwin = ((t == ts2) | (t == ts2 + 1)) & (ell > 0)
        flow += solwin * np.minimum(0.5, fp0 + ell_net) / 2 * (1 - lam * shield)
        flow += chi * pay
        flow += drip * ((t >= ts) & (t < ts + drip_T))
        a = np.where(t >= ts2, np.maximum(0.05, 1 - Labs * (1 - rec * np.clip((t - ts2) / Trec, 0, 1)) / S), 1.0)
        a = np.where(ell > 0, a, 1.0)
        # background demand noise, natural liquidity return
        I = I * (1 - kap) + flow + sI * z[:, 0:1, :][:, 0, :]
        # controller / free-paid borrower side
        if isE.any():
            phi = F / S - phi_shift * manwin
            lo, hi = phi0 - band, phi0 + band
            below = (phi < lo); above = (phi > hi)
            ctrl = (pol == CTRL)
            logr = np.where(ctrl, logr + k_ctrl * below - k_ctrl * above, logr)
            r = np.where(ctrl, np.clip(np.exp(logr), rmin, rmax), req)
            logr = np.where(ctrl, np.log(r), logr)
            dirn = below * 1.0 - above * 1.0
            out['flips'] += ctrl * ((dirn * prevdir) < 0); prevdir = np.where(dirn != 0, dirn, prevdir)
            out['active_days'] += ctrl * (dirn != 0)
            u = rho_u * u + np.sqrt(1 - rho_u ** 2) * z[:, 2:3, :][:, 0, :]
            phistar = np.clip(phi0 * np.exp(eta * 100 * (r - req) - psi * 100 * np.maximum(0, 1 - p) + sig_u * u + pref_shift * (t >= ts)), 0.02, 0.98)
            dF = isE * s_phi * (phistar * S - F)
            F = F + dF; Pd = Pd - dF
            Pstar = (1 - phi0) * np.exp(-eps_d * 100 * (r - req))
            dP = s_d * (Pstar - Pd) * isE * ctrl
            dP = np.where((dP > 0) & (p < 0.995), 0, dP)
            Pd = Pd + dP; S = S + dP; I = I + dP
            out['interest_extra'] += ctrl * (r - req) * Pd / 365
            out['rsum'] += ctrl * np.log(r / req); out['rsq'] += ctrl * np.log(r / req) ** 2
            out['rmaxseen'] = np.maximum(out['rmaxseen'], np.where(ctrl, r, 0))
            out['phimin'] = np.where(isE > 0, np.minimum(out['phimin'], F / S), out['phimin'])
            out['phimax'] = np.where(isE > 0, np.maximum(out['phimax'], F / S), out['phimax'])
        # price, redemption arbitrage
        p = np.clip(a - I / D, 0.02, 1.5)
        fee_eff = fee * (1 - rho_act * rho_level)
        pa = 1 - fee_eff - c_
        Ineed = np.maximum(0, I - D * (a - pa))
        cap = np.maximum(0, np.minimum(Qred, np.where(isE > 0, F, S)))
        a_r = np.minimum(np.minimum(Ineed, Kfree), cap)
        rc = a_r * fee * rho_level * rho_act
        rc_pay = np.minimum(rc, np.maximum(0, Rsv - nu * cum_in))
        # if reserve cannot fund the rebate, rebate only partially paid (cost capped)
        Rsv -= rc_pay; out['rebate_cost'] += rc_pay; out['spent'] += rc_pay
        out['redeemed'] += a_r
        Qred = Qred - a_r
        S = S - a_r; F = np.where(isE > 0, F - a_r, F)
        I = I - a_r; Kfree = Kfree - a_r + ret[t % 3]; ret[t % 3] = a_r.copy()
        # mint arbitrage above the peg
        p = np.clip(a - I / D, 0.02, 1.5)
        pm = 1 + mfee + c_
        a_m = np.clip(D * (a - pm) - I, 0, 0.1)
        S = S + a_m; Pd = Pd + a_m * (1 - phi0 * isE); I = I + a_m
        F = F + a_m * phi0 * isE
        # yield-chasing carry capital
        p = np.clip(a - I / D, 0.02, 1.5)
        pc = np.minimum(1.0, a_inf / (1 + (hreq - yeff) * tau / 365))
        Itar = D * (a - pc)
        buy = np.where(p < pc, np.clip(I - Itar, 0, np.maximum(0, Kc - Hc)), 0)
        sell = np.where(p > pc * 1.002, hz * Hc, 0)
        Hc = Hc + buy - sell; I = I - buy + sell
        p = np.clip(a - I / D, 0.02, 1.5)
        # metrics
        inwin = (t >= first_event - 1)
        dep = np.maximum(0, 1 - p)
        out['maxdep'] = np.maximum(out['maxdep'], dep * inwin)
        out['area'] += 100 * dep * inwin
        out['area1'] += 100 * np.maximum(0, 0.99 - p) * inwin
        b99 = (p < 0.99) & inwin; b98 = (p < 0.98) & inwin; b95 = (p < 0.95) & inwin
        out['d99'] += b99; out['d98'] += b98; out['d95'] += b95
        first99 = np.where((first99 < 0) & b99, t, first99); last99 = np.where(b99, t, last99)
        out['Rmin_after'] = np.where(t >= first_event, np.minimum(out['Rmin_after'], Rsv / S), out['Rmin_after'])
        v7 = v7 * (1 - 1 / 7) + a_r
        if store_r:
            if t % 10 == 0: rpath[t // 10] = r
            if t % 5 == 0: ppath[t // 5] = p; lampath[t // 5] = lam
    out['ell_net'] = ell_net; out['Rend'] = Rsv / S; out['Send'] = S
    out['span99'] = np.where(first99 >= 0, last99 - first99 + 1, 0)
    out['recovery_ts'] = out['span99']
    if store_r: out['rpath'] = rpath; out['ppath'] = ppath; out['lampath'] = lampath
    return out


def summarize(out, key, c_idx):
    x = out[key][c_idx]
    return x.mean(), x.std(ddof=1) / np.sqrt(len(x))


def chunked(cells, R=300, T=730, seed=1, chunk=40, store_r=False):
    """Run cells in chunks; returns list of per-cell dict of arrays (R,)."""
    res = []
    for i in range(0, len(cells), chunk):
        o = simulate(cells[i:i + chunk], R=R, T=T, seed=seed, store_r=store_r)
        for j in range(len(cells[i:i + chunk])):
            res.append({k: (v[:, j] if k in ('rpath', 'ppath', 'lampath') and False else v[j] if v.ndim == 2 else v[:, j]) for k, v in o.items()})
    return res
