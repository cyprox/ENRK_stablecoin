#!/bin/bash
# Headline cells (HEAD pairs, r in {0,3}, s=30): impact {0.04,0.08,0.16} x capacity {0.025,0.05,0.10}
cd "$(dirname "$0")"
for imp in 0.04 0.08 0.16; do for cap in 0.025 0.05 0.10; do
  python3 -B run_t1.py --out t1_sens_${imp}_${cap}.pkl --paths 500 --rs 0,3 --ss 30 --pairs head --kw "{\"impact_coefficient\":$imp,\"daily_liquidation_capacity\":$cap}"
done; done
