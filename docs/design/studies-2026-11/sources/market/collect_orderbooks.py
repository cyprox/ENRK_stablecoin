#!/usr/bin/env python3
"""Why: record KAS spot order-book depth snapshots to calibrate the market-impact coefficient and the
liquidator capacity of the ENRK stress model (decision: owner approval 2026-11-11, step 0 of the plan).

One-shot manual run; no scheduler. Public GET requests only (curl). Standard library only.
Usage:  python3 -I collect_orderbooks.py [--note "text"]
Output: <data>/YYYY-MM-DD/<venue>_<UTCstamp>.json (raw, read-only after write) and <data>/index.csv (one row per venue
and snapshot, plus one 'merged' row). Depth is DISPLAYED liquidity; a calm snapshot does not measure stressed depth.
"""
import csv, json, math, os, subprocess, sys, time
from datetime import datetime, timezone

DATA = os.path.expanduser("~/ENRK_market_data")
UA = ["-sS", "-m", "20", "-A", "enrk-research-collector/1.0"]
VENUES = {
    "kraken": ("https://api.kraken.com/0/public/Depth?pair=KASUSD&count=500", "https://api.kraken.com/0/public/Ticker?pair=KASUSD"),
    "kucoin": ("https://api.kucoin.com/api/v1/market/orderbook/level2_100?symbol=KAS-USDT", "https://api.kucoin.com/api/v1/market/stats?symbol=KAS-USDT"),
    "bybit": ("https://api.bybit.com/v5/market/orderbook?category=spot&symbol=KASUSDT&limit=200", "https://api.bybit.com/v5/market/tickers?category=spot&symbol=KASUSDT"),
    "gate": ("https://api.gateio.ws/api/v4/spot/order_book?currency_pair=KAS_USDT&limit=100", "https://api.gateio.ws/api/v4/spot/tickers?currency_pair=KAS_USDT"),
    "mexc": ("https://api.mexc.com/api/v3/depth?symbol=KASUSDT&limit=500", "https://api.mexc.com/api/v3/ticker/24hr?symbol=KASUSDT"),
    "bitget": ("https://api.bitget.com/api/v2/spot/market/orderbook?symbol=KASUSDT&type=step0&limit=150", "https://api.bitget.com/api/v2/spot/market/tickers?symbol=KASUSDT"),
}

def get(url):
    r = subprocess.run(["curl"] + UA + [url], capture_output=True, text=True)
    return json.loads(r.stdout)

def levels(venue, d):
    if venue == "kraken": b, a = d["result"]["KASUSD"]["bids"], d["result"]["KASUSD"]["asks"]
    elif venue == "kucoin": b, a = d["data"]["bids"], d["data"]["asks"]
    elif venue == "bybit": b, a = d["result"]["b"], d["result"]["a"]
    elif venue == "bitget": b, a = d["data"]["bids"], d["data"]["asks"]
    else: b, a = d["bids"], d["asks"]
    f = lambda xs: [(float(x[0]), float(x[1])) for x in xs if float(x[0]) > 1e-4]  # drop stub orders
    return sorted(f(b), reverse=True), sorted(f(a))

def volume_kas(venue, t):
    try:
        if venue == "kraken": return float(t["result"]["KASUSD"]["v"][1])
        if venue == "kucoin": return float(t["data"]["volValue"]) / float(t["data"]["last"])
        if venue == "mexc": return float(t["volume"])
        if venue == "gate": return float(t[0]["base_volume"])
        if venue == "bybit": return float(t["result"]["list"][0]["volume24h"])
        if venue == "bitget": return float(t["data"][0]["baseVolume"])
    except Exception: return None

def depth(side, mid, pct, sign):
    lim = mid * (1 + sign * pct / 100)
    ok = [(p, q) for p, q in side if (p >= lim if sign < 0 else p <= lim)]
    return sum(q for p, q in ok), sum(p * q for p, q in ok)

def impact(bids, mid, qty):
    rem, got = qty, 0.0
    for p, q in bids:
        t = min(rem, q); got += t * p; rem -= t
        if rem <= 0: break
    return None if rem > 0 else 1 - (got / qty) / mid

def main():
    note = sys.argv[sys.argv.index("--note") + 1] if "--note" in sys.argv else ""
    now = datetime.now(timezone.utc); stamp = now.strftime("%Y%m%dT%H%M%SZ"); day = now.strftime("%Y-%m-%d")
    os.makedirs(os.path.join(DATA, day), exist_ok=True)
    try: hr = get("https://api.kaspa.org/info/hashrate")["hashrate"]
    except Exception: hr = ""
    rows, merged_bids, adv_total = [], [], 0.0
    for v, (ob_url, tk_url) in VENUES.items():
        try:
            ob, tk = get(ob_url), get(tk_url)
            path = os.path.join(DATA, day, f"{v}_{stamp}.json")
            with open(path, "w") as f: json.dump({"orderbook": ob, "ticker": tk, "utc": stamp, "note": note}, f)
            os.chmod(path, 0o444)
            b, a = levels(v, ob); mid = b[0][0]; adv = volume_kas(v, tk)
            r = {"utc": stamp, "venue": v, "best_bid": b[0][0], "best_ask": a[0][0], "adv_kas_24h": adv, "kaspa_hashrate": hr, "note": note}
            for pct in (1, 2, 5):
                k, u = depth(b, mid, pct, -1); r[f"bid_depth_{pct}pct_kas"] = round(k); r[f"bid_depth_{pct}pct_usd"] = round(u)
                k, u = depth(a, a[0][0], pct, +1); r[f"ask_depth_{pct}pct_kas"] = round(k)
            for frac in (0.001, 0.01, 0.05):
                s = impact(b, mid, frac * adv) if adv else None
                r[f"slip_{frac*100:g}pctADV"] = "" if s is None else round(s, 5)
                r[f"k_{frac*100:g}pctADV"] = "" if s is None else round(s / math.sqrt(frac), 4)
            rows.append(r); merged_bids += b
            if adv: adv_total += adv
        except Exception as e:
            rows.append({"utc": stamp, "venue": v, "note": f"ERROR {type(e).__name__}: {str(e)[:80]}"})
    if merged_bids and adv_total:
        mb = sorted(merged_bids, reverse=True); mid = mb[0][0]
        r = {"utc": stamp, "venue": "merged", "best_bid": mid, "adv_kas_24h": adv_total, "kaspa_hashrate": hr, "note": note}
        for pct in (1, 2, 5):
            k, u = depth(mb, mid, pct, -1); r[f"bid_depth_{pct}pct_kas"] = round(k); r[f"bid_depth_{pct}pct_usd"] = round(u)
        for frac in (0.001, 0.01, 0.05, 0.1):
            s = impact(mb, mid, frac * adv_total)
            r[f"slip_{frac*100:g}pctADV"] = "" if s is None else round(s, 5)
            r[f"k_{frac*100:g}pctADV"] = "" if s is None else round(s / math.sqrt(frac), 4)
        rows.append(r)
    cols = ["utc","venue","best_bid","best_ask","adv_kas_24h","kaspa_hashrate","bid_depth_1pct_kas","bid_depth_1pct_usd","bid_depth_2pct_kas","bid_depth_2pct_usd","bid_depth_5pct_kas","bid_depth_5pct_usd","ask_depth_1pct_kas","ask_depth_2pct_kas","ask_depth_5pct_kas","slip_0.1pctADV","k_0.1pctADV","slip_1pctADV","k_1pctADV","slip_5pctADV","k_5pctADV","slip_10pctADV","k_10pctADV","note"]
    idx = os.path.join(DATA, "index.csv"); new = not os.path.exists(idx)
    with open(idx, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); 
        if new: w.writeheader()
        for r in rows: w.writerow(r)
    for r in rows:
        print(r["venue"], "best_bid", r.get("best_bid"), "depth5%USD", r.get("bid_depth_5pct_usd"), "k1%", r.get("k_1pctADV"), r.get("note") if str(r.get("note","")).startswith("ERROR") else "")

if __name__ == "__main__":
    main()
