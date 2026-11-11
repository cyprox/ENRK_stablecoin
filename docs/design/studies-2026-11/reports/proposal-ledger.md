# ENRK proposal ledger (2026-11-11) — every proposal made so far, to be VERIFIED

Status vocabulary for verdicts: CONFIRMED / PARTLY CONFIRMED / REFUTED / UNTESTABLE HERE (say why) / NEEDS DECISION. Each verdict needs evidence (script + numbers, source line, compiled or executed result). Nothing here is a design decision: all are proposals awaiting the owner.

Owner directions so far (2026-11-10/11): recurring stability fee YES; NO burning of fees, they must remunerate (incentive); surplus destination decided by tests; stay on testnet-10; ENRK must have ITS OWN PRICE ORACLE; the Monolith "free vs paid debt" avenue is to be explored as an additional path; the owner's idea: accumulate fees in a reserve used to grant incentive yield that becomes active in case of depeg.

Prior evidence (reports in scratchpad/reports): p1..p5b (audit), r1..r4 (Kaspa facts, tooling, ecosystem, market), econ-m1 (normal-time revenue), econ-m2 (crash + fees; validated 0 differences vs original), econ-a3 (UTXO feasibility), econ-a4 (peg index vs KAS), econ-t1 (surplus split), econ-t2 (demand elasticity), econ-t3 (index in crash; KEY: the original simulator's default IndexResponse makes the index FALL with KAS to ~0.54 at -85%, a 46% built-in cushion; with a flat index ENRK p95 13.8% vs 3.0%, junior net -15.5% vs +1.8%), econ-t4 (testnet-10 fee mechanisms). Other conversation of the owner: docs/design/MONOLITH-COMPARISON-2026-11-10.md, FRAX-COMPARISON-2026-11-11.md, FIAT-STABLECOINS-RAPPEL-2026-11-11.md (read-only, do not edit).

| ID | Proposal | Prior evidence |
|---|---|---|
| P1 | Stability fee r (~3%/yr) paid in KAS from vault collateral, 100% to junior holders (D1); variants D2 (20% treasury until 2.5M-unit cap, then junior), D3 (reserve) | m2, t1, t2, t3; sign of junior net depends on index direction and the two unmeasured parameters |
| P2 | Junior tranche kFIAT ~30%: mandatory at mint vs voluntary at equilibrium share s*; vs no junior | m2/t3 s* 23-29% at h=10%; fragile when index does not fall |
| P3 | kFIAT denomination: A1 fixed face in peg units / A2 write-down index / A3 market | KFIAT-DEFINITION-GAP.md, p5b |
| P4 | Loss rule: waterfall (kFIAT then ENRK) vs carry-over to borrowers (uncapped / capped) | p3-sim |
| P5 | Auction surplus: S1 owner, S2 junior, S3 reserve, or a split | t1: S2 pays but protects nothing; S3 protects, nothing paid |
| P6 | Owner idea: fee reserve granting incentive yield that activates on depeg; variants: redemption-fee rebate, variable yield on locked ENRK, loss-absorbing reserve | none yet; FROZEN_PARAMETERS §7 rejects a visible finite reserve paying individuals |
| P7 | Monolith avenue: free-debt (0%, redeemable) vs paid-debt (interest, not redeemable) split as an oracle-free peg signal driving a rate controller, with an EXPLICIT maximum rate | Monolith doc only |
| P8 | ENRK's own price oracle (owner direction): design, data sources, manipulation resistance, L1 form, how it triggers P6/P7 | none |
| P9 | Targeted single-borrower redemption (vs pro-rata / lowest-ICR-first sweep) | Monolith doc; redemption unimplemented in Rust |
| P10 | Graceful stale-oracle degradation (reduce-only, decaying price) vs ENRK's guard | Monolith doc |
| P11 | Design invariants: no freeze, no pause, no owner burn, no backing sweep; per-family issuance caps fixed by covenant | Frax doc; Argent open-ICC hidden mutability channel (r2) |
| P12 | Clean/dirty liquidation fee, no close factor | Frax doc |
| P13 | Hard debt ceiling or ramp sized from measured KAS liquidity | r4, p5b |
| P14 | Unfreeze without governance: C1 deepening auction floor, C2 sub-par redemption for vaults under 100% ICR | p5b, p3-sim |
| P15 | Index fixes: define L (USD value of one index unit), baseline convention, energy source, replace/remove fee and adoption legs, rewrite the circuit breaker, clip bounds | a4, t3 |
| P16 | L1 mechanisms: lazy fee accrual clock, permissionless harvest, paired ENRK+kFIAT mint, surplus routing in the liquidation tx, junior claim accumulator, event-only distribution | a3 (compiled), t4 (executed on testnet-10) |
| P17 | Declared-outputs fix for vault+oracle co-spend | executed locally and on testnet-10 (verified) |
| P18 | Arithmetic discipline for icr_percent (guards, bounded inputs, cross-multiplication) | audit I18, executed overflow bound |
| P19 | Remove the Stability Pool; auction bids payable in ENRK | p5b |
| P20 | Oracle sweep price bounds (price > 0, bounded move per round) | audit I26 |
| P21 | Population/genesis storage sizing rules (fee input sized near covenant values, ~100 outputs per genesis, sweep batch limits) | audit §13.3b (executed) |
