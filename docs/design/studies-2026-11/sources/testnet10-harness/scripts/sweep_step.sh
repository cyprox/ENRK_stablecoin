#!/bin/bash
# usage: sweep_step.sh M POPIN POPOUT FUND_TXID FUND_INDEX FUND_AMOUNT  -> sweep M round-1 UTXOs (1->2 each), submit
S=/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad
M=$1; cd $S/w/argent; export CARGO_TARGET_DIR=$S/target
FEE=$((100*(6000+2600*M)))
OUT=$(TN10_DIR=$S/tn10 COSPEND_DIR=$S/w/fixed_a2 ORACLE_ID=99a7e5f02e38cba7ea318a0ea632ff4705f36edc048a41e03537ed6d1cc6e68e MINV=${MINV:-2000000000} POP=$2 OUT_POP=$3 M=$M FEE=$FEE FUND_TXID=$4 FUND_INDEX=$5 FUND_AMOUNT=$6 cargo test --offline --test tn10_pop sweep_batch -- --nocapture 2>&1 | grep "TXID\|BUILD_FAILED\|^error\|panicked" | cut -c1-500)
echo "$OUT"; echo "$OUT" | grep -q "^TXID" || exit 1
for try in 1 2 3; do R=$(cd $S/rpc && CARGO_TARGET_DIR=$S/target_rpc cargo run -q --bin submit -- $S/tn10/tx_sweep.json 2>&1 | grep "SUBMITTED\|REJECTED" | cut -c1-500); [ -n "$R" ] && break; sleep 3; done; echo "${R:-NO_RESPONSE}" 
cat $S/tn10/fund.txt
