"""Why: build one daily CSV (UTC) from raw fetches: KAS/USD, hashrate, tx count, active-address proxy, energy (monthly, ffilled).
Read-only on raw/. Stdlib only."""
import json, csv, glob, datetime as dt, os
R=os.path.join(os.path.dirname(__file__),'..','raw'); O=os.path.join(os.path.dirname(__file__),'..')
def day(ts): return dt.datetime.fromtimestamp(ts,dt.timezone.utc).date()
price={}
for row in json.load(open(R+'/gate_KAS_early.json')):   # [t,vol,close,high,low,open,...]
    price[day(int(row[0]))]=float(row[2])
for row in json.load(open(R+'/kucoin_KAS_daily_scratch.json'))['data']:  # [t,open,close,high,low,..]
    price[day(int(row[0]))]=float(row[2])                  # kucoin overrides gate on overlap
hr={}
for r in json.load(open(R+'/hh_1d.json')):
    hr[day(r['timestamp']//1000)]=r['hashrate_kh']*1e3/1e15    # kH/s -> PH/s
tx={};ad={}
for f in sorted(glob.glob(R+'/tx_*.json')):
    for r in json.load(open(f)):
        d=day(r['timestamp']//1000); tx[d]=tx.get(d,0)+r['regular']
for f in sorted(glob.glob(R+'/ad_*.json')):
    for r in json.load(open(f)):
        d=day(r['timestamp']//1000); ad[d]=ad.get(d,0)+r['count']   # sum of hourly unique counts (overcounts multi-hour actives)
def fred(id):
    out={}
    for line in open(R+f'/fred_{id}.csv').read().split('\n')[1:]:
        if not line.strip(): continue
        a,b=line.split(',')
        if b not in ('','.'): out[dt.date.fromisoformat(a)]=float(b)
    return out
en=fred('PNRGINDEXM'); el=fred('APU000072610'); brent=fred('DCOILBRENTEU')
days=sorted(price); d0,d1=days[0],days[-1]
rows=[];last={}
d=d0
def mon(m,d): return m.get(d.replace(day=1))
while d<=d1:
    rows.append(dict(date=d,kas=price.get(d),hashrate_PHs=hr.get(d),tx_regular=tx.get(d),active_addr_hoursum=ad.get(d),
      energy_idx=mon(en,d),elec_usd_kwh=mon(el,d),brent=brent.get(d)))
    d+=dt.timedelta(1)
# forward fill gaps (price missing days, brent weekends)
for k in ['kas','hashrate_PHs','tx_regular','active_addr_hoursum','brent']:
    p=None
    for r in rows:
        if r[k] is None: r[k]=p
        else: p=r[k]
w=csv.DictWriter(open(O+'/daily.csv','w'),fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(len(rows),rows[0],rows[-1])
miss={k:sum(1 for r in rows if r[k] is None) for k in rows[0]}
print(miss)
