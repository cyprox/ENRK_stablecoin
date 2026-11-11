#!/bin/bash
# Why: reproduce raw data fetch (public keyless GETs only). Output into ../raw. Date of original fetch 2026-11-10.
cd "$(dirname "$0")/../raw"
curl -s -m 60 "https://api.kaspa.org/info/hashrate/history?resolution=1d" -o hh_1d.json
for y in 2021 2022 2023 2024 2025 2026; do for m in 01 02 03 04 05 06 07 08 09 10 11 12; do
  ym=$y-$m; [[ "$ym" < "2021-11" || "$ym" > "2026-11" ]] && continue
  [ -s tx_$ym.json ] || curl -s -m 60 "https://api.kaspa.org/transactions/count/$ym" -o tx_$ym.json
  [ -s ad_$ym.json ] || curl -s -m 60 "https://api.kaspa.org/addresses/active/count/$ym" -o ad_$ym.json
done; done
for id in PNRGINDEXM APU000072610 POILBREUSDM; do curl -s -m 40 "https://fred.stlouisfed.org/graph/fredgraph.csv?id=$id&cosd=2010-01-01" -o fred_$id.csv; done
curl -s -m 40 "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU&cosd=2021-01-01" -o fred_DCOILBRENTEU.csv
S=$(date -j -f %Y-%m-%d 2021-11-01 +%s); E=$(date -j -f %Y-%m-%d 2023-06-01 +%s)
curl -s -m 40 "https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair=KAS_USDT&interval=1d&from=$S&to=$E" -o gate_KAS_early.json
