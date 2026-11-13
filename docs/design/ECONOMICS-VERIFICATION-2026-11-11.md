# ENRK — Economic and mechanism verification round

**Date:** November 11, 2026 (second round added November 13, 2026, §10)
**Status:** Findings. **No design decision is taken here.** Every "proposal" is awaiting the owner. Companion to [`AUDIT-2026-11-09.md`](AUDIT-2026-11-09.md) (§13 holds the Kaspa fact base and the testnet-10 results).
**What this is:** the consolidation of a round of simulations, local executions and research made by AI sub-agents under the lead session, each proposal tested and then reviewed by an independent adversarial pass. Raw reports and the scripts that produced them are in [`studies-2026-11/`](studies-2026-11/) (see §7). All numbers are **model outputs under stated assumptions, not forecasts**.

---

## 1. Headline

1. **No architecture within the tested bounds (stability fee ≤ 3 %, junior share ≤ 50 %) is both safe and self-consistent when the peg index does not fall with KAS.** The earlier candidate (junior 30 %, fee 3 %, all fees to the junior, surplus to the borrower) holds only on the original simulator's default, where the index falls to about 0.54 at KAS −85 % — a hidden 46 % cushion on debt value. With a flat index: ENRK p95 loss 13.8 % (not 3.0 %), kFIAT mean loss 25.7 % (not 8.4 %), junior net −15.5 % (not +1.8 %). The simulator's published figures (`FROZEN_PARAMETERS.md`) inherit the same cushion.
2. **The index is the dominant risk, not the fee.** Index noise (5–22 % vol) adds nothing measurable; index *drift* during the crash does: unbacked debt rises from 10.5 % (flat) to 15.6 / 19.9 / 26.8 % (index ×1.5 / ×2 / ×3).
3. **The circuit breaker as coded is harmful.** It trips on noise in 41 % of 60-day windows; if it halts liquidations, unbacked debt at index ×2 goes from 19.9 % to 86.8 %. A breaker must never halt liquidations.
4. **A fee reserve paying incentives on depeg is the wrong use of the reserve in solvency events.** For solvency shocks, using the reserve to absorb losses dominates; for short liquidity shocks, incentives help modestly.
5. **The sustainable debt is small relative to market liquidity** (a few percent of daily volume at plausible liquidator capital, which is unmeasured), so a hard debt ceiling is not optional.
6. **The Argent issuance-cap example is bypassable** (negative mint, extra controller entry) and must not be copied as is.

## 2. Corrections of earlier statements (registry)

| Earlier statement | Status |
|---|---|
| "The crash simulator keeps the index flat" | **False.** Hashrate ^0.4, fees ^0.6, adoption ^0.3 respond to KAS; only energy is fixed. |
| "Fee r ≈ 3 % makes a 30 % junior safe and self-consistent" | **Holds only on the cushioned base.** Also, r = 3.0 % sits at an edge of the simulator's 153 % opening-ICR floor (r = 3.0 % → 0 pre-crash liquidations; 3.5 % → 115). |
| "Redemption-fee rebate is the most efficient peg tool (+41 %)" | **Metric artefact.** Area is measured above 1 point of depeg and the 1 % fee itself creates the 98.5 % band; maximum depth improves only 3–6 %. |
| "A price move bound of 10 % per 600 DAA allows ×1.77 per hour" | **Wrong by ~100×.** At one-minute gaps the bound permits about 117–300× per hour (1.77 = 1.1⁶ is a 10-minute gap). |
| "Unbacked debt rises with junior share" | Artefact: with redemption off it is constant (17.0 for s = 0/30/50); the exogenous redemption schedule is a second built-in cushion (about 45 % of the hole). |
| Standard-mass cap 100,000, N ≈ 120–130 | Withdrawn earlier (AUDIT §13.5). |
| Testnet-12 absent from the sources | Withdrawn earlier (it exists; AUDIT §13.3b). |

The earliest economic studies (`econ-m1`, `m2`, `t1`, `t2`) were **not re-based** on a non-cushioned index; `econ-v1` re-bases the architecture comparison. T2's demand-and-junior intersection (r_clear ≈ 3.3 %) does not hold on a flat index (expected junior return 7.5 % < 10 % hurdle).

## 3. Architecture on adverse bases (500 paired paths; `econ-v1`)

Crash KAS −85 % over 60 days unless noted; ENRK p95 loss / kFIAT mean loss / junior net return (% of face).

| Architecture | orig. (cushioned) | flat index | index ×2 |
|---|---|---|---|
| A0: no fee, no junior | – | 25.4 | 21–32 |
| **A3: fee 3 %, junior 30 %, D1, surplus S1 (candidate)** | 3.0 / 8.4 / +1.8 | **13.8 / 25.7 / −15.5** | 20.0 / 37.3 / −27.2 |
| A5: A3 with surplus to a reserve (S3) | – | 12.5 / 8.5 / +1.7 | 18.4 / 13.2 / −3.1 |
| A8: fee 3 %, junior 50 % | – | 5.4 / – / – | 10.5 |
| A7: A3 + deepening floor (C1a) + sub-par redemption (C2) | – | 11.2 / 27.7 / −17.6 | 16.7 |
| Exploratory stack: fee 3 %, junior 70 %, S3, C1a + C2 | – | holds (ENRK p95 0.0–0.9) | holds |

"Survive / hold" thresholds are the analyst's labels (survive: ENRK p95 ≤ 2 %, latent p95 ≤ 1 %, unbacked mean ≤ 3 %; hold: ≤ 5 %). The stack that holds needs a 70 % junior, above any voluntary equilibrium (23–28 % at a 10 % hurdle). "No tested architecture survives" is robust (fails by 6–25 points); the latent-hole percentile is a knife edge (x2: 4.9 on 500 paths, 0.0 on 1000).

## 4. Verdicts per proposal (ledger P1–P21)

Verdict and confidence are the independent reviewer's (`econ-v5`), with the authors' evidence. Full ledger: [`studies-2026-11/reports/proposal-ledger.md`](studies-2026-11/reports/proposal-ledger.md).

| ID | Proposal | Verdict (confidence) | Key evidence |
|---|---|---|---|
| P1 | Stability fee r ≈ 3 %/yr in KAS, to the junior | PARTLY (medium): REFUTED as a safety lever for r ≤ 3 %; r > 3 % UNTESTABLE | ENRK p95 moves < 1 point for r ∈ {0,1,2,3}; junior net negative on every adverse base; r ≥ 5 % only looks better through the pre-crash cull artefact |
| P2 | Junior kFIAT 30 %, mandatory or voluntary | PARTLY (medium): REFUTED at 30 % | flat85 ENRK p95 by s = 0/15/30/50: 24.0/19.2/13.8/5.4; voluntary equilibrium 24–28 % at a 10 % hurdle, none at 20 % |
| P3 | kFIAT denomination (fixed face vs write-down index) | NEEDS DECISION (high) | The two forms are identical on every aggregate (an identity); the difference is global state on UTXO and the destination of the excess |
| P4 | Loss rule | PARTLY (medium) | Waterfall stays; uncapped carry-over turns loss into a latent hole (flat85: latent p95 28.8, freeze 35 of 60 days); capped carry-over gives no protection on adverse bases |
| P5 | Auction surplus split | PARTLY (medium) | To the junior: pays, protects nothing (exact identity); to a reserve: only protection, pays nobody; the reserve "counts as collateral" has no verified L1 form |
| P6 | Fee reserve granting incentive yield on depeg | PARTLY / NEEDS DECISION (low) | Rebate helps liquidity shocks marginally and worsens small solvency shocks; depeg-triggered yield turns oracle error into a subsidy above ≈ 3 % noise and needs a minimum lock (7 days); loss absorption dominates for solvency |
| P7 | Free/paid-debt split (Monolith) as oracle-free peg signal | PARTLY (medium) | Signal weak and slow; an explicit maximum rate is necessary (22–29 % at day 720 without it); integer exponential controller exact in 5,324 runs; shard write authentication unsolved |
| P8 | ENRK's own price oracle | NEEDS DECISION (medium) | Nothing to price at launch (no ENRK market); a bounded price UTXO executed locally (30 cases); staleness provable only as a lower bound; refresh of the whole population never executed |
| P9 | Targeted single-borrower redemption | PARTLY (medium) | Local execution; ordering is an incentive, not a guarantee; stale-sibling attack found |
| P10 | Graceful stale-oracle degradation | PARTLY (medium) | Provable as a lower bound only; owner "reduce-only" cannot be enforced |
| P11 | Design invariants and covenant-fixed issuance caps | PARTLY REFUTED (high) | Negative mint raised a cap 100 → 105; an extra controller entry minted 1e12 against a cap of 100 |
| P12 | Clean/dirty liquidation fee, no close factor | PARTLY (medium) | Executed; needs a minimum payout; a fully seized vault leaves a zero-value successor |
| P13 | Hard debt ceiling sized on liquidity | PARTLY, number UNTESTABLE (low) | Survivable debt ≈ 1.7–9 % of daily volume at 0.5–2 % liquidator capital (unmeasured); current modelled system ≈ 22 % |
| P14 | Unfreeze: deepening floor (C1), sub-par redemption (C2) | PARTLY (low–medium) | C1 realises the hole instead of removing it (ENRK p95 11.0 → 16.6); C2 modest; depends on bidder behaviour |
| P15 | Index fixes (unit L, baseline, energy source, legs, breaker, bounds) | NEEDS DECISION (medium–high); breaker halting liquidations harmful (high) | See §5 |
| P16 | L1 fee/distribution mechanisms | PARTLY (medium) | Harvest 5 vaults/tx (not 160), surplus routing 3 vaults/tx (not 150), clock lag 130–140 s |
| P17 | Declared-outputs co-spend fix | CONFIRMED (medium) | Executed on testnet-10 (AUDIT §13.3b) |
| P18 | `icr_percent` discipline | CONFIRMED (high) | 10,716 engine runs, 0 mismatches; unguarded fails exactly at `c·p·100 > 2⁶³−1`; guarded needs oracle price bounds |
| P19 | Stability Pool removal, bids in ENRK | PARTLY (medium) | Executed locally (9 % bonus); supply bookkeeping and many vault families open |
| P20 | Oracle sweep price bounds | PARTLY (medium) | ±10.00 % accepted, ±10.01 % rejected; **the bound alone permits ~117–300× per hour at one-minute gaps** |
| P21 | Population/genesis storage sizing rules | CONFIRMED (medium) | Executed (AUDIT §13.3b); not re-run in this round |

## 5. Index design (P15), in short (`econ-v6`)
- **Drift, not noise, makes the damage.** Unbacked mean at index ×2: 19.9 coded, 10.5 with the unit fixed at 1 USD, 12.3 with a 0.25 %/day rate limit, 15.0 with half slope above 1, 16.1 with a cap at 1.10.
- **Baseline convention flips the sign** of the index effect on the same vault (2024-07-31 vault at 101 % on KAS alone: 66 % under full-mean baseline, 110 % under trailing-365).
- **Fee and adoption legs are unusable as coded** (fee leg constant 0.1; index vol 104 % with the polluted proxies, 23–32 % without).
- **Energy source:** monthly series with 1–6 weeks delay (IMF 30 % vol, US electricity 4 %); a Kaspa-native proxy is pro-cyclical (corr 0.57 with KAS, vol 144 %).
- **Minimal-cost shape tested:** slow up, immediate down; costs holders the upside (−0.75 to −0.90 of index value). Fixing the unit at 1 USD removes holders' index exposure entirely.
- **ENRK holder "yield" from the index** is not a yield: zero-sum between holders and borrowers, 365-day return from about −60 % to +140 % without a centre.

## 6. Blind spots (ranked by the independent review)
1. Reactive borrowers (top-ups, exits, self-liquidation, reaction to surplus withheld).
2. Correlated KAS price, redemption demand, ENRK demand and liquidator capital (the redemption schedule is exogenous).
3. Oracle dependence of the unfreeze mechanisms; the whole-population refresh was never executed, so stale siblings are not bounded.
4. A single trust surface (price and index publishers) and the legal/trust aspect of a perpetual key or a reserve paying individuals.
5. Data gaps: a 3.6-year bear-heavy KAS history, no fee series, one order-book snapshot, unknown wash trading, no ENRK market.
6. Liveness of the constrained design and keeper funding (oracle upkeep about 19–128 USD/day).
7. Tail frequency and repeated shocks; the stress-sensitivity cliff at 0.25–0.28 is unmeasured.
8. No end-to-end comparison against alternative architectures.

## 7. Where things are
- [`studies-2026-11/reports/`](studies-2026-11/reports/): the 25 reports (audit phase p1–p5b, Kaspa facts r1–r4, economics m1/m2/a3/a4/t1–t4, verification v1–v6, the ledger). Each tags its claims and states what was not done.
- [`studies-2026-11/sources/`](studies-2026-11/sources/): scripts, contracts and harnesses by study (`econ/<study>/`), the testnet-10 harness (`testnet10-harness/`), the market-data script (`market/`), the original-simulator check (`original-sim-check/`). **Large data (pickles, raw price series, fetched web pages) are not committed**: they are regenerated by the commands in each report. No key, secret or wallet address is in this folder (checked by comparison against the key file and the address file).
- Reproduction: each report ends with exact commands. The simulator extensions have an equivalence check that must show 0 differences against the original `tests/backtesting/stress_test_crash.py` with every new feature off.
- Testnet-10 transactions are identified by their (public) ids in AUDIT §13.3b and in `reports/econ-t4-tn10-fee-mechanisms.md`.

## 8. Limits of this round
- All studies are scratch modelling: no `qgate`, no done-check, no code-map entry; the scripts carry no "Why:" docstrings tied to a decision reference. They are evidence, not project code.
- Re-execution by the reviewer proves reproducibility, not independence (the simulator was not re-implemented).
- Persistent model flaws (see `reports/p3-sim.md`, `econ-m2`): permanent cumulative square-root impact, passive borrowers, an opening-ICR floor at 153 %, an uncalibrated liquidation capacity (5 %/day), an exogenous redemption schedule, a median-log meaning of "−85 %".
- Local script-engine executions do not exercise node finality, mempool rules or mainnet contention; constants in test contracts are test values, not proposals.

## 9. Decisions that belong to the owner
1. The fate of the peg index: fixed unit (e.g. 1 USD), slow-up/immediate-down bound, or another form; baseline and energy source.
2. Whether the breaker may ever act on liquidations (the tests say no) and on what trigger.
3. The loss-absorption structure: reserve of surplus, junior share (30 % is not enough on adverse bases), or a stack; and what the junior is paid.
4. The role of the fee reserve: loss absorption (recommended by the tests for solvency events) versus incentives.
5. The ENRK price oracle: phased start (informative, then k-of-n, then triggers requiring two venues).
6. The debt ceiling and how liquidator capital is measured (data collection first).
7. The issuance-cap design (not the Argent example).
8. Whether to run the three gap-fillers: reactive borrowers, re-basing `m2`/`t1`/`t2` on a non-cushioned index, executing the whole-population refresh on testnet-10.

---

## 10. Second round: units of account, whole-population oracle refresh, market data (owner-approved steps 0, 1a, 1b)

Reports: [`econ-w1-unit-variants-rebase.md`](studies-2026-11/reports/econ-w1-unit-variants-rebase.md), [`econ-x1b-population-refresh.md`](studies-2026-11/reports/econ-x1b-population-refresh.md); sources under `studies-2026-11/sources/econ/{w1,x1b}/` and `sources/market/collect_orderbooks.py`. These two reports have **not** yet been through the independent review that covered the first round.

### 10.1 The unit of account does not change crash safety (W1)
- Units tested: the coded index (without the hidden cushion), USD, CNY, USD/EUR/CNY, USD/CNY/RUB (equal and 50/30/20), electricity only, gold, and a bounded "slow-up" index. Data: FRED (CNY onshore, EUR, electricity), the Central Bank of Russia official XML (RUB), futures for gold (unofficial), keyless public GETs on 2026-11-11.
- **KAS risk dominates** (KAS volatility 97 % against 3.0 % for CNY, 4.5 % for the USD/CNY/RUB basket). Crash simulation of the candidate (fee 3 %, junior 30 %, KAS −85 %): ENRK p95 loss 13.7–14.5 % in every stable unit (USD 13.8 %); paired differences against USD −0.03 to +0.05 points. The ordering of architectures is the same on every unit.
- **What depends on the unit:** a large and *fast* revaluation of the unit inside the crash (speed matters about 4.7× more than level: +20 % in one step on day 5 adds 10.3 points of unbacked debt, +20 % ramped over 60 days adds 2.2). Worst 60-day revaluations since 2005: CNY +6.8 %, USD/EUR/CNY +5.2 %, USD/CNY/RUB equal +24.8 % (50/30/20: +14.3 %), RUB alone +80.6 %, gold +33 %, electricity +9 %. Devaluations of the unit (CNY 2015–16 −10.6 %, 2018 −9.9 %, 2022 −13.2 %) lower debt value and help the system but cost holders.
- A RUB leg raises the basket's worst 60-day revaluation about five-fold without measured benefit. Oracle and legal facts (listed, **not assessed**): Pyth and Chainlink list USD/CNY, EUR/USD and gold, no RUB feed; the official RUB rate lies up to 16.3 % below the market quote on stress days; OFAC Directive 4 (2022-02-28) prohibits transactions with the Central Bank of Russia and the scope for publishing a rate derived from it was not assessed. No keyless offshore-yuan (CNH) history exists, so the onshore/offshore gap is not quantified.
- Holders (USD terms, A3 crash): USD −3.2 % mean (p5 −13.6 %), CNY −3.0 %, USD/CNY/RUB −3.1 %, gold −1.0 %, coded index −3.3 % (p5 −18.6 %); a unit that loses 10–20 % dominates the crash loss from about 5 %.
- **Re-based conclusions (no cushion, r ≤ 3 %, so the 153 % artefact is not involved):** junior expected return at s = 30 %, crash probability 10 %/yr: −2.7 / +0.6 / +3.9 / +7.4 for r = 0 / 1 / 2 / 3 %; voluntary junior share s* at r = 3 %: 44 % (hurdle 5 %), 26 % (10 %), none (20 %); fee at which a 30 % junior clears: 2.3 % / about 3.7 % / about 6.5 % (T2 had 1.8 / 3.3 / 6.8). The self-consistency gap remains: s* ≈ 26 % gives ENRK p95 14–19 %, while s = 50 % gives 5.4 %.
- At KAS −70 % the exploratory stack sits at the survive edge (unbacked 2.8–2.9 %) and flips to 3.2–3.6 % with a +10 to +20 % unit revaluation, with gold, or with the coded index.

### 10.2 Whole-population oracle refresh executed on testnet-10 (X1B)
- A single transaction that consumes all N sibling price UTXOs and recreates them at a **changed price** works on chain, in two forms: (b) a leader entry with follower inputs (max **N = 46**: compute 487,182 = 97.4 % of the limit, 6.9 s to confirm, fee 0.487 TKAS; N = 47 refused on compute 507,273; N = 128 does not compile, the script exceeds the 250,000-byte limit) and (a) a single actor (max N = 15: transient 1,057,220 > 1,000,000 at N = 16). Form (b) is cheaper at every N.
- The accepted form for the consumed range: the first input runs `refresh(sig, new_price)` with the other siblings consumed through a no-argument delegate entry; the earlier failure (V3) came from spending the other inputs through the leader entry.
- **The completeness guard is essential and was demonstrated by a negative control on chain**: a variant without the all-N check refreshed two of four siblings, and a vault withdrawal was accepted on chain against the stale sibling at the old price (mass 11,990). With the guard (count equals n, slot equals index, equal round and price among siblings), a missing, extra, duplicated or mixed sibling is rejected (20+ local negatives); an attempt to spend an old sibling after a refresh is refused by the node with its generic missing-input message ("consumed, therefore gone" is derived, not stated by the node).
- Cost: about 20× more per UTXO than a plain value-preserving `use` round; at one refresh every 10 s the floor fee is 187 TKAS/day (b, N = 4) to 4,209 TKAS/day (b, N = 46), divided by 6 at one refresh per minute. **A 640-UTXO population cannot be refreshed in one transaction with this form**: the design must aim at a few dozen siblings or a single price UTXO.
- A vault liquidation reads the new price after a refresh (b, N = 8, price 0.891, ICR 142.6, mass 3,369); at the old prices the liquidation does not build.
- Net spend 5.104 TKAS, all fees (72 accepted transactions); every test contract was drained. Limits: lightly loaded testnet, one sample per row, constants are test values, publisher-key compromise not tested, transient and storage mass from the local calculator, N > 46 derived.

### 10.3 Order-book collection started (step 0)
`sources/market/collect_orderbooks.py` takes a manual one-shot snapshot of six KAS venues (public GETs, no scheduler) into `~/ENRK_market_data/` (raw JSON files read-only, plus `index.csv`). The first snapshot (calm, 2026-11-11): merged bid depth within 5 % of the best bid about 621,000 USD (about 480,000 on 2026-11-10), Kraken more than half; per-venue impact coefficient at 1 % of daily volume 0.009–0.043, merged 0.013. The data folder is outside the repository; it can be moved on the owner's instruction. A calm snapshot does not measure stressed depth: extra snapshots are to be taken on days when KAS moves more than 8 %.

### 10.4 What this changes
- The choice of the unit (USD, CNY, basket) is a **trust, oracle and consistency decision** (the founding thesis states "no USD, no fiat"), not a crash-safety decision; a RUB leg adds revaluation risk and legal exposure for no measured gain.
- The oracle design must carry the all-N completeness guard, must accept that populations are limited to dozens of siblings (or a single price UTXO), and must budget its refresh cost; who pays remains open in a system without governance.
- Still open from the first round: reactive borrowers, correlated shocks, the oracle dependence of the unfreeze, and a calibrated liquidator capital (the market data above is the first input).

