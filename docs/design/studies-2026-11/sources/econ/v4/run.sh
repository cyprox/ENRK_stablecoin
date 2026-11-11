#!/bin/zsh
# usage: run.sh <app.ag> <Actor> <fields> <cases> <out>
SP=/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad
cd $SP/w/argent && V4_APP=$1 V4_ACTOR=$2 V4_FIELDS=$3 V4_CASES=$4 V4_OUT=$5 CARGO_TARGET_DIR=$SP/target cargo test --offline --test v4_exec arith -- --nocapture 2>&1 | tail -8
