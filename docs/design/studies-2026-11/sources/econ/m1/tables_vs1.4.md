## VOL x1.4

### T1 revenue split, % of avg debt/yr (churn 1, redemption 2%, ICR 250); columns mint|stab|liq|red|total
calm      r=0% | 2.00 | 0.00 | 3.02 | 0.03 | 5.05
calm      r=1% | 2.00 | 1.00 | 3.06 | 0.03 | 6.09
calm      r=2% | 2.00 | 2.00 | 3.09 | 0.03 | 7.12
calm      r=3% | 2.00 | 3.00 | 3.13 | 0.03 | 8.16
calm      r=5% | 2.00 | 5.01 | 3.20 | 0.03 | 10.23
bull      r=0% | 2.00 | 0.00 | 4.33 | 0.03 | 6.36
bull      r=1% | 2.00 | 1.00 | 4.35 | 0.03 | 7.38
bull      r=2% | 2.00 | 2.00 | 4.37 | 0.03 | 8.41
bull      r=3% | 2.00 | 3.01 | 4.39 | 0.03 | 9.43
bull      r=5% | 2.00 | 5.01 | 4.43 | 0.03 | 11.47
sideways  r=0% | 2.00 | 0.00 | 11.03 | 0.03 | 13.06
sideways  r=1% | 2.00 | 1.01 | 11.07 | 0.03 | 14.11
sideways  r=2% | 2.00 | 2.01 | 11.12 | 0.03 | 15.16
sideways  r=3% | 2.00 | 3.02 | 11.16 | 0.03 | 16.22
sideways  r=5% | 2.00 | 5.03 | 11.26 | 0.03 | 18.32
slowbear  r=0% | 2.00 | 0.00 | 17.34 | 0.04 | 19.38
slowbear  r=1% | 2.00 | 1.01 | 17.40 | 0.04 | 20.45
slowbear  r=2% | 2.00 | 2.02 | 17.47 | 0.04 | 21.52
slowbear  r=3% | 2.00 | 3.03 | 17.51 | 0.04 | 22.58
slowbear  r=5% | 2.00 | 5.04 | 17.63 | 0.04 | 24.71
mix       r=0% | 2.00 | 0.00 | 8.93 | 0.03 | 10.96
mix       r=1% | 2.00 | 1.00 | 8.97 | 0.03 | 12.01
mix       r=2% | 2.00 | 2.01 | 9.01 | 0.03 | 13.05
mix       r=3% | 2.00 | 3.01 | 9.05 | 0.03 | 14.09
mix       r=5% | 2.00 | 5.02 | 9.13 | 0.03 | 16.18

### T1b total fee % of debt by churn (mix of 4 regimes, q=2%, ICR 250)
r=0% c=0.5:9.96 c=1:10.96 c=2:12.96
r=1% c=0.5:11.01 c=1:12.01 c=2:14.01
r=2% c=0.5:12.05 c=1:13.05 c=2:15.05
r=3% c=0.5:13.09 c=1:14.09 c=2:16.09
r=5% c=0.5:15.18 c=1:16.18 c=2:18.18

### T1c total fee % by redemption rate (mix, c=1, ICR250)
r=0% q=0%:11.09 q=2%:10.96 q=10%:10.51
r=1% q=0%:12.13 q=2%:12.01 q=10%:11.54
r=2% q=0%:13.18 q=2%:13.05 q=10%:12.59
r=3% q=0%:14.22 q=2%:14.09 q=10%:13.63
r=5% q=0%:16.30 q=2%:16.18 q=10%:15.70

### T1d total fee % by opening ICR (mix, c=1, q=2%)
r=0% ICR200:21.82 ICR250:10.96 ICR300:7.01
r=1% ICR200:22.88 ICR250:12.01 ICR300:8.03
r=2% ICR200:23.98 ICR250:13.05 ICR300:9.05
r=3% ICR200:25.04 ICR250:14.09 ICR300:10.08
r=5% ICR200:27.20 ICR250:16.18 ICR300:12.13

### T2 USD revenue per year, M USD (mix, q=2%, ICR 250): D=1/5/20M, churn .5/1/2
r=0% c=0.5: 0.100/0.498/1.992 | c=1: 0.110/0.548/2.192 | c=2: 0.130/0.648/2.592
r=1% c=0.5: 0.110/0.550/2.201 | c=1: 0.120/0.600/2.401 | c=2: 0.140/0.700/2.801
r=2% c=0.5: 0.121/0.603/2.411 | c=1: 0.131/0.653/2.611 | c=2: 0.151/0.753/3.011
r=3% c=0.5: 0.131/0.655/2.619 | c=1: 0.141/0.705/2.819 | c=2: 0.161/0.805/3.219
r=5% c=0.5: 0.152/0.759/3.037 | c=1: 0.162/0.809/3.237 | c=2: 0.182/0.909/3.637

### T3 years to treasury cap ($300k = 2.5M units, FROZEN s6; 20% of all fees, mean revenue constant)
r=0% c=0.5: 15.1/3.0/0.8 | c=1: 13.7/2.7/0.7 | c=2: 11.6/2.3/0.6
r=1% c=0.5: 13.6/2.7/0.7 | c=1: 12.5/2.5/0.6 | c=2: 10.7/2.1/0.5
r=2% c=0.5: 12.4/2.5/0.6 | c=1: 11.5/2.3/0.6 | c=2: 10.0/2.0/0.5
r=3% c=0.5: 11.5/2.3/0.6 | c=1: 10.6/2.1/0.5 | c=2: 9.3/1.9/0.5
r=5% c=0.5: 9.9/2.0/0.5 | c=1: 9.3/1.9/0.5 | c=2: 8.2/1.6/0.4

### T3b years to cap, by regime (D=5M, c=1, q=2%, ICR250)
r=0% calm:5.9 bull:4.7 sideways:2.3 slowbear:1.5
r=1% calm:4.9 bull:4.1 sideways:2.1 slowbear:1.5
r=2% calm:4.2 bull:3.6 sideways:2.0 slowbear:1.4
r=3% calm:3.7 bull:3.2 sideways:1.9 slowbear:1.3
r=5% calm:2.9 bull:2.6 sideways:1.6 slowbear:1.2

### T4 borrower. y* = annual return the borrowed funds must earn to beat holding KAS (%/yr of debt), = -(delta0 - 2%*churn). fees-only cost = r+2%c+1%q
regime r  ICR | fees-only(c=1,q=2%) | y* c=1 q=2% | y* at r=0 | fee-attributable y*-y*0 | delta0 p10 (c=0 part)
calm      r=0% ICR200 | 2.02 | 16.04 | 16.04 | 0.00 | -67.74
calm      r=2% ICR200 | 4.02 | 18.06 | 16.04 | 2.02 | -69.85
calm      r=5% ICR200 | 7.02 | 20.85 | 16.04 | 4.81 | -69.91
calm      r=0% ICR250 | 2.02 | 8.82 | 8.82 | 0.00 | -28.47
calm      r=2% ICR250 | 4.02 | 10.90 | 8.82 | 2.07 | -29.83
calm      r=5% ICR250 | 7.02 | 13.96 | 8.82 | 5.13 | -33.17
calm      r=0% ICR300 | 2.02 | 4.34 | 4.34 | 0.00 | -7.91
calm      r=2% ICR300 | 4.02 | 6.48 | 4.34 | 2.14 | -10.60
calm      r=5% ICR300 | 7.02 | 9.89 | 4.34 | 5.55 | -13.79
bull      r=0% ICR200 | 2.02 | 116.66 | 116.66 | 0.00 | -341.80
bull      r=2% ICR200 | 4.02 | 120.83 | 116.66 | 4.17 | -357.01
bull      r=5% ICR200 | 7.02 | 125.34 | 116.66 | 8.68 | -358.07
bull      r=0% ICR250 | 2.02 | 60.37 | 60.37 | 0.00 | -148.06
bull      r=2% ICR250 | 4.02 | 64.37 | 60.37 | 4.00 | -156.72
bull      r=5% ICR250 | 7.02 | 70.27 | 60.37 | 9.90 | -166.15
bull      r=0% ICR300 | 2.02 | 23.85 | 23.85 | 0.00 | -56.94
bull      r=2% ICR300 | 4.02 | 27.76 | 23.85 | 3.92 | -63.35
bull      r=5% ICR300 | 7.02 | 33.55 | 23.85 | 9.71 | -71.78
sideways  r=0% ICR200 | 2.02 | 73.28 | 73.28 | 0.00 | -253.25
sideways  r=2% ICR200 | 4.02 | 75.00 | 73.28 | 1.72 | -253.96
sideways  r=5% ICR200 | 7.02 | 77.43 | 73.28 | 4.15 | -258.92
sideways  r=0% ICR250 | 2.02 | 52.42 | 52.42 | 0.00 | -167.16
sideways  r=2% ICR250 | 4.02 | 54.61 | 52.42 | 2.19 | -177.78
sideways  r=5% ICR250 | 7.02 | 58.34 | 52.42 | 5.93 | -178.73
sideways  r=0% ICR300 | 2.02 | 33.79 | 33.79 | 0.00 | -110.10
sideways  r=2% ICR300 | 4.02 | 36.44 | 33.79 | 2.65 | -112.65
sideways  r=5% ICR300 | 7.02 | 40.41 | 33.79 | 6.61 | -118.49
slowbear  r=0% ICR200 | 2.02 | -11.75 | -11.75 | 0.00 | -75.54
slowbear  r=2% ICR200 | 4.02 | -9.97 | -11.75 | 1.78 | -78.20
slowbear  r=5% ICR200 | 7.02 | -8.67 | -11.75 | 3.08 | -88.61
slowbear  r=0% ICR250 | 2.02 | -6.57 | -6.57 | 0.00 | -56.00
slowbear  r=2% ICR250 | 4.02 | -5.78 | -6.57 | 0.79 | -57.91
slowbear  r=5% ICR250 | 7.02 | -4.68 | -6.57 | 1.89 | -58.58
slowbear  r=0% ICR300 | 2.02 | -4.03 | -4.03 | 0.00 | -60.41
slowbear  r=2% ICR300 | 4.02 | -2.95 | -4.03 | 1.08 | -63.30
slowbear  r=5% ICR300 | 7.02 | -1.38 | -4.03 | 2.65 | -66.10
mix       r=0% ICR200 | 2.02 | 48.56 | 48.56 | 0.00 | -184.58
mix       r=2% ICR200 | 4.02 | 50.98 | 48.56 | 2.42 | -189.76
mix       r=5% ICR200 | 7.02 | 53.74 | 48.56 | 5.18 | -193.88
mix       r=0% ICR250 | 2.02 | 28.76 | 28.76 | 0.00 | -99.92
mix       r=2% ICR250 | 4.02 | 31.03 | 28.76 | 2.26 | -105.56
mix       r=5% ICR250 | 7.02 | 34.47 | 28.76 | 5.71 | -109.16
mix       r=0% ICR300 | 2.02 | 14.49 | 14.49 | 0.00 | -58.84
mix       r=2% ICR300 | 4.02 | 16.93 | 14.49 | 2.45 | -62.48
mix       r=5% ICR300 | 7.02 | 20.62 | 14.49 | 6.13 | -67.54

### T5 liquidations & fee effect on ICR (c-independent), q=2%: share of vaults liquidated in year | bad debt % of D0 | (end ICR omitted; analytic: the fee removes r/ICR0 of collateral per year)
calm      ICR200 r=0%: 45.66|0.00 ; r=2%: 46.26|0.00 ; r=5%: 47.19|0.00
calm      ICR250 r=0%: 27.59|0.00 ; r=2%: 28.14|0.00 ; r=5%: 28.90|0.00
calm      ICR300 r=0%: 13.16|0.00 ; r=2%: 13.43|0.00 ; r=5%: 14.12|0.00
bull      ICR200 r=0%: 42.43|0.00 ; r=2%: 42.76|0.00 ; r=5%: 42.94|0.00
bull      ICR250 r=0%: 26.66|0.00 ; r=2%: 26.89|0.00 ; r=5%: 27.24|0.00
bull      ICR300 r=0%: 15.80|0.00 ; r=2%: 15.94|0.00 ; r=5%: 16.15|0.00
sideways  ICR200 r=0%: 65.30|0.00 ; r=2%: 65.70|0.00 ; r=5%: 65.97|0.00
sideways  ICR250 r=0%: 50.04|0.00 ; r=2%: 50.37|0.00 ; r=5%: 50.98|0.00
sideways  ICR300 r=0%: 36.52|0.00 ; r=2%: 36.79|0.00 ; r=5%: 37.16|0.00
slowbear  ICR200 r=0%: 86.02|0.00 ; r=2%: 86.36|0.00 ; r=5%: 86.79|0.00
slowbear  ICR250 r=0%: 77.96|0.00 ; r=2%: 78.19|0.00 ; r=5%: 78.56|0.00
slowbear  ICR300 r=0%: 68.41|0.00 ; r=2%: 68.63|0.00 ; r=5%: 69.13|0.00

### T6 junior gross yield, % of junior notional per yr = F/s (mix of regimes; c=1,q=2%,ICR250). D1 = 100% fee to junior; D2 pre-cap = 80%; D2 post-cap = D1; D3 = 0. Net of bad debt absorbed.
r=0% s=15%: D1 73.08, D2pre 58.47 | s=30%: D1 36.54, D2pre 29.23 | s=50%: D1 21.92, D2pre 17.54
r=1% s=15%: D1 80.05, D2pre 64.04 | s=30%: D1 40.02, D2pre 32.02 | s=50%: D1 24.01, D2pre 19.21
r=2% s=15%: D1 87.02, D2pre 69.62 | s=30%: D1 43.51, D2pre 34.81 | s=50%: D1 26.11, D2pre 20.89
r=3% s=15%: D1 93.96, D2pre 75.17 | s=30%: D1 46.98, D2pre 37.58 | s=50%: D1 28.19, D2pre 22.55
r=5% s=15%: D1 107.89, D2pre 86.31 | s=30%: D1 53.94, D2pre 43.16 | s=50%: D1 32.37, D2pre 25.89

### T6b junior wrong-way: D1 yield s=30% by regime, receipt-value vs held-in-KAS marked at year end; p10 of fee (% of debt)
calm      r=0% | at receipt 16.82 | held in KAS 17.98 | corr(fee USD, KAS ret)=-0.42 | mtm p10 fee %debt 0.02
calm      r=2% | at receipt 23.74 | held in KAS 25.70 | corr(fee USD, KAS ret)=-0.42 | mtm p10 fee %debt 1.96
calm      r=5% | at receipt 34.12 | held in KAS 37.18 | corr(fee USD, KAS ret)=-0.42 | mtm p10 fee %debt 4.86
bull      r=0% | at receipt 21.21 | held in KAS 44.33 | corr(fee USD, KAS ret)=-0.18 | mtm p10 fee %debt 0.02
bull      r=2% | at receipt 28.02 | held in KAS 57.95 | corr(fee USD, KAS ret)=-0.18 | mtm p10 fee %debt 2.30
bull      r=5% | at receipt 38.24 | held in KAS 78.45 | corr(fee USD, KAS ret)=-0.18 | mtm p10 fee %debt 5.67
sideways  r=0% | at receipt 43.54 | held in KAS 67.85 | corr(fee USD, KAS ret)=-0.34 | mtm p10 fee %debt 0.02
sideways  r=2% | at receipt 50.55 | held in KAS 77.26 | corr(fee USD, KAS ret)=-0.34 | mtm p10 fee %debt 2.19
sideways  r=5% | at receipt 61.07 | held in KAS 91.73 | corr(fee USD, KAS ret)=-0.34 | mtm p10 fee %debt 5.34
slowbear  r=0% | at receipt 64.59 | held in KAS 49.25 | corr(fee USD, KAS ret)=-0.3 | mtm p10 fee %debt 0.04
slowbear  r=2% | at receipt 71.74 | held in KAS 54.62 | corr(fee USD, KAS ret)=-0.3 | mtm p10 fee %debt 3.06
slowbear  r=5% | at receipt 82.36 | held in KAS 62.39 | corr(fee USD, KAS ret)=-0.3 | mtm p10 fee %debt 4.84

### T7 s* = largest junior share s (1% grid) with net yield >= hurdle h; 100% = nobody needs to be compensated beyond; mix regimes; c=1,q=2%,ICR250. cols D1 | D2pre | D1-held-in-KAS | D3
mix h=5% r=0%: 100|100|100|0 ; r=1%: 100|100|100|0 ; r=2%: 100|100|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
mix h=10% r=0%: 100|87|100|0 ; r=1%: 100|96|100|0 ; r=2%: 100|100|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
mix h=20% r=0%: 54|43|67|0 ; r=1%: 60|48|74|0 ; r=2%: 65|52|80|0 ; r=3%: 70|56|87|0 ; r=5%: 80|64|100|0
calm h=5% r=0%: 100|80|100|0 ; r=1%: 100|97|100|0 ; r=2%: 100|100|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
calm h=10% r=0%: 50|40|53|0 ; r=1%: 60|48|65|0 ; r=2%: 71|56|77|0 ; r=3%: 81|65|88|0 ; r=5%: 100|81|100|0
calm h=20% r=0%: 25|20|26|0 ; r=1%: 30|24|32|0 ; r=2%: 35|28|38|0 ; r=3%: 40|32|44|0 ; r=5%: 51|40|55|0
bull h=5% r=0%: 100|100|100|0 ; r=1%: 100|100|100|0 ; r=2%: 100|100|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
bull h=10% r=0%: 63|50|100|0 ; r=1%: 73|59|100|0 ; r=2%: 84|67|100|0 ; r=3%: 94|75|100|0 ; r=5%: 100|91|100|0
bull h=20% r=0%: 31|25|66|0 ; r=1%: 36|29|76|0 ; r=2%: 42|33|86|0 ; r=3%: 47|37|97|0 ; r=5%: 57|45|100|0
sideways h=5% r=0%: 100|100|100|0 ; r=1%: 100|100|100|0 ; r=2%: 100|100|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
sideways h=10% r=0%: 100|100|100|0 ; r=1%: 100|100|100|0 ; r=2%: 100|100|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
sideways h=20% r=0%: 65|52|100|0 ; r=1%: 70|56|100|0 ; r=2%: 75|60|100|0 ; r=3%: 81|64|100|0 ; r=5%: 91|73|100|0
slowbear h=5% r=0%: 100|100|100|0 ; r=1%: 100|100|100|0 ; r=2%: 100|100|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
slowbear h=10% r=0%: 100|100|100|0 ; r=1%: 100|100|100|0 ; r=2%: 100|100|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
slowbear h=20% r=0%: 96|77|73|0 ; r=1%: 100|81|77|0 ; r=2%: 100|86|81|0 ; r=3%: 100|90|85|0 ; r=5%: 100|98|93|0

### T7b s* for mix, h=10%, by churn (D1)
c=0.5 r=0%: 99 ; r=1%: 100 ; r=2%: 100 ; r=3%: 100 ; r=5%: 100
c=1 r=0%: 100 ; r=1%: 100 ; r=2%: 100 ; r=3%: 100 ; r=5%: 100
c=2 r=0%: 100 ; r=1%: 100 ; r=2%: 100 ; r=3%: 100 ; r=5%: 100

### bad debt (all vaults) % of D0, max over 300 paths, by regime ICR200 r=0/5%
calm r=0%:mean 0.00 p90 0.00 max 0.00 r=5%:mean 0.00 p90 0.00 max 0.00
bull r=0%:mean 0.00 p90 0.00 max 0.00 r=5%:mean 0.00 p90 0.00 max 0.00
sideways r=0%:mean 0.00 p90 0.00 max 0.00 r=5%:mean 0.00 p90 0.00 max 0.00
slowbear r=0%:mean 0.00 p90 0.00 max 0.00 r=5%:mean 0.00 p90 0.00 max 0.00
