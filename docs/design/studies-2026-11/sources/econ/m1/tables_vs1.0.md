## VOL x1.0

### T1 revenue split, % of avg debt/yr (churn 1, redemption 2%, ICR 250); columns mint|stab|liq|red|total
calm      r=0% | 2.00 | 0.00 | 1.00 | 0.02 | 3.02
calm      r=1% | 2.00 | 1.00 | 1.03 | 0.02 | 4.05
calm      r=2% | 2.00 | 2.00 | 1.05 | 0.02 | 5.07
calm      r=3% | 2.00 | 3.00 | 1.07 | 0.02 | 6.10
calm      r=5% | 2.00 | 5.00 | 1.12 | 0.02 | 8.14
bull      r=0% | 2.00 | 0.00 | 1.24 | 0.02 | 3.26
bull      r=1% | 2.00 | 1.00 | 1.25 | 0.02 | 4.27
bull      r=2% | 2.00 | 2.00 | 1.27 | 0.02 | 5.29
bull      r=3% | 2.00 | 3.00 | 1.28 | 0.02 | 6.31
bull      r=5% | 2.00 | 5.00 | 1.31 | 0.02 | 8.33
sideways  r=0% | 2.00 | 0.00 | 5.41 | 0.03 | 7.44
sideways  r=1% | 2.00 | 1.00 | 5.45 | 0.03 | 8.48
sideways  r=2% | 2.00 | 2.01 | 5.47 | 0.03 | 9.51
sideways  r=3% | 2.00 | 3.01 | 5.51 | 0.03 | 10.55
sideways  r=5% | 2.00 | 5.01 | 5.58 | 0.03 | 12.63
slowbear  r=0% | 2.00 | 0.00 | 12.08 | 0.03 | 14.11
slowbear  r=1% | 2.00 | 1.01 | 12.13 | 0.03 | 15.17
slowbear  r=2% | 2.00 | 2.01 | 12.20 | 0.03 | 16.24
slowbear  r=3% | 2.00 | 3.02 | 12.26 | 0.03 | 17.31
slowbear  r=5% | 2.00 | 5.03 | 12.37 | 0.03 | 19.44
mix       r=0% | 2.00 | 0.00 | 4.93 | 0.03 | 6.96
mix       r=1% | 2.00 | 1.00 | 4.96 | 0.03 | 7.99
mix       r=2% | 2.00 | 2.00 | 5.00 | 0.03 | 9.03
mix       r=3% | 2.00 | 3.01 | 5.03 | 0.03 | 10.07
mix       r=5% | 2.00 | 5.01 | 5.09 | 0.03 | 12.13

### T1b total fee % of debt by churn (mix of 4 regimes, q=2%, ICR 250)
r=0% c=0.5:5.96 c=1:6.96 c=2:8.96
r=1% c=0.5:6.99 c=1:7.99 c=2:9.99
r=2% c=0.5:8.03 c=1:9.03 c=2:11.03
r=3% c=0.5:9.07 c=1:10.07 c=2:12.07
r=5% c=0.5:11.13 c=1:12.13 c=2:14.13

### T1c total fee % by redemption rate (mix, c=1, ICR250)
r=0% q=0%:7.08 q=2%:6.96 q=10%:6.58
r=1% q=0%:8.12 q=2%:7.99 q=10%:7.61
r=2% q=0%:9.15 q=2%:9.03 q=10%:8.64
r=3% q=0%:10.19 q=2%:10.07 q=10%:9.67
r=5% q=0%:12.25 q=2%:12.13 q=10%:11.74

### T1d total fee % by opening ICR (mix, c=1, q=2%)
r=0% ICR200:12.70 ICR250:6.96 ICR300:4.79
r=1% ICR200:13.78 ICR250:7.99 ICR300:5.81
r=2% ICR200:14.84 ICR250:9.03 ICR300:6.82
r=3% ICR200:15.92 ICR250:10.07 ICR300:7.84
r=5% ICR200:18.06 ICR250:12.13 ICR300:9.88

### T2 USD revenue per year, M USD (mix, q=2%, ICR 250): D=1/5/20M, churn .5/1/2
r=0% c=0.5: 0.060/0.298/1.192 | c=1: 0.070/0.348/1.392 | c=2: 0.090/0.448/1.792
r=1% c=0.5: 0.070/0.350/1.399 | c=1: 0.080/0.400/1.599 | c=2: 0.100/0.500/1.999
r=2% c=0.5: 0.080/0.401/1.606 | c=1: 0.090/0.451/1.806 | c=2: 0.110/0.551/2.206
r=3% c=0.5: 0.091/0.453/1.813 | c=1: 0.101/0.503/2.013 | c=2: 0.121/0.603/2.413
r=5% c=0.5: 0.111/0.557/2.227 | c=1: 0.121/0.607/2.427 | c=2: 0.141/0.707/2.827

### T3 years to treasury cap ($300k = 2.5M units, FROZEN s6; 20% of all fees, mean revenue constant)
r=0% c=0.5: 25.2/5.0/1.3 | c=1: 21.6/4.3/1.1 | c=2: 16.7/3.3/0.8
r=1% c=0.5: 21.4/4.3/1.1 | c=1: 18.8/3.8/0.9 | c=2: 15.0/3.0/0.8
r=2% c=0.5: 18.7/3.7/0.9 | c=1: 16.6/3.3/0.8 | c=2: 13.6/2.7/0.7
r=3% c=0.5: 16.5/3.3/0.8 | c=1: 14.9/3.0/0.7 | c=2: 12.4/2.5/0.6
r=5% c=0.5: 13.5/2.7/0.7 | c=1: 12.4/2.5/0.6 | c=2: 10.6/2.1/0.5

### T3b years to cap, by regime (D=5M, c=1, q=2%, ICR250)
r=0% calm:9.9 bull:9.2 sideways:4.0 slowbear:2.1
r=1% calm:7.4 bull:7.0 sideways:3.5 slowbear:2.0
r=2% calm:5.9 bull:5.7 sideways:3.2 slowbear:1.8
r=3% calm:4.9 bull:4.8 sideways:2.8 slowbear:1.7
r=5% calm:3.7 bull:3.6 sideways:2.4 slowbear:1.5

### T4 borrower. y* = annual return the borrowed funds must earn to beat holding KAS (%/yr of debt), = -(delta0 - 2%*churn). fees-only cost = r+2%c+1%q
regime r  ICR | fees-only(c=1,q=2%) | y* c=1 q=2% | y* at r=0 | fee-attributable y*-y*0 | delta0 p10 (c=0 part)
calm      r=0% ICR200 | 2.02 | 7.54 | 7.54 | 0.00 | -24.46
calm      r=2% ICR200 | 4.02 | 9.62 | 7.54 | 2.08 | -26.51
calm      r=5% ICR200 | 7.02 | 12.81 | 7.54 | 5.28 | -31.36
calm      r=0% ICR250 | 2.02 | 3.79 | 3.79 | 0.00 | -6.79
calm      r=2% ICR250 | 4.02 | 5.96 | 3.79 | 2.17 | -9.26
calm      r=5% ICR250 | 7.02 | 9.10 | 3.79 | 5.31 | -12.15
calm      r=0% ICR300 | 2.02 | 2.50 | 2.50 | 0.00 | -1.22
calm      r=2% ICR300 | 4.02 | 4.63 | 2.50 | 2.13 | -4.13
calm      r=5% ICR300 | 7.02 | 7.84 | 2.50 | 5.34 | -8.68
bull      r=0% ICR200 | 2.02 | 32.49 | 32.49 | 0.00 | -91.94
bull      r=2% ICR200 | 4.02 | 35.60 | 32.49 | 3.11 | -93.28
bull      r=5% ICR200 | 7.02 | 40.28 | 32.49 | 7.80 | -95.56
bull      r=0% ICR250 | 2.02 | 14.74 | 14.74 | 0.00 | -32.90
bull      r=2% ICR250 | 4.02 | 18.27 | 14.74 | 3.53 | -36.04
bull      r=5% ICR250 | 7.02 | 23.41 | 14.74 | 8.67 | -40.81
bull      r=0% ICR300 | 2.02 | 7.35 | 7.35 | 0.00 | -8.05
bull      r=2% ICR300 | 4.02 | 10.76 | 7.35 | 3.41 | -13.63
bull      r=5% ICR300 | 7.02 | 15.82 | 7.35 | 8.46 | -22.14
sideways  r=0% ICR200 | 2.02 | 33.83 | 33.83 | 0.00 | -132.18
sideways  r=2% ICR200 | 4.02 | 35.40 | 33.83 | 1.57 | -136.20
sideways  r=5% ICR200 | 7.02 | 38.03 | 33.83 | 4.20 | -134.62
sideways  r=0% ICR250 | 2.02 | 19.37 | 19.37 | 0.00 | -65.12
sideways  r=2% ICR250 | 4.02 | 21.40 | 19.37 | 2.03 | -66.93
sideways  r=5% ICR250 | 7.02 | 24.99 | 19.37 | 5.62 | -73.71
sideways  r=0% ICR300 | 2.02 | 11.25 | 11.25 | 0.00 | -41.77
sideways  r=2% ICR300 | 4.02 | 13.54 | 11.25 | 2.29 | -46.69
sideways  r=5% ICR300 | 7.02 | 16.98 | 11.25 | 5.73 | -47.74
slowbear  r=0% ICR200 | 2.02 | -25.19 | -25.19 | 0.00 | -29.52
slowbear  r=2% ICR200 | 4.02 | -24.66 | -25.19 | 0.53 | -31.55
slowbear  r=5% ICR200 | 7.02 | -23.67 | -25.19 | 1.52 | -34.67
slowbear  r=0% ICR250 | 2.02 | -18.08 | -18.08 | 0.00 | -26.59
slowbear  r=2% ICR250 | 4.02 | -17.27 | -18.08 | 0.81 | -28.66
slowbear  r=5% ICR250 | 7.02 | -16.04 | -18.08 | 2.05 | -29.77
slowbear  r=0% ICR300 | 2.02 | -10.91 | -10.91 | 0.00 | -24.67
slowbear  r=2% ICR300 | 4.02 | -9.95 | -10.91 | 0.95 | -25.20
slowbear  r=5% ICR300 | 7.02 | -8.52 | -10.91 | 2.39 | -27.09
mix       r=0% ICR200 | 2.02 | 12.17 | 12.17 | 0.00 | -69.53
mix       r=2% ICR200 | 4.02 | 13.99 | 12.17 | 1.82 | -71.88
mix       r=5% ICR200 | 7.02 | 16.86 | 12.17 | 4.70 | -74.05
mix       r=0% ICR250 | 2.02 | 4.96 | 4.96 | 0.00 | -32.85
mix       r=2% ICR250 | 4.02 | 7.09 | 4.96 | 2.13 | -35.22
mix       r=5% ICR250 | 7.02 | 10.37 | 4.96 | 5.41 | -39.11
mix       r=0% ICR300 | 2.02 | 2.55 | 2.55 | 0.00 | -18.93
mix       r=2% ICR300 | 4.02 | 4.75 | 2.55 | 2.20 | -22.41
mix       r=5% ICR300 | 7.02 | 8.03 | 2.55 | 5.48 | -26.41

### T5 liquidations & fee effect on ICR (c-independent), q=2%: share of vaults liquidated in year | bad debt % of D0 | (end ICR omitted; analytic: the fee removes r/ICR0 of collateral per year)
calm      ICR200 r=0%: 29.09|0.00 ; r=2%: 30.50|0.00 ; r=5%: 31.92|0.00
calm      ICR250 r=0%: 11.99|0.00 ; r=2%: 12.62|0.00 ; r=5%: 13.37|0.00
calm      ICR300 r=0%: 3.73|0.00 ; r=2%: 3.93|0.00 ; r=5%: 4.23|0.00
bull      ICR200 r=0%: 19.79|0.00 ; r=2%: 20.00|0.00 ; r=5%: 20.47|0.00
bull      ICR250 r=0%: 10.58|0.00 ; r=2%: 10.84|0.00 ; r=5%: 11.11|0.00
bull      ICR300 r=0%: 5.18|0.00 ; r=2%: 5.27|0.00 ; r=5%: 5.37|0.00
sideways  ICR200 r=0%: 52.98|0.00 ; r=2%: 53.32|0.00 ; r=5%: 54.24|0.00
sideways  ICR250 r=0%: 35.62|0.00 ; r=2%: 35.91|0.00 ; r=5%: 36.67|0.00
sideways  ICR300 r=0%: 23.31|0.00 ; r=2%: 23.56|0.00 ; r=5%: 24.05|0.00
slowbear  ICR200 r=0%: 85.27|0.00 ; r=2%: 85.47|0.00 ; r=5%: 86.26|0.00
slowbear  ICR250 r=0%: 75.58|0.00 ; r=2%: 76.00|0.00 ; r=5%: 76.72|0.00
slowbear  ICR300 r=0%: 64.10|0.00 ; r=2%: 64.52|0.00 ; r=5%: 65.13|0.00

### T6 junior gross yield, % of junior notional per yr = F/s (mix of regimes; c=1,q=2%,ICR250). D1 = 100% fee to junior; D2 pre-cap = 80%; D2 post-cap = D1; D3 = 0. Net of bad debt absorbed.
r=0% s=15%: D1 46.40, D2pre 37.12 | s=30%: D1 23.20, D2pre 18.56 | s=50%: D1 13.92, D2pre 11.14
r=1% s=15%: D1 53.29, D2pre 42.64 | s=30%: D1 26.65, D2pre 21.32 | s=50%: D1 15.99, D2pre 12.79
r=2% s=15%: D1 60.20, D2pre 48.16 | s=30%: D1 30.10, D2pre 24.08 | s=50%: D1 18.06, D2pre 14.45
r=3% s=15%: D1 67.11, D2pre 53.69 | s=30%: D1 33.56, D2pre 26.84 | s=50%: D1 20.13, D2pre 16.11
r=5% s=15%: D1 80.89, D2pre 64.71 | s=30%: D1 40.45, D2pre 32.36 | s=50%: D1 24.27, D2pre 19.41

### T6b junior wrong-way: D1 yield s=30% by regime, receipt-value vs held-in-KAS marked at year end; p10 of fee (% of debt)
calm      r=0% | at receipt 10.08 | held in KAS 10.41 | corr(fee USD, KAS ret)=-0.42 | mtm p10 fee %debt 0.02
calm      r=2% | at receipt 16.91 | held in KAS 17.90 | corr(fee USD, KAS ret)=-0.43 | mtm p10 fee %debt 1.83
calm      r=5% | at receipt 27.14 | held in KAS 28.88 | corr(fee USD, KAS ret)=-0.44 | mtm p10 fee %debt 4.55
bull      r=0% | at receipt 10.88 | held in KAS 17.69 | corr(fee USD, KAS ret)=-0.22 | mtm p10 fee %debt 0.02
bull      r=2% | at receipt 17.65 | held in KAS 29.55 | corr(fee USD, KAS ret)=-0.22 | mtm p10 fee %debt 2.19
bull      r=5% | at receipt 27.77 | held in KAS 46.93 | corr(fee USD, KAS ret)=-0.22 | mtm p10 fee %debt 5.43
sideways  r=0% | at receipt 24.80 | held in KAS 29.79 | corr(fee USD, KAS ret)=-0.45 | mtm p10 fee %debt 0.02
sideways  r=2% | at receipt 31.69 | held in KAS 37.94 | corr(fee USD, KAS ret)=-0.45 | mtm p10 fee %debt 1.96
sideways  r=5% | at receipt 42.09 | held in KAS 50.32 | corr(fee USD, KAS ret)=-0.45 | mtm p10 fee %debt 4.86
slowbear  r=0% | at receipt 47.04 | held in KAS 33.29 | corr(fee USD, KAS ret)=-0.47 | mtm p10 fee %debt 0.03
slowbear  r=2% | at receipt 54.15 | held in KAS 38.03 | corr(fee USD, KAS ret)=-0.47 | mtm p10 fee %debt 2.57
slowbear  r=5% | at receipt 64.78 | held in KAS 45.16 | corr(fee USD, KAS ret)=-0.47 | mtm p10 fee %debt 5.36

### T7 s* = largest junior share s (1% grid) with net yield >= hurdle h; 100% = nobody needs to be compensated beyond; mix regimes; c=1,q=2%,ICR250. cols D1 | D2pre | D1-held-in-KAS | D3
mix h=5% r=0%: 100|100|100|0 ; r=1%: 100|100|100|0 ; r=2%: 100|100|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
mix h=10% r=0%: 69|55|68|0 ; r=1%: 79|63|80|0 ; r=2%: 90|72|92|0 ; r=3%: 100|80|100|0 ; r=5%: 100|97|100|0
mix h=20% r=0%: 34|27|34|0 ; r=1%: 39|31|40|0 ; r=2%: 45|36|46|0 ; r=3%: 50|40|52|0 ; r=5%: 60|48|64|0
calm h=5% r=0%: 60|48|62|0 ; r=1%: 80|64|85|0 ; r=2%: 100|81|100|0 ; r=3%: 100|97|100|0 ; r=5%: 100|100|100|0
calm h=10% r=0%: 30|24|31|0 ; r=1%: 40|32|42|0 ; r=2%: 50|40|53|0 ; r=3%: 60|48|64|0 ; r=5%: 81|65|86|0
calm h=20% r=0%: 15|12|15|0 ; r=1%: 20|16|21|0 ; r=2%: 25|20|26|0 ; r=3%: 30|24|32|0 ; r=5%: 40|32|43|0
bull h=5% r=0%: 65|52|100|0 ; r=1%: 85|68|100|0 ; r=2%: 100|84|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
bull h=10% r=0%: 32|26|53|0 ; r=1%: 42|34|71|0 ; r=2%: 52|42|88|0 ; r=3%: 63|50|100|0 ; r=5%: 83|66|100|0
bull h=20% r=0%: 16|13|26|0 ; r=1%: 21|17|35|0 ; r=2%: 26|21|44|0 ; r=3%: 31|25|53|0 ; r=5%: 41|33|70|0
sideways h=5% r=0%: 100|100|100|0 ; r=1%: 100|100|100|0 ; r=2%: 100|100|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
sideways h=10% r=0%: 74|59|89|0 ; r=1%: 84|67|100|0 ; r=2%: 95|76|100|0 ; r=3%: 100|84|100|0 ; r=5%: 100|100|100|0
sideways h=20% r=0%: 37|29|44|0 ; r=1%: 42|33|50|0 ; r=2%: 47|38|56|0 ; r=3%: 52|42|63|0 ; r=5%: 63|50|75|0
slowbear h=5% r=0%: 100|100|100|0 ; r=1%: 100|100|100|0 ; r=2%: 100|100|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
slowbear h=10% r=0%: 100|100|99|0 ; r=1%: 100|100|100|0 ; r=2%: 100|100|100|0 ; r=3%: 100|100|100|0 ; r=5%: 100|100|100|0
slowbear h=20% r=0%: 70|56|49|0 ; r=1%: 75|60|53|0 ; r=2%: 81|64|57|0 ; r=3%: 86|69|60|0 ; r=5%: 97|77|67|0

### T7b s* for mix, h=10%, by churn (D1)
c=0.5 r=0%: 59 ; r=1%: 69 ; r=2%: 80 ; r=3%: 90 ; r=5%: 100
c=1 r=0%: 69 ; r=1%: 79 ; r=2%: 90 ; r=3%: 100 ; r=5%: 100
c=2 r=0%: 89 ; r=1%: 99 ; r=2%: 100 ; r=3%: 100 ; r=5%: 100

### bad debt (all vaults) % of D0, max over 300 paths, by regime ICR200 r=0/5%
calm r=0%:mean 0.00 p90 0.00 max 0.00 r=5%:mean 0.00 p90 0.00 max 0.00
bull r=0%:mean 0.00 p90 0.00 max 0.00 r=5%:mean 0.00 p90 0.00 max 0.00
sideways r=0%:mean 0.00 p90 0.00 max 0.00 r=5%:mean 0.00 p90 0.00 max 0.00
slowbear r=0%:mean 0.00 p90 0.00 max 0.00 r=5%:mean 0.00 p90 0.00 max 0.00
