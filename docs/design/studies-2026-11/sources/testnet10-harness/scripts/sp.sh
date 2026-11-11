#!/bin/bash
# usage: sp.sh <test>
S=/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad
rm -f $S/tn10/t4_sp_*.json $S/econ/t4/surplus/ledger_next.json
$S/tn10/t4run.sh t4_surplus $1
