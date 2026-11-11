#!/bin/bash
# prints: daa pmt tip_ts wall_ms  (retries DNS)
S=/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad
for i in 1 2 3 4 5 6; do
 R=$(cd $S/rpc && CARGO_TARGET_DIR=$S/target_rpc cargo run -q --offline --bin clockinfo 2>&1 | grep "^daa")
 [ -n "$R" ] && { echo "$R" | awk '{print "DAA="$2" PMT="$4" TIP="$6" WALL="$10}'; exit 0; }; sleep 2
done; exit 1
