"""Why: ECON-W1 U3b: official CBR USD/RUB vs a market quote (Yahoo RUB=X, unofficial) around the 2014-12 and 2022-03 episodes; also gaps in the official series. python3 -I -B rub_divergence.py"""
import csv, json, datetime as dt, numpy as np
cbr = {dt.date.fromisoformat(r["observation_date"]): float(r["USDRUB_CBR"]) for r in csv.DictReader(open("data/cbr_usdrub.csv"))}
j = json.load(open("data/y_RUB.json"))["chart"]["result"][0]
yh = {dt.date.fromtimestamp(t): v for t, v in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if v}
def rep(a, b, name):
    ds = [d for d in sorted(cbr) if dt.date.fromisoformat(a) <= d <= dt.date.fromisoformat(b) and d in yh]
    x = np.array([cbr[d] / yh[d] - 1 for d in ds]); i = int(np.abs(x).argmax())
    print(f"{name}: {len(ds)} common days; official/market-1 median {100*np.median(x):+.2f}%, p95 |dev| {100*np.percentile(np.abs(x),95):.2f}%, max |dev| {100*abs(x[i]):.1f}% on {ds[i]} (CBR {cbr[ds[i]]:.1f} vs market {yh[ds[i]]:.1f})")
rep("2014-12-10", "2014-12-24", "Dec 2014"); rep("2022-02-22", "2022-04-15", "2022-02-22..04-15"); rep("2023-01-01", "2026-11-10", "2023-2026 (calm)")
ds = sorted(cbr); g = [(ds[i + 1] - ds[i]).days for i in range(len(ds) - 1)]
print("official series: first", ds[0], "last", ds[-1], "obs", len(ds), "max gap days", max(g), "(weekend/holiday set rates are in the file: CBR publishes an official rate for the next day, incl. non-trading days)")
big = [(ds[i + 1], cbr[ds[i + 1]] / cbr[ds[i]] - 1) for i in range(len(ds) - 1)]
print("largest 1-obs moves of the official rate:", [(str(d), f"{100*v:+.1f}%") for d, v in sorted(big, key=lambda t: -abs(t[1]))[:5]])
