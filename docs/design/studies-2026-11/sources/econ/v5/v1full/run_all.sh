#!/bin/sh
# ECON-V1 full reproduction (3 processes at a time, ~3 h on a loaded machine). Run check_v1.py first (~70 s, must print "check_v1: OK").
cd "$(dirname "$0")"
python3 -B check_v1.py > check_v1_output.txt 2>&1
for e in E6 E1 E2 E4 E5 E7; do python3 -B run_v1.py --exp $e --out $e.pkl --paths 500 --procs 3 >> runall.log 2>&1; done
python3 -B run_v1.py --exp E3 --out E3.pkl --paths 300 --procs 3 >> runall.log 2>&1
python3 -B analyze_v1.py > tables_v1.txt
echo done >> runall.log
