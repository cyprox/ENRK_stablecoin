#!/bin/bash
# usage: hv.sh <test> ; runs t4_harvest <test> with T4SRC env
S=/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad
rm -f $S/tn10/t4_hv_*.json $S/econ/t4/harvest/ledger_next.json
$S/tn10/t4run.sh t4_harvest $1
