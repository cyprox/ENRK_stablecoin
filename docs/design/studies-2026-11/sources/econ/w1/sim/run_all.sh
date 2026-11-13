#!/bin/sh
# ECON-W1 reproduction. cwd = this directory. <=3 processes. ~20 min per experiment at 500 paths.
python3 -B check_v1.py > check_v1_output.txt 2>&1
python3 -B check_w1.py > check_w1_output.txt 2>&1
python3 -B w1_run.py --exp WB --out WB.pkl --paths 500 --procs 3 > run_WB.log 2>&1
python3 -B w1_run.py --exp WC --out WC.pkl --paths 500 --procs 3 > run_WC.log 2>&1
echo done > run_done.txt
