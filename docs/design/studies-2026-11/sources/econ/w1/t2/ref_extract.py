"""Why: print the reference borrow rates used in the T2 report from the downloaded DeFiLlama files (no decision ref)."""
import json
P = json.load(open('web/pools.json'))['data']
L = {x['pool']: x for x in json.load(open('web/lendborrow.json'))}
for p in P:
    if p['project'] in ('sky-lending', 'liquity-v1', 'liquity-v2', 'crvusd', 'aave-v3', 'compound-v3', 'sparklend') and p['chain'] == 'Ethereum':
        l = L.get(p['pool'], {})
        if l.get('apyBaseBorrow') is not None and p['tvlUsd'] > 1e6:
            print(p['project'], p['symbol'], round(p['tvlUsd'] / 1e6, 1), 'borrowAPR%', l['apyBaseBorrow'], 'minted', l.get('mintedCoin'))
k = json.load(open('web/kaskad.json'))
print('Kaskad currentChainTvls', k['currentChainTvls'])
