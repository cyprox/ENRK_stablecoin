#!/bin/bash
# Sensitivity on headline cells (s=30, r in {0,3,5}, all D x S): impact {0.04,0.08,0.16} x capacity {0.025,0.05,0.10} (0.08/0.05 = base, already in grid_main)
cd "$(dirname "$0")"
for imp in 0.04 0.08 0.16; do for cap in 0.025 0.05 0.10; do
  python3 -B run_grid.py --out sens_${imp}_${cap}.pkl --paths 500 --rs 0,3,5 --ss 30 --kw "{\"impact_coefficient\":$imp,\"daily_liquidation_capacity\":$cap}"
done; done
