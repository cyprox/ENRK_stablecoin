# Aggregates coinbase extra-data pool tags over a sample of recent Kaspa mainnet blocks (api.kaspa.org). Prints family shares only; no addresses stored.
import json,urllib.request,collections,re
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'research'}),timeout=60))
cur=get('https://api.kaspa.org/info/blockdag')['virtualParentHashes'][-1]
fam=collections.Counter(); n=0; seen=set()
def family(t):
    t=t.lower()
    for k in ['humpool','viabtc','f2pool','kaspa-pool','wpool','antpool','binance','kryptex','2miners','woolypooly','acc-pool','herominers','lolminer','bitmain','poolin','okx','foundry','nanopool','sparkpool','kas.fyi','zpool','mmpos','sunpool']:
        if k in t: return k
    return 'other:'+t[:14].split('/')[1] if t.count('/')>1 else 'other/untagged'
for page in range(150):
    try: r=get(f'https://api.kaspa.org/blocks?lowHash={cur}&includeBlocks=true&includeTransactions=true')
    except Exception as e: print('stop',e); break
    bl=r.get('blocks',[])
    if not bl: break
    for b in bl:
        hh=b['verboseData']['hash']
        if hh in seen: continue
        seen.add(hh); n+=1
        p=bytes.fromhex(b['transactions'][0]['payload'])
        sl=p[18]; extra=p[19+sl:]
        fam[family(re.sub(rb'[^\x20-\x7e]',b'',extra).decode())]+=1
    cur=bl[-1]['verboseData']['hash']
    if n>40000: break
print('blocks sampled',n)
cum=0
for t,c in fam.most_common(15):
    cum+=c; print(f'{t:25s}{c:7d} {100*c/n:5.1f}%  cum {100*cum/n:5.1f}%')
