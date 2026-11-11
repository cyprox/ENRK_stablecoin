#!/bin/bash
# usage: run_round.sh N FUND_TXID FUND_INDEX FUND_AMOUNT  -> genesis N price UTXOs, then spend them all in one round
set -u
S=/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad
N=$1; FT=$2; FI=$3; FA=$4; PRICE=${PRICE:-1000000000}
cd $S/w/argent; export CARGO_TARGET_DIR=$S/target; FEE=$((100*(4000+800*N)))
G=$(TN10_DIR=$S/tn10 COSPEND_DIR=$S/w/${VDIR:-fixed_a2} STEP=oracle N=$N PRICE=$PRICE IN_TXID=$FT IN_INDEX=$FI IN_AMOUNT=$FA IN_DAA=0 FEE=$FEE cargo test --offline --test tn10_launch -- --nocapture 2>&1)
GT=$(echo "$G" | sed -n 's/^TXID //p'); CID=$(echo "$G" | sed -n 's/^COVENANT_ID //p'); CH=$((FA-N*PRICE-FEE))
[ -z "$GT" ] && { echo "GENESIS_BUILD_FAILED"; echo "$G" | grep -i "panicked\|error" | head -3; exit 1; }
(cd $S/rpc && CARGO_TARGET_DIR=$S/target_rpc cargo run -q --bin submit -- $S/tn10/tx_oracle.json 2>&1 | grep "SUBMITTED\|REJECTED" | cut -c1-400) | sed 's/^/genesis: /'
sleep 6
FEE2=$((100*(4000+1000*N)))
R=$(TN10_DIR=$S/tn10 COSPEND_DIR=$S/w/${VDIR:-fixed_a2} ORACLE_ID=$CID N=$N PRICE=$PRICE ORACLE_TXID=$GT FUND_TXID=$GT FUND_INDEX=$N FUND_AMOUNT=$CH FEE=$FEE2 cargo test --offline --test tn10_round -- --nocapture 2>&1)
echo "$R" | grep "BUILD_FAILED" | cut -c1-400
RT=$(echo "$R" | sed -n 's/^TXID //p')
[ -z "$RT" ] && { echo "ROUND_BUILD_FAILED"; exit 1; }
(cd $S/rpc && CARGO_TARGET_DIR=$S/target_rpc cargo run -q --bin submit -- $S/tn10/tx_round.json 2>&1 | grep "SUBMITTED\|REJECTED" | cut -c1-500) | sed 's/^/round: /'
echo "N=$N genesis=$GT round=$RT next_fund=$RT:$N amount=$((CH-FEE2))"
