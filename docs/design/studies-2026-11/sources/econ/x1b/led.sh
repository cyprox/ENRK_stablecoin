python3 - <<'PY'
import json
for l in open('/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/x1b/ledger.jsonl'):
    j=json.loads(l); print(j['label'],j['submit'],'api',j.get('api_mass'),'s',j.get('confirm_s'),'|',j['local_mass'],'|',j['msg'][:200] if j['submit']!='SUBMITTED' else j['txid'][:12])
PY
