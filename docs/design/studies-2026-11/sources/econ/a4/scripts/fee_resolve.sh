#!/bin/bash
# Why: resolve fees of the sampled non-coinbase txs (public POST /transactions/search is a read-only lookup). Run after sample_fees.sh.
cd "$(dirname "$0")/.."
python3 - <<'P'
import json,glob
ids=[]
for f in glob.glob('raw/feeblk_*.json'):
    try: d=json.load(open(f))
    except Exception: continue
    for b in d:
        for t in b['transactions'][1:]: ids.append(t['verboseData']['transactionId'])
json.dump({'transactionIds':sorted(set(ids))},open('raw/feeq.json','w'))
P
curl -s -m 60 -X POST -H 'content-type: application/json' -d @raw/feeq.json "https://api.kaspa.org/transactions/search?resolve_previous_outpoints=light" -o raw/feetx.json
python3 - <<'P'
import json
for t in json.load(open('raw/feetx.json')):
    i=sum(x.get('previous_outpoint_amount') or 0 for x in t['inputs']); o=sum(x['amount'] for x in t['outputs']); m=int(t['mass'])
    print('fee_sompi',i-o,'mass',m,'sompi_per_gram',(i-o)/m)
P
