#!/bin/sh
# ECON-W2 Monte Carlo steps (after the three checks). cwd = this directory; one pool of 3 processes at a time.
python3 -I -B w2_run.py --exp HL   --out HL.pkl   --paths 500 --procs 3 > run_HL.log 2>&1
python3 -I -B w2_run.py --exp OAT  --out OAT.pkl  --paths 300 --procs 3 > run_OAT.log 2>&1
python3 -I -B w2_run.py --exp SENS --out SENS.pkl --paths 300 --procs 3 > run_SENS.log 2>&1
python3 -I -B w2_run.py --exp SIZE --out SIZE.pkl --paths 300 --procs 3 > run_SIZE.log 2>&1
echo done > run_done.txt
