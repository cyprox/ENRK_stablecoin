# ENRK compared with Kaspa Dollar, Monolith and Frax

**Date:** 2026-11-15. **Status:** read-only study. No design decision is taken here: every "idea" is a proposal awaiting owner validation.

**Sources and their limits**
- KSD: [`kaspadollar/KASPADOLLAR-REVIEW-2026-11-15.md`](kaspadollar/KASPADOLLAR-REVIEW-2026-11-15.md) and its `evidence/` folder (pre-launch, published text only, no code exists).
- Monolith: [`MONOLITH-COMPARISON-2026-11-10.md`](MONOLITH-COMPARISON-2026-11-10.md) (copy; code read and tests run by the earlier study).
- Frax: [`FRAX-COMPARISON-2026-11-11.md`](FRAX-COMPARISON-2026-11-11.md) (copy; market data and code of 2026-11-11).
- ENRK: `docs/design/FROZEN_PARAMETERS.md` (3 Sep 2026), `PROJECT-STATE.md` (13 Nov 2026), `docs/design/L1_NATIVE_REDUCED_SPEC.md`, `studies-2026-11/reports/econ-v3-enrk-oracle.md`, and the owner decisions recorded in the project memory (recurring stability fee yes, fees never burned, layer = Kaspa L1, own price oracle). `FROZEN_PARAMETERS.md` predates some later decisions; where they differ the later owner decision applies and the frozen value is marked "(frozen doc)". Peg-index fate, loss-absorption structure and debt ceiling are **still undecided** by the owner.

Important asymmetry: ENRK and KSD are both designs and measurements, not live products. Monolith is deployed; Frax is deployed (frxUSD supply about 91-94 M, down about 10.5% in 30 days per the Frax study, 2026-11-11). Evidence quality differs accordingly (KSD: text only; ENRK: specs, simulations and testnet-10 runs; Monolith: code, audits, tests; Frax: market data, audits, code).

---

## 1. Side by side

| Topic | ENRK | Kaspa Dollar (KSD) | Monolith | Frax (frxUSD) |
|---|---|---|---|---|
| Status | Design and specification; implementation not started | Pre-launch; fundraiser; no code, no testnet, no audit | Deployed on Ethereum, audited (several reports) | Deployed, multi-chain |
| Execution layer | Kaspa L1 covenants (owner, 2026-11-13) | Kaspa L1 covenants (KIP-16/17/20/21, KCC-20) | EVM | EVM, about 23-26 chains (the Frax study notes the sources disagree) |
| Backing | Over-collateralised KAS vaults | Over-collateralised KAS vaults (KAS only) | Single collateral per instance | Custodial RWA / fiat-equivalent reserves |
| Peg target | Index peg (formula frozen: 40% hashrate, 30% energy, 20% fees, 10% adoption, clipped to [0.1, 5.0]; fate of the index undecided) | $1 | Rate controller on free-debt ratio, no price input | $1 via redemption against reserves |
| Min ratio at mint / liquidation | ICR 200% / MCR 150% (frozen doc) | 250% / 200% | Collateral factor ≤ 85% LTV | n/a for frxUSD; Fraxlend separate |
| Liquidation | Dutch auction, 120 min, floor 75%, fee 4% (frozen doc); 180 vaults liquidated in one transaction on one price (testnet-10) | Partial liquidation back to exactly 200% by anyone, penalty 5%; no auction | Fixed incentive 0-10%, 25% close factor, no auction | Fraxlend: no close factor, fee 10% clean / 9% dirty |
| Redemption | Specified, not implemented; ENRK tranche only; lowest ICR first; fee 1% (frozen doc) | Any vault chosen by the redeemer; $1 of KAS at the liquidation price ℓ; oracle fee 0.1% | One targeted borrower; free-debt only | Against reserves, issuer-controlled |
| Fees | Mint 2%, liquidation 4%, redemption 1% (frozen doc); recurring stability fee decided YES; fees never burned | Oracle fee 0.1% (floor 1 KAS) on priced actions; no stability fee stated | Variable interest on paid debt; 0% free debt | Mint/redeem fees set by the owner role (code); no fee data collected by the Frax study |
| Loss beyond collateral | Waterfall with seniority (ENRK redeemable tranche vs kFIAT); structure still undecided | Not socialised, not minted: KSD holders bear it | Pro-rata to all borrowers, no buffer | Fraxlend: lenders; stablecoin: case-by-case DAO |
| Price oracle | Own oracle: price UTXOs under one covenant id, `sweep` authorised by a **publisher signature** (checkSig); measured on testnet-10 (rounds of N=256 and 640); max N≈46 per refresh transaction in one design | Median of **miner votes** in the coinbase payload, ZK-proved via KIP-21/OpZkPrecompile; stale >30 min halts priced actions | Price feed fixed per instance (no setter); stale path decays price to 0 over 24 h while liquidations stay enabled | Not a collateral-price design |
| Governance / admin | None after launch; parameters frozen at compile time | No upgrade or pause described; whitepaper updated in place; "deployer" and "publisher/membership" roles unexplained | No proxy; operator powers bounded and expire (≤1460 days) | Proxy; 4-of-7 Safe + 24 h timelock (frxUSD); owner can freeze, pause, burn, recover |
| Issuance control | Cap design undecided (the Argent issuance-cap example was found bypassable in an earlier study) | Net issuance ≤ 50,000 KSD in any 24 h (burst bound; sustained 25,000/day) via 8 budgeted minting UTXOs (Theorem 1, arithmetic checked) | No issuance cap found in the Monolith study (borrowing limited by collateral factor and reduce-only mode) | Issuer |
| Evidence available | Specs, simulations (W1/W2), testnet-10 transactions, independent review of the W1/x1b/W2 reports (38 findings, none high) | Site text; maths recomputed; no code | Code, 163 of 164 tests pass (1 documented test artefact), 4 audit PDFs (2 marked DRAFT) | Market data, audits, code |

## 2. Where KSD and ENRK are close or opposed

1. **Same chain, same collateral, same scarce resource.** Both lend against KAS on Kaspa L1 covenants. The earlier market study measured KAS depth (selling 5% of average daily volume costs 0.94% on average, -1.7% at the last fill; 8.8% costs 2.33% on average, -5.7% at the last fill; the book is exhausted at 36.8 M KAS; source `r4-market.md`, 2026-11-10) and ENRK's own work found that debt must stay small against KAS liquidity. Two stablecoins competing for the same KAS liquidity and liquidators is a shared risk, not only a competition. Not quantified here.
2. **Oracle trust is the sharpest difference.**
   - ENRK's KAS collateral oracle (variants A/B) updates through a `sweep` authorised by a publisher signature: trust in the key holder. As written it has **no bound on a single-round price move** (variant A accepts a price of 0; PROJECT-STATE items 1e and audit I26). Bounded moves exist only in test prototypes: 10% in the x1b population-refresh test, and 200 bps with a `oracle_dead` age of 36,000 DAA in the separate **ENRK-price** prototype of `econ-v3` (placeholders, a different oracle from the collateral one). The stale-sibling problem is mitigated by a population-completeness guard in the form tested on testnet-10 (max N = 46 is a property of that contract form), not by decentralising the feeder.
   - KSD removes the feeder by letting miners vote, at the price of three dependencies: sustained participation (only 50% is enforced after launch), pool operators (not hashers) writing the votes, and an unenforced assumption that voters read independent markets. Concentration today is high: the whitepaper gives 32.7% and 57.1% (29 Oct, source not re-fetched); a 3.7-minute sample of 2,223 blocks by pool tag gave about 30.7% and 52.2% (15 Nov). These are not two independent counts; the top-two figure is not confirmed exactly.
   - KSD's own pages are inconsistent about whether a permissioned "publisher" set exists. If it does, KSD's oracle converges towards ENRK's.
3. **Peg definition.** KSD pegs to $1 with an arbitrage argument whose redemption leg weakens in a fall (redeemers get x/ℓ with ℓ ≥ median). ENRK's index peg is a different bet: it is not comparable to a $1 peg, and the ENRK studies found that index behaviour (falling with KAS in the original simulator, a hidden 46% cushion) dominates crash safety. KSD has no index risk but carries the full KAS drawdown on a 200% line.
4. **Liquidation mechanics.** KSD relies on any liquidator, partial back to exactly 200%, a 5% penalty and an oracle that can only move 25%/h downward; the whitepaper itself computes a window of 36 min after −20% and about 1.6 h after −40% where liquidation is not profitable (134 min after −50% is this study's recomputation). ENRK's frozen model uses a Dutch auction and a 75% floor. ENRK's earlier measurements showed that a floor too high freezes liquidation in deep falls; KSD's equivalent is the rate-limited ℓ.
5. **No admin keys.** ENRK freezes parameters at compile time. KSD is described as having no admin key by a third-party article (SECOND-HAND, cryptonews.net 2026-11-09); the site pages read do not state it and describe no upgrade or pause mechanism, while the whitepaper is "updated in place", the deployer role is undefined and the permissioned-publisher text is unexplained. These claims cannot be compared until KSD publishes code.
6. **Loss rule.** KSD is explicit: no socialisation, no minting; holders bear unbacked debt. ENRK's loss structure is an open owner decision.
7. **Maturity.** KSD's external audit is planned for June-August after a January-April build (no code yet); ENRK has already measured oracle and liquidation behaviour on testnet-10, had its W1/x1b/W2 simulation reports independently reviewed (38 findings, none high) and has an internal audit (`AUDIT-2026-11-09`). Neither has an external audit.

## 3. Ideas for ENRK — proposals only, none validated

Each needs a Kaspa covenant feasibility check and an owner decision before anything else.

1. **Miner-vote oracle as an input for ENRK's own-oracle question.** It is the only miner-vote alternative found in this study (other non-single-key forms are listed in `econ-v3`; that no other exists is UNVERIFIED). Its security terms are in KSD finding C-D. Before it could be considered: obtain KSD's proof mass and proving latency (UNVERIFIED today), and measure real vote participation if any miner votes exist.
2. **Asymmetric rate limits** on the price seen by minting and by liquidation (KSD: mint price rises ≤10%/h, liquidation price falls ≤25%/h). ENRK's v3 oracle already bounds a single move (200 bps test value); the asymmetric split by use is new and testable in the existing simulator.
3. **Settlement after prolonged oracle silence** (KSD: 30 days, redemption at the last price). ENRK has a stale-oracle rule in the prototype (`oracle_dead`, placeholder 36,000 DAA) but no end-state; compare.
4. **Budgeted minting UTXOs.** KSD's 8-UTXO refill design (Theorem 1) may be of the same family as the Argent issuance-cap example found bypassable earlier (not compared); read its argument against that finding before reusing either. Note that 8 x 3,125 = 25,000: the 50,000 figure is a burst bound (each UTXO can hold up to 2B), the sustained rate is 25,000/day.
5. **Partial liquidation to a target ratio** as a comparison point for ENRK's auction, using the W2 simulator with KSD's parameters (250%/200%/5%, 25%/h limit) as one more configuration.
6. **Shared-liquidity stress case.** Add a second KAS-collateralised stablecoin with an overlapping liquidator pool as a scenario in the crash simulator.

Not proposed: contacting KaspaDollar or the Kaspa core developers (outward action, needs the owner's separate go).

## 4. Limits of this comparison

- KSD figures come from the site and from recomputation; nothing is observed in operation.
- ENRK values marked "(frozen doc)" may be superseded; the open decisions are listed in `PROJECT-STATE.md`.
- No simulation was run for this comparison; section 3 items are untested suggestions.
- Monolith and Frax columns repeat the earlier studies and were not re-verified on 2026-11-15; their dates (2026-11-10/11) apply.
