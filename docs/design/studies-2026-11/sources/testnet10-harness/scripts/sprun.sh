#!/bin/bash
# usage: sprun.sh "<vids>" TAG [FEE] : liquidate
S=/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad
H=$S/econ/t4/surplus
export VIDS=$1 FEE=${3:-3000000}
$S/tn10/sp.sh sp_liquidate | tee $H/last_build.txt | grep -v "^SPK"
grep -q "STORAGE_MASS" $H/last_build.txt || { echo BUILD_FAILED_SEE; exit 1; }
ON_OK="cp $H/ledger_next.json $H/ledger.json" $S/tn10/t4sub.sh t4_sp_liq.json $2 | tee -a $S/econ/t4/log/sp_results.txt
