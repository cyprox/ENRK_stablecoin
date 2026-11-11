#!/bin/bash
# usage: t4run.sh <test-file> <test-name>   (env passes through)
S=/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad
cd $S/w/argent; export CARGO_TARGET_DIR=$S/target TN10_DIR=$S/tn10 T4SRC=$S/econ/t4
cargo test --offline --test $1 $2 -- --nocapture --exact 2>&1 | grep -v "^running\|^test \|^$\|Finished\|Running\|Compiling\|warning" | cut -c1-900
