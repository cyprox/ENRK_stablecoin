#!/bin/bash
# Why: sample recent per-tx fees on Kaspa (public GET/POST-search read-only) to compare with the code's fee baseline.
cd "$(dirname "$0")/../raw"
cur=$(curl -s -m 30 https://api.kaspa.org/info/virtual-chain-blue-score | python3 -c "import json,sys;print(json.load(sys.stdin)['blueScore'])")
for i in $(seq 1 40); do
  bs=$((cur-2000-i*37))
  curl -s -m 30 "https://api.kaspa.org/blocks-from-bluescore?blueScore=$bs&includeTransactions=true" -o "feeblk_$i.json"
  sleep 0.3
done
