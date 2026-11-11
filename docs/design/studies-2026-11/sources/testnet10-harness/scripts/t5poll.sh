#!/bin/bash
# poll REST for all ids in t5_ids.txt until accepted; print per-tx accepted time & accepting daa
S=/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad
for i in $(seq 1 60); do
  N=0; for t in $(cat $S/tn10/t5_ids.txt); do
    curl -s "https://api-tn10.kaspa.org/transactions/$t?inputs=false&outputs=false" | python3 -c "
import json,sys
try:
 d=json.load(sys.stdin);print('$t',d.get('is_accepted'),d.get('block_time'),d.get('accepting_block_blue_score'),d.get('accepting_block_time'),d.get('mass'))
except Exception as e: print('$t','ERR')" ; done > $S/tn10/t5_poll.txt
  grep -c " True " $S/tn10/t5_poll.txt | grep -q "^$(wc -l < $S/tn10/t5_ids.txt | tr -d ' ')$" && break; sleep 3
done
cat $S/tn10/t5_poll.txt
