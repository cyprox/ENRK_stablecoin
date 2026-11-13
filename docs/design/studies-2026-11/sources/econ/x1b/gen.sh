#!/bin/bash
# usage: gen.sh <a|b|actl> <N>  -> econ/x1b/<v>/n<N>/{oracle.ag,vault.ag}
X=/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/x1b
V=$1; N=$2; D=$X/$V/n$N; mkdir -p $D
T=$X/${V:0:1}/oracle.tmpl; [ "$V" = actl ] && T=$X/a/oracle_ctl.tmpl
sed "s/@MAXF@/$((N-1))/;s/@MAXO@/$N/" $T > $D/oracle.ag
F=PriceRound; [ "${V:0:1}" = b ] && F=Follower
sed "s/OracleFeed::PriceRound/OracleFeed::$F/g" /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/w/fixed_b/vault.ag > $D/vault.ag
echo $D
