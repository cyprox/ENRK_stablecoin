#!/bin/bash
# usage: hvrun.sh "<vids>" TAG [FEE]
S=/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad
H=$S/econ/t4/harvest
eval $($S/tn10/pmt.sh)
export LOCK=$((PMT-5000)) VIDS=$1 FEE=${3:-25000000}
$S/tn10/hv.sh hv_harvest | tee $H/last_build.txt | grep -v "^VAULT\|SPK"
grep -q "STORAGE_MASS" $H/last_build.txt || { echo BUILD_FAILED_SEE; grep BUILD_FAILED $H/last_build.txt; exit 1; }
ON_OK="cp $H/ledger_next.json $H/ledger.json" $S/tn10/t4sub.sh t4_hv_harvest.json $2 | tee -a $S/econ/t4/log/hv_results.txt
