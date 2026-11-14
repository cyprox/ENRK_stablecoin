#!/bin/sh
# ECON-W2 reproduction. cwd = this directory. Each step uses a pool of 3 processes, steps run one after the other (never more than 3 processes at once).
python3 -I -B check_v1.py > check_v1_output.txt 2>&1
python3 -I -B check_w1.py > check_w1_output.txt 2>&1
python3 -I -B check_w2.py > check_w2_output.txt 2>&1
python3 -I -B w2_run.py --exp HL   --out HL.pkl   --paths 500 --procs 3 > run_HL.log 2>&1
python3 -I -B w2_run.py --exp OAT  --out OAT.pkl  --paths 300 --procs 3 > run_OAT.log 2>&1
python3 -I -B w2_run.py --exp SENS --out SENS.pkl --paths 300 --procs 3 > run_SENS.log 2>&1
python3 -I -B w2_run.py --exp SIZE --out SIZE.pkl --paths 300 --procs 3 > run_SIZE.log 2>&1
echo done > run_done.txt
