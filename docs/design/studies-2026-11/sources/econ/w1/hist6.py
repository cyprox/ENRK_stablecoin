"""Why: ECON-V6 history analysis on the a4 dataset: baseline conventions, L options, energy sources, fee/adoption legs, clip/rate limit
(decision: owner brief 2026-11-11; P15 a,b,c,d,f). numpy + stdlib. Inputs: daily.csv (a4) and xraw/*.csv (public FRED GETs, 2026-11-11).
Usage: python3 -B hist6.py > hist6_out.txt   (writes hist6.json)"""
import csv, json, datetime as dt, sys
import numpy as np
sys.dont_write_bytecode = True
rows = list(csv.DictReader(open('daily.csv')))
dates = [dt.date.fromisoformat(r['date']) for r in rows]
def col(k):
    x = np.array([float(r[k]) if r[k] not in ('', 'None') else np.nan for r in rows])
    for i in range(1, len(x)):
        if np.isnan(x[i]): x[i] = x[i - 1]
    return x
K = col('kas'); H = col('hashrate_PHs'); TX = col('tx_regular'); AD = col('active_addr_hoursum'); EN = col('energy_idx'); EL = col('elec_usd_kwh')
n = len(K)
def trail(x, m, f=np.mean):
    return np.array([f(x[max(0, i - m + 1):i + 1]) for i in range(len(x))])
F = trail(TX, 7); A = trail(AD, 30)                       # a4 stand-ins (spam-polluted)
Fr = trail(TX, 30, np.median); Ar = trail(AD, 30, np.median)   # spam-robust variants (30d rolling median)
Hs = trail(H, 30, np.median)
def fred(id_):
    d = {}
    for r in csv.DictReader(open(f'xraw/{id_}.csv')):
        v = r[id_]
        if v not in ('', '.'): d[dt.date.fromisoformat(r['observation_date'])] = float(v)
    return d
def daily_ff(d, lag_days=0):
    ks = sorted(d); out = np.empty(n); j = -1
    for i, t in enumerate(dates):
        while j + 1 < len(ks) and ks[j + 1] + dt.timedelta(days=lag_days) <= t: j += 1
        out[i] = d[ks[max(j, 0)]]
    return out
CPIEL = daily_ff(fred('CUSR0000SEHF01')); PPIEL = daily_ff(fred('PCU221122221122')); HH = daily_ff(fred('DHHNGSP')); EUG = daily_ff(fred('PNGASEUUSDM'))
# Kaspa-native: break-even electricity price implied by KAS price, emission and hashrate (emission ASSUMED smooth: halves every 12 months, only the shape matters)
months = np.array([(t.year - 2022) * 12 + t.month - 5 + t.day / 30.0 for t in dates])
EMIT = 0.5 ** (months / 12.0)
BREAKEVEN = K * EMIT / H            # USD revenue per PH/s-day, proportional to the break-even electricity price at constant efficiency
NETCOST = H * EL                    # network electricity bill proxy at constant efficiency: hashrate x US retail price
clip = lambda x, lo=.1, hi=5.: np.minimum(np.maximum(x, lo), hi)
def base(x, mode):
    if mode == 'launch': return np.full_like(x, x[:7].mean())
    if mode == 'fullmean': return np.full_like(x, x.mean())
    if mode == 'trail365': return trail(x, 365)
    if mode == 'fixed2024': i = dates.index(dt.date(2024, 1, 1)); return np.full_like(x, x[i - 29:i + 1].mean())
BASES = ('launch', 'fullmean', 'trail365', 'fixed2024')
W4 = (.40, .30, .20, .10)
def comp(x, mode): return clip(x / base(x, mode))
def index(mode, h=H, e=EN, f=None, a=None, w=W4, lo=.1, hi=5.):
    cs = [comp(h, mode), comp(e, mode), comp(f, mode) if f is not None else np.ones(n), comp(a, mode) if a is not None else np.ones(n)]
    return clip(sum(wi * c for wi, c in zip(w, cs)), lo, hi)
def start_of(mode): return 365 if mode == 'trail365' else 0
def metrics(I, st=0, hz=(90, 180, 365), icr0=2.0, mcr=1.5):
    lk, li = np.log(K[st:]), np.log(I[st:])
    wk = lk[7::7] - lk[:-7:7][:len(lk[7::7])]; wi = li[7::7] - li[:-7:7][:len(li[7::7])]; m = min(len(wk), len(wi)); wk, wi = wk[:m], wi[:m]
    k30 = lk[30:] - lk[:-30]; i30 = li[30:] - li[:-30]
    o = dict(vol=float(wi.std(ddof=1) * np.sqrt(52)), corr_w=float(np.corrcoef(wk, wi)[0, 1]) if wi.std() > 0 else None,
             corr_30=float(np.corrcoef(k30, i30)[0, 1]) if i30.std() > 0 else None,
             out11=float(np.mean((I[st:] < .89) | (I[st:] > 1.11))), imin=float(I[st:].min()), imax=float(I[st:].max()),
             at_hi5=float(np.mean(I[st:] >= 5 - 1e-9)), idx_up_kas_down30=float(np.mean((i30 > 0) & (k30 < 0))))
    for h in hz:
        mj, mk = [], []
        for s in range(st, n - h):
            rel = (K[s:s + h + 1] / K[s]) / (I[s:s + h + 1] / I[s]); mj.append(icr0 * rel.min()); mk.append(icr0 * (K[s:s + h + 1] / K[s]).min())
        mj, mk = np.array(mj), np.array(mk)
        o[f'touch{h}'] = float(np.mean(mj < mcr)); o[f'touchK{h}'] = float(np.mean(mk < mcr)); o[f'lt100_{h}'] = float(np.mean(mj < 1)); o[f'lt100K_{h}'] = float(np.mean(mk < 1))
    r365 = I[st + 365:] / I[st:-365] - 1 if n - st > 366 else np.array([0.])
    o['ret365_p5'], o['ret365_med'], o['ret365_p95'] = [float(np.percentile(r365, q)) for q in (5, 50, 95)]
    return o
def pr(title, rowsd, cols):
    print('\n' + title); print('| variant | ' + ' | '.join(cols) + ' |'); print('|' + '---|' * (len(cols) + 1))
    for k, v in rowsd.items():
        print('| ' + k + ' | ' + ' | '.join('%s' % (('%.2f' % v[c]) if isinstance(v[c], float) else v[c]) for c in cols) + ' |')
J = {}
# ------------------------------------------------------------------ (b) baseline conventions
print('(b) BASELINE CONVENTION. Opening ICR 200%, MCR 150%; touch = share of start dates whose ICR (KAS and index) goes below 150% within the horizon; K-only = KAS alone.')
for proxies in ('HE', 'full'):
    R = {}
    for b in BASES:
        I = index(b, f=F if proxies == 'full' else None, a=A if proxies == 'full' else None)
        st = start_of(b); R[b] = metrics(I, st)
        R[b]['I_2024_11_04_over_I_2024_07_31'] = float(I[dates.index(dt.date(2024, 11, 4))] / I[dates.index(dt.date(2024, 7, 31))])
        i0, i1 = dates.index(dt.date(2024, 7, 31)), dates.index(dt.date(2024, 11, 4)); R[b]['icr_2024_11_04_pct'] = float(200 * (K[i1] / K[i0]) / (I[i1] / I[i0])) if (st <= i0) else None
        R[b]['icr_K_only_2024_11_04_pct'] = float(200 * K[i1] / K[i0])
    J['baseline|' + proxies] = R
    pr(f'proxies={proxies}, energy=IMF idx', R, ['vol', 'corr_w', 'corr_30', 'out11', 'imin', 'imax', 'at_hi5', 'touch90', 'touchK90', 'touch180', 'touchK180', 'touch365', 'touchK365', 'lt100_180', 'lt100K_180', 'icr_2024_11_04_pct', 'icr_K_only_2024_11_04_pct', 'ret365_p5', 'ret365_med', 'ret365_p95'])
# ------------------------------------------------------------------ (a) L options
print('\n(a) L OPTIONS (index unit USD value). Debt USD = D * L * I. fullmean baseline, window = full sample; "touch180" as above.')
ELn = EL / EL.mean(); ENn = EN / EN.mean()
L = {
    'L1: I as coded (HE legs), L=1 at launch, drifts': index('fullmean'),
    'L1b: I as coded, noisy F/A proxies': index('fullmean', f=F, a=A),
    'L2a: USD-anchored basket = US retail electricity only': ELn,
    'L2b: USD-anchored basket = IMF energy index only': ENn,
    'L2c: USD-anchored 50% elec + 50% IMF energy': .5 * ELn + .5 * ENn,
    'L3: unit fixed at 1 USD (index not used in ICR)': np.ones(n),
}
R = {k: metrics(v) for k, v in L.items()}; J['L'] = R
pr('L options', R, ['vol', 'corr_w', 'imin', 'imax', 'touch90', 'touchK90', 'touch180', 'touchK180', 'lt100_180', 'lt100K_180', 'ret365_p5', 'ret365_med', 'ret365_p95'])
# ------------------------------------------------------------------ (c) energy sources
print('\n(c) ENERGY SOURCES (monthly log returns over 2023-03..2026-10; KAS month-end). cadence = how often the source is revised; lag = publication delay (ASSUMED typical).')
def month_end_idx():
    out = []
    for i in range(n - 1):
        if dates[i].month != dates[i + 1].month: out.append(i)
    out.append(n - 1); return out
me = month_end_idx()
SRC = {'IMF energy index (FRED PNRGINDEXM)': (EN, 'monthly', '~1 month'), 'US retail electricity (APU000072610)': (EL, 'monthly', '~2-6 weeks'),
       'US CPI electricity (CUSR0000SEHF01)': (CPIEL, 'monthly', '~2-6 weeks'), 'US PPI electric power (PCU221122221122)': (PPIEL, 'monthly', '~1.5 months'),
       'Henry Hub gas (DHHNGSP)': (HH, 'daily', '1 day'), 'EU gas (PNGASEUUSDM)': (EUG, 'monthly', '~1 month'),
       'Kaspa break-even price K*emission/H': (BREAKEVEN, 'every block/day (on-chain + KAS oracle)', 'none'),
       'Kaspa network bill H x US elec': (NETCOST, 'daily + monthly external', '~1 month')}
R = {}
lk = np.log(K[me]); mk = np.diff(lk)
for k, (x, cad, lag) in SRC.items():
    lx = np.log(x[me]); mx = np.diff(lx)
    d30 = np.log(x[30:] / x[:-30]); k30 = np.log(K[30:] / K[:-30])
    R[k] = dict(vol_m=float(mx.std(ddof=1) * np.sqrt(12)), corr_m=float(np.corrcoef(mk, mx)[0, 1]) if mx.std() > 0 else None,
                corr_30=float(np.corrcoef(k30, d30)[0, 1]) if d30.std() > 0 else None, maxup_m=float(np.exp(mx.max()) - 1), maxdn_m=float(np.exp(mx.min()) - 1),
                chg_total=float(x[-1] / x[0] - 1), cadence=cad, lag=lag, nchg=int(np.sum(np.diff(x) != 0)))
J['energy'] = R
pr('energy sources', R, ['vol_m', 'corr_m', 'corr_30', 'maxup_m', 'maxdn_m', 'chg_total', 'nchg', 'cadence', 'lag'])
print('   corr of source with hashrate (monthly log returns):', {k: round(float(np.corrcoef(np.diff(np.log(H[me])), np.diff(np.log(x[me])))[0, 1]), 2) for k, (x, _, _) in SRC.items()})
# ------------------------------------------------------------------ (d) legs
print('\n(d) FEE / ADOPTION LEGS. baseline=fullmean (hindsight; a4 default), energy = IMF idx unless noted.')
Hn = lambda x, b='fullmean': comp(x, b)
def V(b):
    return {
        'V0 coded 4/3/2/1 with tx7d & addr30d proxies (spam-polluted)': index(b, f=F, a=A),
        'V1 4/3/2/1 with F=A=1 held flat (a4 HE)': index(b),
        'V2 H+E re-weighted .571/.429': index(b, w=(.571, .429, 0, 0)),
        'V3 H+E .5/.5': index(b, w=(.5, .5, 0, 0)),
        'V4 H only': index(b, w=(1, 0, 0, 0)),
        'V5 E only (IMF)': index(b, w=(0, 1, 0, 0)),
        'V6 E only (US elec)': index(b, e=EL, w=(0, 1, 0, 0)),
        'V7 4/3/2/1, F,A = 30d rolling MEDIAN of tx, addr': index(b, f=Fr, a=Ar),
        'V8 H(30d median) + E re-weighted .571/.429': index(b, h=Hs, w=(.571, .429, 0, 0)),
        'V9 H+E+KAS-price leg: .4 H + .3 E + .3 K(90d mean)': clip(.4 * Hn(H, b) + .3 * Hn(EN, b) + .3 * clip(trail(K, 90) / base(trail(K, 90), b))),
        'V10 H+E with US-elec as E: .571/.429': index(b, e=EL, w=(.571, .429, 0, 0)),
        'V11 H*E network-bill index': clip(Hn(H * EL, b)),
    }
for b in ('fullmean', 'trail365', 'fixed2024'):
    R = {k: metrics(v, start_of(b)) for k, v in V(b).items()}; J['legs|' + b] = R
    pr(f'legs, baseline={b}', R, ['vol', 'corr_w', 'corr_30', 'out11', 'imin', 'imax', 'at_hi5', 'touch180', 'touchK180', 'lt100_180', 'lt100K_180', 'ret365_p5', 'ret365_med', 'ret365_p95'])
b = 'fullmean'; I0 = V(b)['V1 4/3/2/1 with F=A=1 held flat (a4 HE)']
print('   pinned fractions (fullmean): fee proxy comp at 0.1 floor', float(np.mean(comp(F, b) <= .1)), ' at 5.0', float(np.mean(comp(F, b) >= 5)), '; adoption proxy at floor', float(np.mean(comp(A, b) <= .1)), ' at 5', float(np.mean(comp(A, b) >= 5)))
print('   coded F (avg fee 100-122 sompi/gram, ~0.002 KAS vs baseline 0.1 KAS) = 0.02-0.1 before clip -> clipped to 0.1: a CONSTANT 0.1 leg (see a4 s0.7). Effect of coded F=0.1 and A=1: index shifts down by 0.2*(1-0.1)=0.18 vs F=1.')
Ic = clip(.4 * comp(H, 'fullmean') + .3 * comp(EN, 'fullmean') + .2 * 0.1 + .1 * 1.0)
R = {'coded: F pinned 0.1, A=1': metrics(Ic), 'F=A=1 (a4 HE)': metrics(I0)}; J['legs|coded_pinned'] = R
pr('coded F pinned vs flat', R, ['vol', 'corr_w', 'imin', 'imax', 'touch180', 'touchK180', 'ret365_p5', 'ret365_med', 'ret365_p95'])
# ------------------------------------------------------------------ (f) clip, slope and rate limit on the history
print('\n(f) CLIP / RATE LIMIT applied to the published index on history (base: fullmean/HE; also fullmean/full noisy and trail365/HE).')
def shape(I, lo=.1, hi=5., slope=1., step=0.):
    out = np.empty_like(I); last = I[0]
    for t in range(len(I)):
        v = I[t]
        if slope != 1. and v > 1: v = 1 + slope * (v - 1)
        v = min(max(v, lo), hi)
        if step > 0: v = min(max(v, last * (1 - step)), last * (1 + step))
        out[t] = v; last = v
    return out
SH = {'frozen [0.1,5]': {}, 'hi 2.0': dict(hi=2.), 'hi 1.5': dict(hi=1.5), 'hi 1.25': dict(hi=1.25), 'hi 1.10': dict(hi=1.1), '[0.5,2]': dict(lo=.5, hi=2.), '[0.8,1.25]': dict(lo=.8, hi=1.25),
      'slope .5 above 1': dict(slope=.5), 'step 1%/day': dict(step=.01), 'step .5%/day': dict(step=.005), 'step .25%/day': dict(step=.0025), 'step .1%/day': dict(step=.001),
      'step .5%/day + hi 1.5': dict(step=.005, hi=1.5)}
for nm, I, st in (('fullmean/HE', index('fullmean'), 0), ('fullmean/full(noisy)', index('fullmean', f=F, a=A), 0), ('trail365/HE', index('trail365'), 365)):
    R = {}
    for k, kw in SH.items():
        Is = shape(I, **kw); m = metrics(Is, st); m['rms_log_gap_vs_raw'] = float(np.sqrt(np.mean(np.log(Is[st:] / I[st:]) ** 2))); R[k] = m
    J['shape|' + nm] = R
    pr(f'shaping on {nm}', R, ['vol', 'imin', 'imax', 'touch90', 'touch180', 'touchK180', 'lt100_180', 'lt100K_180', 'rms_log_gap_vs_raw', 'ret365_p5', 'ret365_med', 'ret365_p95'])
json.dump(J, open('hist6.json', 'w'), indent=1)
