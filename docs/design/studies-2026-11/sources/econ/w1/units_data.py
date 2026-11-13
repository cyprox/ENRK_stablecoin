"""Why: ECON-W1 unit-of-account history: builds the USD value of each candidate unit (U0..U6) and the history tables
(decision: owner question 2026-11-11, step 1a; TEST only, no design decision). numpy + stdlib; python3 -I -B units_data.py > units_hist_out.md
Inputs (public keyless GETs 2026-11-11, saved in data/): FRED DEXCHUS (USD/CNY, Fed H.10 onshore), DEXUSEU, APU000072610 (US retail electricity),
ECB eurofxref-hist.csv, Yahoo chart API GC=F (COMEX gold futures, unofficial), daily.csv (a4 KAS dataset), v6/out coded index (hindsight HE and noisy full).
Unit value u(t) = USD value of one unit of account (arbitrary scale). KAS in unit = KAS_USD / u. Vault: collateral C KAS, debt D units fixed => ICR(t)=ICR0 * (K/K0)/(u/u0)."""
import csv, json, datetime as dt, sys, os
import numpy as np
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
def fred(path, col):
    d = {}
    for r in csv.DictReader(open(path)):
        v = r[col]
        if v not in ("", "."): d[dt.date.fromisoformat(r["observation_date"])] = float(v)
    return d
def ffill(d, dates, lag=0):
    ks = sorted(d); out = np.empty(len(dates)); j = -1
    for i, t in enumerate(dates):
        while j + 1 < len(ks) and ks[j + 1] + dt.timedelta(days=lag) <= t: j += 1
        out[i] = d[ks[max(j, 0)]]
    return out
def ecb():
    rows = list(csv.DictReader(open(os.path.join(D, "eurofxref-hist.csv"))))
    u, c = {}, {}
    for r in rows:
        try: u[dt.date.fromisoformat(r["Date"])] = float(r["USD"]); c[dt.date.fromisoformat(r["Date"])] = float(r["CNY"])
        except ValueError: pass
    return u, c
def yahoo(path):
    j = json.load(open(path))["chart"]["result"][0]; out = {}
    for t, v in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]):
        if v is not None: out[dt.date.fromtimestamp(t)] = float(v)
    return out
def kas_rows():
    rows = list(csv.DictReader(open(os.path.join(HERE, "daily.csv"))))
    return [dt.date.fromisoformat(r["date"]) for r in rows], np.array([float(r["kas"]) for r in rows])
def coded_index(name):
    d = {}
    for r in csv.DictReader(open(os.path.join(HERE, "..", "v6", "out", name))): d[dt.date.fromisoformat(r["date"])] = float(r["index"])
    return d

def unit_series(dates):
    """USD value of each unit on `dates` (normalised to 1 on dates[0])."""
    cny = 1.0 / ffill(fred(f"{D}/DEXCHUS.csv", "DEXCHUS"), dates)
    eur = ffill(fred(f"{D}/DEXUSEU.csv", "DEXUSEU"), dates)
    ue, ce = ecb(); ecb_cny = ffill({k: ue[k] / ce[k] for k in ue if k in ce}, dates)   # USD per CNY = (USD/EUR)/(CNY/EUR)
    elec = ffill(fred(os.path.join(HERE, "xraw", "APU000072610.csv"), "APU000072610"), dates)
    elec45 = ffill(fred(os.path.join(HERE, "xraw", "APU000072610.csv"), "APU000072610"), dates, lag=45)
    gold = ffill(yahoo(f"{D}/y_GCF.json"), dates)
    rub = 1.0 / ffill(fred(f"{D}/cbr_usdrub.csv", "USDRUB_CBR"), dates)     # CBR official USD/RUB, USD value of 1 RUB
    raw = ffill(coded_index("index_fullmean_idx_HE.csv"), dates); rawf = ffill(coded_index("index_fullmean_idx_full.csv"), dates)
    pub = raw.copy()
    for i in range(1, len(pub)): pub[i] = min(raw[i], pub[i - 1] * 1.0025)       # slow-up (0.25%/day) / immediate-down
    s = {"U1_USD": np.ones(len(dates)), "U2_CNY_FRED": cny, "U2e_CNY_ECB": ecb_cny, "U3_basket": (1 + eur / eur[0] + cny / cny[0]) / 3,
         "U3b_USD_CNY_RUB_eq": (1 + cny / cny[0] + rub / rub[0]) / 3, "U3b_USD50_CNY30_RUB20": .5 + .3 * cny / cny[0] + .2 * rub / rub[0],
         "U3c_USD_EUR_CNY_RUB_eq4": (1 + eur / eur[0] + cny / cny[0] + rub / rub[0]) / 4, "RUB_alone": rub, "U4_elec": elec, "U4l_elec_lag45": elec45, "U6_gold": gold, "U0_coded_HE": raw, "U0n_coded_noisy": rawf, "U5_coded_HE_up0.25%": pub}
    return {k: v / v[0] for k, v in s.items()}

def lr(x): return np.diff(np.log(x))
def hist_table(dates, K, S):
    n = len(K); out = {}
    kr = lr(K); k30 = np.log(K[30:] / K[:-30]); kw = np.log(K[7::7][:] / K[:-7:7][:len(K[7::7])])
    for name, u in S.items():
        ur = lr(u); o = {}
        o["vol"] = float(ur.std(ddof=1) * np.sqrt(365)); o["drift"] = float(np.log(u[-1] / u[0]) / ((n - 1) / 365.0))
        o["corr_d"] = float(np.corrcoef(kr, ur)[0, 1]) if ur.std() > 0 else None
        u30 = np.log(u[30:] / u[:-30]); o["corr_30"] = float(np.corrcoef(k30, u30)[0, 1]) if u30.std() > 0 else None
        o["w1_up"], o["w1_dn"] = float(np.exp(ur.max()) - 1), float(np.exp(ur.min()) - 1)
        o["w30_up"], o["w30_dn"] = float(np.exp(u30.max()) - 1), float(np.exp(u30.min()) - 1)
        o["umin"], o["umax"] = float(u.min()), float(u.max())
        Ku = K / u; o["kas_unit_vol"] = float(lr(Ku).std(ddof=1) * np.sqrt(365))
        for h in (90, 180, 365):
            t, t100 = [], []
            for s in range(0, n - h):
                m = ((K[s:s + h + 1] / K[s]) / (u[s:s + h + 1] / u[s])).min(); t.append(2.0 * m < 1.5); t100.append(2.0 * m < 1.0)
            o[f"touch{h}"] = float(np.mean(t)); o[f"lt100_{h}"] = float(np.mean(t100))
        # worst ICR change attributable to the unit within 60d windows: ratio u_t/u_s extremes
        r365 = u[365:] / u[:-365] - 1; o["ret365_p5"], o["ret365_med"], o["ret365_p95"] = [float(np.percentile(r365, q)) for q in (5, 50, 95)]
        out[name] = o
    return out
def vault_table(dates, K, S, opens):
    res = {}
    for d0 in opens:
        s = dates.index(d0); e = min(s + 180, len(K) - 1); row = {}
        for name, u in S.items():
            rel = (K[s:e + 1] / K[s]) / (u[s:e + 1] / u[s]); row[name] = (float(2 * rel.min() * 100), float(2 * rel[-1] * 100))
        res[d0.isoformat()] = row
    return res

def long_fx():
    """long history (2005-07-25..2026-11-06) of the USD value of CNY, EUR, basket (1/3 each, fixed quantities at window start), gold, electricity."""
    cn = fred(f"{D}/DEXCHUS.csv", "DEXCHUS"); eu = fred(f"{D}/DEXUSEU.csv", "DEXUSEU"); gd = yahoo(f"{D}/y_GCF.json"); rb = fred(f"{D}/cbr_usdrub.csv", "USDRUB_CBR")
    e0 = dt.date(2005, 7, 25); e1 = dt.date(2026, 11, 6)
    dates = [e0 + dt.timedelta(days=i) for i in range((e1 - e0).days + 1)]
    cny = 1.0 / ffill(cn, dates); eur = ffill(eu, dates); gold = ffill(gd, dates); rub = 1.0 / ffill(rb, dates)
    el = ffill(fred(os.path.join(HERE, "xraw", "APU000072610.csv"), "APU000072610"), dates)
    return dates, {"CNY": cny, "EUR": eur, "gold": gold, "elec": el, "RUB": rub}
def window_stats(dates, S, h):
    out = {}
    cn, eu = S["CNY"], S["EUR"]
    rb = S["RUB"]
    for name in ("CNY", "EUR", "basket", "RUB", "basketRUB_eq", "basketRUB_50_30_20", "gold", "elec"):
        if name == "basket": r = (1 + eu[h:] / eu[:-h] + cn[h:] / cn[:-h]) / 3
        elif name == "basketRUB_eq": r = (1 + cn[h:] / cn[:-h] + rb[h:] / rb[:-h]) / 3
        elif name == "basketRUB_50_30_20": r = .5 + .3 * cn[h:] / cn[:-h] + .2 * rb[h:] / rb[:-h]
        else: r = S[name][h:] / S[name][:-h]
        r = r - 1
        out[name] = dict(up_max=float(r.max()), up_date=dates[int(r.argmax()) + h].isoformat(), dn_min=float(r.min()), dn_date=dates[int(r.argmin()) + h].isoformat(),
                         p_up5=float(np.mean(r > .05)), p_up10=float(np.mean(r > .10)), p_up20=float(np.mean(r > .20)),
                         p_dn5=float(np.mean(r < -.05)), p_dn10=float(np.mean(r < -.10)), p_dn20=float(np.mean(r < -.20)), sd=float(np.log1p(r).std(ddof=1)),
                         p95=float(np.percentile(r, 95)), p5=float(np.percentile(r, 5)))
    return out
EPIS = [("CNY 2005-07-25..2008-07-18 (managed appreciation)", "2005-07-25", "2008-07-18"), ("CNY 2015-08-07..2015-09-07 (11 Aug 2015 fixing reform)", "2015-08-07", "2015-09-07"),
        ("CNY 2015-08-10..2016-12-30 (devaluation run)", "2015-08-10", "2016-12-30"), ("CNY 2017-01-03..2017-09-08 (reappreciation)", "2017-01-03", "2017-09-08"),
        ("CNY 2018-04-17..2018-10-31 (trade-war devaluation)", "2018-04-17", "2018-10-31"), ("CNY 2019-08-01..2019-09-03 (breach of 7.0)", "2019-08-01", "2019-09-03"),
        ("CNY 2020-05-27..2021-05-31 (reappreciation)", "2020-05-27", "2021-05-31"), ("CNY 2022-03-31..2022-11-04 (devaluation)", "2022-03-31", "2022-11-04"),
        ("EUR 2008-07-15..2008-11-05", "2008-07-15", "2008-11-05"), ("EUR 2014-05-08..2015-03-13", "2014-05-08", "2015-03-13"),
        ("RUB 2014-07-01..2015-01-30 (2014 crisis)", "2014-07-01", "2015-01-30"), ("RUB 2014-12-10..2014-12-18 (week of 16 Dec 2014)", "2014-12-10", "2014-12-18"), ("RUB 2022-02-22..2022-03-10 (invasion, exchange closed 28 Feb-23 Mar 2022)", "2022-02-22", "2022-03-10"), ("RUB 2022-03-10..2022-06-24 (re-appreciation, official rate)", "2022-03-10", "2022-06-24"), ("RUB 2008-07-15..2009-02-02", "2008-07-15", "2009-02-02"), ("gold 2013-04-01..2013-06-28", "2013-04-01", "2013-06-28"), ("gold 2008-03-17..2008-10-24", "2008-03-17", "2008-10-24"), ("gold 2020-08-06..2020-09-24", "2020-08-06", "2020-09-24")]

def pc(x, d=1): return "n/a" if x is None else f"{100 * x:+.{d}f}%"
if __name__ == "__main__":
    dates, K = kas_rows()
    # trim to the last FRED date (2026-11-06): FX series are forward-filled after it, so cut there
    cut = dt.date(2026, 11, 6); n = dates.index(cut) + 1; dates, K = dates[:n], K[:n]
    S = unit_series(dates); H = hist_table(dates, K, S)
    J = {"hist": H, "period": [dates[0].isoformat(), dates[-1].isoformat()], "n": len(dates)}
    print(f"# ECON-W1 unit history, {dates[0]}..{dates[-1]} ({len(dates)} days), KAS from a4 daily.csv. Opening ICR 200%, MCR 150%, debt fixed in the unit.")
    print("\n## H1. Unit value u(t) in USD (annualised, daily log returns) and link with KAS. touch = share of start dates whose ICR goes below 150% within the horizon; lt100 = below 100%")
    print("| unit | vol/yr | drift/yr | corr(KAS,u) daily / 30d | worst 1d up / dn | worst 30d up / dn | u min..max | 365d return p5/med/p95 | KAS-in-unit vol | touch 90/180/365 | ICR<100% 180d |")
    print("|" + "---|" * 12)
    for k, o in H.items():
        print(f"| {k} | {pc(o['vol'])} | {pc(o['drift'])} | {o['corr_d']:+.2f} / {o['corr_30']:+.2f} | {pc(o['w1_up'])} / {pc(o['w1_dn'])} | {pc(o['w30_up'])} / {pc(o['w30_dn'])} | {o['umin']:.2f}..{o['umax']:.2f} | {pc(o['ret365_p5'],0)} / {pc(o['ret365_med'],0)} / {pc(o['ret365_p95'],0)} | {pc(o['kas_unit_vol'],0)} | {100*o['touch90']:.0f} / {100*o['touch180']:.0f} / {100*o['touch365']:.0f}% | {100*o['lt100_180']:.0f}% |" if o['corr_d'] is not None else
              f"| {k} | {pc(o['vol'])} | {pc(o['drift'])} | n/a | n/a | n/a | {o['umin']:.2f}..{o['umax']:.2f} | {pc(o['ret365_p5'],0)} / {pc(o['ret365_med'],0)} / {pc(o['ret365_p95'],0)} | {pc(o['kas_unit_vol'],0)} | {100*o['touch90']:.0f} / {100*o['touch180']:.0f} / {100*o['touch365']:.0f}% | {100*o['lt100_180']:.0f}% |")
    opens = [dt.date(2023, 6, 1), dt.date(2023, 12, 1), dt.date(2024, 5, 1), dt.date(2024, 7, 31), dt.date(2024, 11, 4), dt.date(2025, 3, 1), dt.date(2025, 8, 1), dt.date(2026, 1, 15)]
    opens = [d for d in opens if d in dates and dates.index(d) + 180 < len(dates)]
    V = vault_table(dates, K, S, opens); J["vaults"] = V
    print("\n## H2. ICR (%) of a vault opened at 200% on the date shown, in the 180 following days: minimum / at day 180")
    names = list(S)
    print("| open date | KAS-only(USD) | " + " | ".join(n for n in names if n != "U1_USD") + " |"); print("|" + "---|" * (len(names) + 1))
    for d0, row in V.items():
        print(f"| {d0} | {row['U1_USD'][0]:.0f} / {row['U1_USD'][1]:.0f} | " + " | ".join(f"{row[n][0]:.0f} / {row[n][1]:.0f}" for n in names if n != "U1_USD") + " |")
    # data-source agreement
    a, b = S["U2_CNY_FRED"], S["U2e_CNY_ECB"]; d = lr(a) - lr(b)
    print(f"\n## H3. Source cross-check: USD value of CNY from FRED H.10 vs ECB cross (USD/EUR over CNY/EUR): level ratio min..max {np.min(a/b):.4f}..{np.max(a/b):.4f}; daily log-return difference sd {100*d.std():.3f}%, max |diff| {100*np.abs(d).max():.2f}%; vol FRED {pc(lr(a).std()*365**.5)} ECB {pc(lr(b).std()*365**.5)}.")
    dd, S2 = long_fx(); L = {}
    print("\n## H4. Long history 2005-07-25..2026-11-06 (CNY float era; gold futures GC=F, electricity APU000072610 monthly). Change of the unit's USD value over h calendar days. UP = unit revalues against USD (raises the debt value in USD: adverse for the CDP); DN = unit loses USD value (adverse for holders)")
    for h in (30, 60, 180):
        W = window_stats(dd, S2, h); L[h] = W
        print(f"\nh={h} days")
        print("| unit | sd (log) | p5 / p95 | worst UP (end date) | worst DN (end date) | P(up>5/10/20%) | P(dn<-5/-10/-20%) |"); print("|---|---|---|---|---|---|---|")
        for k, o in W.items():
            print(f"| {k} | {pc(o['sd'])} | {pc(o['p5'])} / {pc(o['p95'])} | {pc(o['up_max'])} ({o['up_date']}) | {pc(o['dn_min'])} ({o['dn_date']}) | {100*o['p_up5']:.1f} / {100*o['p_up10']:.1f} / {100*o['p_up20']:.1f}% | {100*o['p_dn5']:.1f} / {100*o['p_dn10']:.1f} / {100*o['p_dn20']:.1f}% |")
    J["long"] = {str(k): v for k, v in L.items()}
    print("\n## H5. Named episodes: change of the unit's USD value between the dates (long-history series)")
    print("| episode | CNY | EUR | basket(USD,EUR,CNY) | RUB | basket(USD,CNY,RUB) eq | basket 50/30/20 | gold |"); print("|---|---|---|---|---|---|---|---|")
    ep = {}
    for nm, a0, a1 in EPIS:
        i0, i1 = dd.index(dt.date.fromisoformat(a0)), dd.index(dt.date.fromisoformat(a1))
        c = S2["CNY"][i1] / S2["CNY"][i0] - 1; e = S2["EUR"][i1] / S2["EUR"][i0] - 1; g = S2["gold"][i1] / S2["gold"][i0] - 1; bk = (1 + (1 + e) + (1 + c)) / 3 - 1
        rr = S2["RUB"][i1] / S2["RUB"][i0] - 1; b3 = (2 + c + rr) / 3 - 1 + 0; b3 = (1 + (1 + c) + (1 + rr)) / 3 - 1; b5 = .5 + .3 * (1 + c) + .2 * (1 + rr) - 1
        ep[nm] = dict(CNY=c, EUR=e, basket=bk, RUB=rr, b3=b3, b532=b5, gold=g); print(f"| {nm} | {pc(c)} | {pc(e)} | {pc(bk)} | {pc(rr)} | {pc(b3)} | {pc(b5)} | {pc(g)} |")
    J["episodes"] = ep
    cn = fred(f"{D}/DEXCHUS.csv", "DEXCHUS"); ks = sorted(cn); gaps = [(ks[i + 1] - ks[i]).days for i in range(len(ks) - 1) if ks[i] >= dt.date(2020, 1, 1)]
    print(f"\n## H6. Publication facts (data): FRED DEXCHUS last observation {ks[-1]} (fetched 2026-11-11); gap between observations since 2020: median {int(np.median(gaps))} d, max {max(gaps)} d; Yahoo spot 2026-11-11: onshore CNY=X 6.6591, offshore CNH=X 6.6688 (offshore weaker by {100*(6.6688/6.6591-1):.2f}%, one observation; no keyless CNH history was obtainable: Yahoo returns a single point, stooq needs JavaScript).")
    json.dump(J, open(os.path.join(HERE, "units_hist.json"), "w"), indent=1)
