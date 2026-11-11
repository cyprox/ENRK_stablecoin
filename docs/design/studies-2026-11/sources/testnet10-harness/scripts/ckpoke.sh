#!/bin/bash
# usage: ckpoke.sh ENTRY LOCK SEQ [submit]   ; uses econ/t4/ck_state.txt (txid ms daa raw); CVID fixed
S=/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad
read CT MS DAA RAW < $S/econ/t4/ck_state.txt
export ENTRY=$1 LOCK=$2 SEQ=$3 CV_ID=$(cat $S/econ/t4/ck_cid.txt) CV_TXID=$CT CV_INDEX=0 STATE_MS=$MS STATE_DAA=$DAA STATE_RAW=$RAW FUND_FILE=$S/tn10/t4_fund.txt FEE=${FEE:-500000}
rm -f $S/tn10/t4_ck_poke.json
[ -n "${PATCH:-}" ] && export PATCH_SEQ_MAX=1
$S/tn10/t4run.sh t4_clock ck_poke
