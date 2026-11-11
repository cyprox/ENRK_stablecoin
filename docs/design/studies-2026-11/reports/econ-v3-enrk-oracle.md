# econ-v3: ENRK's own price oracle on Kaspa L1 (ledger P8)

Date 2026-11-11. Research and design-feasibility only. No design decision is taken: the recommendation in section 9 is labelled "proposal for owner decision". Repo /Users/simoes/ENRK_stablecoin was read only. Nothing was broadcast; no network other than public GET was used; no background process left.
SP = /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad. Work files: SP/econ/v3/{price,gate,range,kofn,h,model_cost.py,model_cost.out,web}.
Tags: VERIFIED (source, URL, compile or local engine execution), DERIVED (my arithmetic from verified inputs), UNVERIFIED. "LOCAL-ENGINE" = the real Kaspa txscript engine run by the Argent TxBuilder at build time (as in AUDIT 13 / t4); it does not check node-level rules (finality of lock_time against the live DAA, relay fee, mempool).

## 0. Direction taken and what "ENRK price" means here
Owner direction: ENRK has its own price oracle. Taken as given; this report designs and assesses it.
Unit (open, not decided): the oracle can publish (a) USD per ENRK, or (b) a dimensionless ratio r = market price of ENRK / peg target (index x L). The peg target needs the index and L (P15), and today none of the index inputs exist on L1: contracts/igra/src/oracle_feeds.rs:1-10 documents Band Protocol (energy), Chainlink (adoption), Kaspa RPC (hashrate/fees) feeds, i.e. the Igra/EVM path; the L1 spec has only the KAS price UTXO (L1_NATIVE_REDUCED_SPEC.md section 2; argent/examples/enrk/{a,b}/oracle.ag). [VERIFIED by reading]. Whoever publishes (b) also publishes the index: one trust surface, not two.

## 1. What the ENRK price would be used for, and what manipulation does
Uses stated in the ledger (P6, P7, P15, P10) and the brief; none is implemented today.
| Use | What the price decides | Manipulated DOWN (fake depeg) | Manipulated UP (hide depeg) |
|---|---|---|---|
| U1 breaker (P15 rewrite) | pause/limit mint when ENRK trades far from peg | stops issuance cheaply (griefing), blocks borrowers | breaker never fires while real depeg runs |
| U2 incentive trigger P6 (reserve pays yield on depeg) | activates the reserve payout | drains the reserve to whoever is paid (attacker holds the paid position) | holders get no support when needed |
| U3 rate controller P7 (free vs paid debt) as cross-check | confirms/denies the activity signal | raises the rate on borrowers (cost to them) | rate stays low in a real depeg |
| U4 mint/redeem arbitrage bounds (fee scaling, e.g. cheaper redemption when market < peg) | fee level | cheaper redemption fee: attacker gains the fee difference | dearer redemption fee, slows peg repair |
Not proposed as a use: the ENRK price must not be the collateral valuation of vaults (that stays KAS oracle x index); then a manipulated ENRK price cannot create undercollateralised debt or wrongful liquidations by itself. [DERIVED design constraint].
Damage bound for U2 is the budget the trigger can release per period, so any design needs a hard per-window cap on what the signal can move (see 9).

## 2. Baseline facts (all VERIFIED unless noted)
- KAS oracle today: N sibling UTXOs under one covenant id; `use` recreates unchanged, `sweep` (publisher checkSig) splits 1 to 2; variant B stores price as state (argent/examples/enrk/b/oracle.ag). Vault binds the oracle id through a state field and `observes` (ORACLE-BINDING.md sections 3-6). Executed on testnet-10: N=256 and N=640 rounds, 180-vault liquidation on one price (AUDIT 13.3b). Important: the executed N=384/640 rounds spent siblings through `use` (price unchanged); the only price-changing entry executed on chain is the 1 to 2 `sweep`; an N to N refresh at a new price is NOT executed anywhere (AUDIT 13.3b "Rounds then spent the population through `use` and recreated it").
- Stale-sibling problem: old siblings stay spendable forever unless a refresh provably consumes all of them (SP/reports/econ-a3 section on clocks; AUDIT I-items). A consumer picks the stalest or most favourable sibling.
- Clock: no wall-clock primitive. CLTV against `tx.daa >= x` / `tx.time >= temporal(x)` gives a lower bound; finality makes claimed lock_time <= real (past median time in ms domain, virtual DAA in DAA domain). t4 executed on TN10: lock_time above real was refused ("transaction input #0 is not finalized"); raw OpTxLockTime read with all-MAX sequences accepts any value (so a CLTV entry is required); median time lags wall clock 130-140 s, DAA domain lags much less; the anchor must be in the same domain as lock_time. (econ-t4 section 1.) Measured DAA rate: TN10 about 11.9/s, mainnet about 8.3/s in a 20 s sample (AUDIT 13.3b), so DAA windows are block-count windows, not fixed seconds. Rate-by-rate: UNVERIFIED stability.
- Hot UTXO: 20 back-to-back spends of one UTXO included in 2.09 s; 60 in 9.97 s (6.0 to 9.6 spends/s); conflicting spend refused at once (econ-t4 section 5).
- Fee floor: 100 sompi x max(compute, transient/2) (AUDIT 13.3b). Mass per block: compute 500k / transient 1M / storage 500k. Genesis/sweep batches limited by storage mass (about 87 inputs per sweep tx at 2.1 G sompi; 25 outputs per genesis at 3 KAS; 128 x 10 KAS refused). Fee-paying input must be sized near covenant values (AUDIT 13.3b).
- Markets (r4-market.md, 2026-11-10): KAS 0.02951 USD, 24h volume 6.7M USD; six-venue merged bid depth within 1/2/5% = 6.9M/11.9M/16.2M KAS = 0.2M/0.35M/0.48M USD; selling 11.4M KAS (5% of ADV, 0.34M USD) costs 0.94% average and -1.7% at the last fill; 20M KAS (8.8% of ADV) -5.7%; 36.8M exhausts the book (-32.5%). KAS own max drawdown -87.7%; worst day -24.9%.
- No ENRK market exists on any venue. Kaspa L1 DEX status: argent-playground `ag/dex/dex.ag` (commit 86d5453, 2026-10-23, read this session) is a FIXED-RATE whole-lot swap: line 156-162 `quote_payment.amount * quote_per_base_den == base_reserve.amount * quote_per_base_num`; header comment lines 200-201 "KAS fees, partial fills, change lots, and slippage are outside this demo". No curve, no price discovery. [VERIFIED]. A web search found no live L1 covenant AMM or order book on mainnet (only a testnet AMM mentioned by a news analysis) [SECONDARY]. Igra AMMs exist but are tiny: DefiLlama api.llama.fi/protocol/kasdex (KasDex, Igra) TVL 303 USD at ts 1794373859 (about 2026-11-10); KaspaCom DEX TVL 72,697 USD (chains Kasplex, Igra) [VERIFIED API read, third-party data]. Also L1 ENRK cannot trade in an Igra pool without a bridge, which the L1 path exists to avoid (L1_NATIVE_REDUCED_SPEC.md section 1).
Consequence (DERIVED): at launch there is no market price of ENRK to oracle. Any "market price" published at first is either (i) a number from a venue that does not yet exist, or (ii) a function of the index, i.e. identical to option 4. The market oracle only becomes informative after real depth exists, and the date when that happens is not observable on-chain without trusting someone.

## 3. Compiled and executed artefacts (SP/econ/v3)
1. SP/econ/v3/price/app.ag: ENRK price UTXO. State {publisher, round, price, stamp}. `use` (recreate unchanged, value equal). `update(sig, next_price, left_value)`: checkSig; price and next_price in (0, 1e12]; bounded move by cross multiplication `next*10000 <= price*(10000+B)` and `>= price*(10000-B)`, B=200 bps (TEST value); `tx.daa >= stamp + MIN_GAP_DAA` (MIN_GAP 100, TEST); `now_c = OpTxLockTime()` must be < 5e11 (DAA domain); round+1; stamp'=now_c; 1 to 2 split with value conserved. COMPILED with argent/target/debug/argentc (e76ee07), first attempt.
2. SP/econ/v3/gate/gate.ag (+ price.ag copy): consumer using the declared-outputs pattern (`observes oracle by self.price_covid`, `require oracle.outputs become {...}`). Entries `depeg_trigger` (price*10000 < target*(10000-300)) and `oracle_dead` (`tx.daa >= stamp + MAX_AGE`, MAX_AGE 36000 DAA, placeholder). COMPILED.
3. SP/econ/v3/h (cargo crate depending on SP/w/argent; built with `CARGO_TARGET_DIR=SP/target cargo test --offline`): tests/price.rs, tests/mass.rs, tests/range.rs. Result of tests/price.rs: 3 tests passed, 30 cases, every case as expected (LOCAL-ENGINE).
| Case | Expected | Got |
|---|---|---|
| U1 +1.5%, U2 -1.5%, U3 +2.0000%, U4 -2.0000% at lock = stamp+gap | accept | accept |
| U5 +2.0001% (102,000,001), U6 -2.0001%, U7 +50% | reject | reject (script verification failed) |
| U8 price 0, U9 negative price | reject | reject |
| U10 lock = stamp+gap-1 | reject | reject: "locktime requirement not satisfied -- 1100 > 1099" |
| U11 lock far later (50,000 DAA after) | accept | accept (stamp follows) |
| U12 wrong signer, U13 value not conserved (off by 1 sompi), U19 left_value 0 | reject | reject |
| U14 stored price 0, U15 stored price 1e12+1, U16 PRICE_MAX +1 | reject | reject |
| U17 price 1e12 moving -1% | accept | accept (no int64 overflow at the cap) |
| U18 ms-domain lock_time 1.7e12 | reject | reject: "mismatched locktime types" |
| S1 `use` unchanged | accept | accept |
| S2 `use` with price +1%, S3 stamp changed, S4 value -1 sompi | reject | reject |
| G1 depeg_trigger at price -5% (band 3%) | accept | accept |
| G2 -2%, G3 exactly -3% | reject | reject |
| G4 gate points to a different covenant id than the co-spent price UTXO | reject | reject: "observe `oracle` expects 1 inputs for its covenant id, found 0" |
| G5 oracle_dead with lock = stamp+36000 | accept | accept |
| G6 lock one DAA early (36999) | reject | reject (CLTV) |
| G7 oracle_dead claimed with lock_time 0 (understating age) | reject | reject (CLTV) |
Not covered by these runs (UNVERIFIED): node-level finality (lock_time above the live DAA is refused by the node, shown in t4 for a different contract), relay fee, mempool, and the interaction with the KAS oracle and a vault in the same transaction (3 covenant ids).
4. Mass of N price UTXOs spent via `use` and recreated (tests/mass.rs, MAINNET params, LOCAL-ENGINE + MassCalculator): N=1 compute 1052 / transient 2728; N=64 61,406 / 150,904; N=256 245,342 / 602,488, storage 0 for equal values. Marginal per input (64 to 256): 958 compute, 2,352 transient. N=512 refused (transient 1,204,600 > 1,000,000), N=532 refused (compute 509,750 > 500,000), N=640 refused (compute 613,214). DERIVED ceiling about 425 (transient 1e6/2352) for this actor, versus 532 (variant B) and 642 (variant A) recorded for the KAS oracle in AUDIT/REMEASUREMENT; the difference is script size (the `update` entry and the extra state field are in every redeem script). A leaner price actor (e.g. `update` in a separate covenant) is not tested.
5. SP/econ/v3/kofn/app.ag: 2-of-3 quorum using two `sig` parameters and two key indices (no ternary and no early return exist in Argent; `checkMultiSig([..],[..])` array literals are rejected by the parser). COMPILED. Not run in the engine. Malformed 65-byte signatures raise an error rather than false (r2-languages), so the quorum must pass real signatures from distinct keys, which this form does.
6. SP/econ/v3/range/app.ag: counted-range N to N refresh `consumes { olds: Px[1..=8] } emits { news: Px[1..=8] }` with per-sibling bounded move and `require(olds.length == n)` where `n` is the population size in state (so a refresh must consume the whole population, closing the stale-sibling hole if the count is conserved). COMPILED on the repo's pinned argentc (e76ee07) after two compiler complaints (state array needed; `news[i].value` must be referenced). tests/range.rs (R1-R7) FAILED at the first case: "entry `Px::refresh` expects 2 arguments, got 0": the harness submitted the other population inputs as plain `refresh` calls. The consumed inputs of a same-actor `consumes` range need a different input form which I did not find in the builder API in the time available. So the engine behaviour of a range refresh is UNVERIFIED. Two risks recorded (DERIVED): (i) ORACLE-BINDING.md section 7: a leader entry requires |I(c)|=1 per covenant id; a same-id range consumed by a leader probably cannot be the same covenant as the one whose siblings are consumed by `use` ladders; (ii) the compiler caps a range at 512 inputs (docs/entry-clause-ranges.md, "0 <= minimum <= maximum <= 512" in the newer clone SP/src_argent/a), and the mass ceiling above is about 425. This is the P5A stale-sibling question again, not solved here.

## 4. Staleness without a clock: what is and is not enforceable (DERIVED, supported by G5-G7 and t4)
Consensus bounds a claimed lock_time from above by real time and CLTV bounds it from below by an anchor. A script therefore can prove "at least T has elapsed" and can never prove "at most T has elapsed".
- Staleness (age >= MAX_AGE) is provable by anyone who wants to prove it: they claim the highest lock_time they can (honest-high). Entries that benefit from staleness (permissionless "oracle is dead" fallback) are enforceable: G5-G7.
- Freshness (age <= MAX_AGE) is not enforceable against a spender who wants to use an old price: he claims a low lock_time (>= stamp). Gates that must require freshness cannot be built from time. They can only be built from structure: the old price UTXO must no longer exist (all-N refresh), or the consumer must itself carry a recent anchor.
- A per-UTXO "dead" flag is useless: other siblings stay alive. The check must be recomputed by each consumer from `stamp`. And an attacker can present an OLD sibling (stamp from round R-5) to a fallback entry and claim the oracle is dead while it is alive; this is exactly the stale-sibling hole, and it is why the all-N refresh (or a much shorter lived population) is a prerequisite for any "dead oracle" fallback to be safe.
- Maximum drift per time is enforceable from below only: `tx.daa >= stamp + MIN_GAP` forces updates of one lineage to be at least MIN_GAP DAA apart, so the price can move at most B per MIN_GAP: with B=0.5% and MIN_GAP=600 DAA (about 50-70 s at 8.3-11.9 DAA/s) a compromised publisher needs about 71 steps (ln(0.7)/ln(0.995)) x about 60 s = about 71 minutes to move the published price by -30% (DERIVED; the constants are test values). But parallel lineages: each split sibling is its own lineage, so a publisher could advance two lineages with different prices; consumers choosing the more favourable sibling widen the effective spread by the number of unrefreshed rounds. Again needs all-N refresh.

## 5. The options
Common to all: a consumer needs one extra co-spent input (+958 compute / +2,352 transient measured above) once per transaction, not per vault: 180-vault liquidation = 866,620 transient (AUDIT 13.3b), so adding one price input to a vault operation leaves about 197 vaults per tx instead of about 200 (DERIVED). Contention: one price UTXO served 180 vaults of two covenant ids on chain.

### Option 1: publisher-signed ENRK price (like the KAS oracle)
Forms: 1a single key; 1b k-of-n (2-of-3 compiled, section 3.5); 1c rotating keys.
- Manipulation cost: equals the cost of corrupting the key(s) (1a one party; 1b k parties), plus nothing market-based; the on-chain bound limits the speed (section 4). A rational honest publisher computing from a market is itself exposed to the market-depth costs in option 2.
- Latency: update is an ordinary transaction. Measured on TN10: tx accepted and included in 7-8 s typically (7-67 s observed, econ-t4), first inclusion 0.76 s in the hot test. So price age is dominated by publisher polling plus about 8 s confirmation, not by the 100 ms block time. Practical floor about 10 s; MIN_GAP bounds it from below as design choice.
- Trust in an immutable system: a perpetual key (or keys) with no governance. If the publisher vanishes: the last price is spendable forever through `use`; staleness is provable (section 4); a fallback must be written into the consumers in advance (section 9). 1c rotation without governance can only be a pre-committed key chain (state holds a hash of the next key; the update reveals it): not compiled here (hash builtins not tried), UNVERIFIED. Succession is decided by the first key holder, so rotation does not remove the trust, it moves it to the key-chain creator.
- Failure modes: stale (provable, fallback), absent (same), manipulated (bounded rate; sustained over a window an attacker with the key reaches any level; k-of-n raises the cost of collusion only if keys are held by independent operators, which nothing in the contract can verify).
- Binding: `observes` + declared outputs, as for the KAS oracle (G1-G7 compile and run); covenant id in the consumer's state (Q1c); consumers created by `spawns` carry it (ORACLE-BINDING.md section 3). Expressible: YES (section 3).
- Mass/cost: see section 6. Publisher cost is paid by someone: nothing in an immutable system pays it unless fees are routed (the fee mechanisms of P16: harvest tips). UNVERIFIED who funds it.

### Option 2: TWAP of an on-chain covenant AMM or order book
- Exists? No L1 venue with price discovery exists (section 2: dex.ag is fixed-rate). One could be built: a pool UTXO with reserves in state and a swap entry checking x*y >= k, a TWAP accumulator (cumulative price x claimed time) in state, read through `observes`. Not compiled or run here. It would be a hot UTXO: serial, 6-9.6 swaps/s on TN10. That is a feasibility estimate for the whole pool, not per user.
- Manipulation cost versus depth (DERIVED, constant product, fee 0.3%, SP/econ/v3/model_cost.out). L = quote-side reserve in USD, x = displacement:
| L | x=5% capital in | round trip fee | cost per arbitrage restore (L x^2/4) | x=20% capital in |
|---|---|---|---|---|
| 10k | 247 | 1.5 | 6 | 954 |
| 100k | 2,470 | 14.8 | 62 | 9,545 |
| 500k | 12,348 | 74 | 312 | 47,723 |
| 2M | 49,390 | 296 | 1,250 | 190,890 |
 A sole-venue pool (no outside arbitrage) is moved for the price of the round trip fee: 15 USD for a 5% displacement of a 100k pool, plus the capital held for the window. A TWAP window multiplies capital lock-up cost, not the fee; with arbitrage present the cost per restore cycle is L x^2/4 per sample. The only depth data for the same asset family is KAS: the merged 6-venue book within 5% is 0.48M USD; so even KAS would be "L = 500k" in this table; an ENRK pool starts below that (DefiLlama: KasDex Igra TVL 303 USD, the largest Kaspa DEX there 73k USD).
- TWAP weighting uses elapsed time from claimed lock_time: the swapper that follows a manipulated price chooses the highest allowed lock_time and gives it the maximum weight (DERIVED from section 4), a feature Uniswap-style block timestamps do not have.
- Latency: every swap can update the accumulator; no publisher. Cadence limited by pool UTXO serialisation.
- Trust: none beyond code, at the price of manipulability. If liquidity vanishes: price freezes or moves with the last trade; staleness provable only with the all-N or single-UTXO pool structure (a single pool UTXO has no sibling problem, but all consumers contend on it unless read through a replicated copy, which reintroduces siblings).
- Binding: the pool read through `observes`; pool and ENRK issuer in one lineage via `spawns`. Expressible: probably yes (declared outputs), UNVERIFIED.
- Verdict: cannot be the first oracle (no venue, no depth); possible later as one input of option 5.

### Option 3: price derived from protocol activity
Candidate signals: redemption volume per window, mint/redeem fee levels, Monolith-style free-vs-paid debt ratio (docs/design/MONOLITH-COMPARISON-2026-11-10.md lines 29-31: "The ratio of free debt is the only input of the rate controller ... No market price feed is used for the peg"; lines 52-53: rate controller has no price input and no maximum rate).
- What it measures: borrower behaviour, not a price. It gives a direction (peg pressure), not a level, and it is slow (borrowers switch modes rarely). It cannot say "ENRK trades at 0.94".
- Manipulation cost: moving the free-debt ratio requires opening/closing debt of the size of the ratio shift: cost is interest/fee on the position and capital locked; for a small system a whale shifts the ratio. Depth analogue: the system itself is about 100M KAS in the model (2.95M USD, r4 section 7), about 44% of ADV.
- Latency: slow (days) by nature.
- Trust: none (pure covenant state). Failure: absent = no signal, frozen ratio. Binding: aggregate ratio lives in shared state, the same contention and Q1c issue the Monolith document flags (lines 193-195). Expressible: needs a shared aggregate; by the audited pattern it would have to be a replicated/sharded counter UTXO (like the supply/issuer shards, econ-t4 caveat "K shards"). Not tested.
- Verdict: useful as an independent cross-check, not as a price.

### Option 4: index-only (no market price) with market-based safeguards
- The peg is to the index (L1 spec); redemption at index value works with no ENRK market price (Liquity v1/v2 and Monolith redeem at face value; section 7). The market enters only through arbitrageurs: they redeem when market < face (Liquity v2 README: "redemptions ... only profitable when BOLD < $1", docs.liquity.org/v2-faq/redemptions-and-delegation).
- Market-based safeguards without an ENRK oracle: redemption itself (needs implemented redemption, P9, unimplemented today), fee floors, caps on issuance by family (P11).
- Manipulation cost: no market price to manipulate, so none; the index is still published by someone (P15) and is the single trust surface.
- Failure: if the index publisher vanishes, peg target is frozen: same dead-oracle problem as the KAS price.
- Verdict: the baseline every other option must beat; all comparables except RAI and crvUSD use it (section 7).

### Option 5: hybrids (proposals)
5a Two-signal AND: P6/P7 triggers need (published ENRK price below target by band) AND (activity signal agrees: redemption volume above X or free ratio moves). An attacker must pay for both; cost add up, damage bounded by the AND and the cap.
5b Publisher quorum plus on-chain medians: k-of-n publishers each post; consumer reads one UTXO that stores the median of the last posts (the median is computed in the update entry from signed inputs of several lineages). Not compiled.
5c Bounded-move price plus automatic degradation: on provable staleness the consumers drop to option 4 (index-only), which exists with no input from the dead oracle (section 9).
5d Same UTXO family as the KAS oracle: add `enrk_price` (or r) to the KAS oracle state: one co-spent input instead of two, saves 958 compute / 2,352 transient per transaction and one population to refresh, at the cost of one key and one cadence for both (couples the collateral price to a weaker signal: if the ENRK price source fails, the KAS price stops with it unless the entries are separate). Compile not tested.

## 6. Mass, contention and cost (measured constants, DERIVED outputs)
| Item | Value | Source |
|---|---|---|
| `use` per input | 958 compute, 2,352 transient (ENRK price actor) | tests/mass.rs |
| N ceiling for this actor | about 425 (transient-bound) | derived from mass.rs |
| KAS oracle ceilings | A 642 / B 532 | AUDIT, L1 spec 2.5 |
| 1 to 2 `update` tx | about 2.4-2.7k mass (KAS oracle `use` measured 2,416 on TN10) | econ-t4 section 5 |
| Fee floor | 100 sompi x max(compute, transient/2) | AUDIT 13.3b |
| Floor fee per round N=64 / 256 / 425 | 0.076 / 0.30 / 0.50 KAS (0.0022 / 0.0089 / 0.0148 USD at 0.02951) | model_cost.out |
| Publisher cost, one round per 10 s, N=64 / 256 / 425 | 652 / 2,603 / 4,321 KAS per day (19 / 77 / 128 USD per day) | model_cost.out |
| Population growth | sweep/update 1 to 2, about 87 inputs per tx at 2.1 G sompi; storage-mass bound; values must be uniform for cheap rounds | AUDIT 13.3b |
| Genesis | storage 4e12/value per covenant output: N=128 at 10 KAS refused; 25 per genesis at 3 KAS | econ-t4 section 3, AUDIT |
The price-changing N to N refresh is not measured on chain. The cost per day above assumes a refresh transaction of the same mass as the `use` round. Whether an immutable system can fund 20-130 USD per day is open (compare the harvest tip mechanism in econ-t4 section 2 and P16).

## 7. How comparable systems price their own stablecoin or avoid it (primary sources read this session)
| System | Own-coin market price used? | Evidence |
|---|---|---|
| RAI / Reflexer | YES, the controller input. Proportional term = redemptionPrice - marketPrice; integral with leak; period `integralPeriodSize`; noise barrier | github.com/reflexer-labs/geb-rrfm-calculators src/calculator/PIRawPerSecondCalculator.sol lines 76-84, 288-292, 340-352 (`proportionalTerm = subtract(int(redemptionPrice), multiply(int(marketPrice), int(10**9)))`, `require(subtract(now, lastUpdateTime) >= integralPeriodSize ...)`) [VERIFIED]. Market price feed: docs.reflexer.finance/system-contracts/oracle-module.md lists governance-led whitelist medianizer, Chainlink medianizer, and a Uniswap v2 TWAP medianizer; warns governance could set a huge window `maxWindowSize` [VERIFIED]; later move to a TWAP of the Chainlink RAI/USD feed and a Uniswap v3 converter proposal [SECONDARY, medium.com/reflexer-labs, community.reflexer.finance, 2021 era]. RAI relies on pre-existing deep ETH markets and governance-set rate bounds in OracleRelayer [SECONDARY]. |
| Maker (DAI) | Collateral prices only, through the OSM: 1 hour delay (`hop = ONE_HOUR`), whitelisted readers (`bud`, "OSM/contract-not-whitelisted") | github.com/makerdao/osm src/osm.sol lines 73-74, 88, 113-131 [VERIFIED]. That Maker reads no DAI market price in its core is from my knowledge: UNVERIFIED here (the PSM was not fetched). |
| Liquity v1 | No market price of LUSD: redemption at face; I did not fetch v1 sources: UNVERIFIED. |
| Liquity v2 (BOLD) | No: "swaps 1 BOLD for $1 worth of collateral ... in order to maintain a hard BOLD price floor"; only collateral oracles (Chainlink, min/max asymmetric pricing: min(market, exchange rate) for minting, max for redemptions, with 1-2% bands); branch shutdown on oracle failure; user-set interest rates order the redemption queue | github.com/liquity/bold README.md lines 141, 151, 163, 754, 1243-1273; docs.liquity.org/v2-faq/redemptions-and-delegation [VERIFIED] |
| Frax v1 | YES: `frax_price()` from `UniswapPairOracle fraxEthOracle` x Chainlink ETH/USD; `refreshCollateralRatio()` moves the collateral ratio by `frax_step` when price is outside `price_band` with a cooldown; setters `onlyByOwnerGovernanceOrController` | github.com/FraxFinance/frax-solidity src/hardhat/contracts/Frax/Frax.sol lines 32-44, 133-152, 197-218, 305-348 [VERIFIED]. frxUSD (v3) design not verified (search only gave press): UNVERIFIED. |
| Monolith | NO: free-debt ratio drives the rate; no price input and no maximum rate | docs/design/MONOLITH-COMPARISON-2026-11-10.md lines 29-31, 52-53 (owner's document, read only; not re-verified against Monolith sources here) |
| Curve crvUSD | YES, smoothed and filtered: AggMonetaryPolicy4 `rate = rate0 * exp((1e18 - p)/sigma - debt_ratio_ema/target) + extra`, capped at MAX_RATE = 43959106799 per second ("300% APY"), sigma bounded 1e14..1e18; price p from `PRICE_ORACLE.price()`; the aggregator only counts pools with `MIN_LIQUIDITY = 100_000e18` and takes each pool's `price_oracle()` (an EMA); PegKeeper acts on pool imbalance and requires "peg unprofitable" not to occur | github.com/curvefi/curve-stablecoin curve_stablecoin/mpolicies/AggMonetaryPolicy4.vy lines 60-67, 88-92, 300-340; price_oracles/AggregateStablePrice.vy lines 3, 39, 155-156; stabilizer/PegKeeper.vy lines 248-306 [VERIFIED] |
Pattern (DERIVED): systems that read their own price (RAI, Frax v1, crvUSD) do so on deep multi-venue markets that exist before the coin, with smoothing (TWAP/EMA), liquidity filters, and bounds (noise barrier, price band, MAX_RATE). Systems launched without a market for their coin (Liquity, Maker core, Monolith) avoid it. ENRK on L1 has neither the market nor a smoothing source yet.

## 8. Failure modes with automatic fallbacks (what is expressible)
| Event | Detection on L1 | Fallback that needs no human | Expressible? |
|---|---|---|---|
| Publisher stops | provable staleness: `tx.daa >= stamp + MAX_AGE` (G5-G7) | consumers switch to index-only rules (option 4); P6/P7 triggers stop being payable | Compiled and run for the check; the switch needs every consumer entry to branch on it (design work). Safe only with all-N refresh (section 4) |
| Publisher posts garbage | bound check (U5-U9) and price>0 (U8, U9) | none needed within B per gap; larger real moves are delayed (the price lags a real crash by design) | Run |
| Publisher compromised, steady bias | bound limits speed; AND with activity signal (5a) | trigger needs second signal; budget cap | AND not built |
| Pool manipulated (option 2) | none on-chain without a second source | median of venues (5b), liquidity floor | not built |
| Price lags a real crash (bound too tight) | n/a | the triggers are late by about |ln(1-d)/B| gaps: for d=30%, B=2%: 18 updates | choose B and gap together; open |
| Both signals absent | n/a | index-only | yes |
Lag versus 100 ms blocks (DERIVED): block time is not the limit. Time to publish = observation delay + confirmation (7-8 s typical, up to 67 s seen on a lightly loaded TN10) + MIN_GAP. The sweep/round cadence for a population N is "N x block time" for a max-size round (about one block at N=425-640, L1 spec 2.5). In a -25% day (r4), a 2%-per-minute bound reaches -25% in about 14 minutes of publishing.

## 9. Proposal for owner decision (not a decision)
Staged, so that nothing depends on a market that does not exist yet:
1. Define the signal as r = market price of ENRK / peg target (dimensionless, 1e8 scale), because the consumers only need the deviation; the unit decision belongs to P15.
2. Phase 0 (launch): the ENRK price UTXO family is deployed with the declared-outputs pattern, but the consumers treat it as informational and rely on option 4 (index-only) plus the activity signal of option 3. Reason: no ENRK venue exists (section 2), so any published price would be the publisher's opinion.
3. Phase 1 (once at least two independent venues exist, off-chain or on-chain): a k-of-n publisher quorum (2-of-3 compiled) posts r as a median of TWAPs with a volume/depth floor stated in the publisher procedure; on-chain rules: price>0, cap, bounded move per MIN_GAP, round counter, stamp (price/app.ag).
4. Triggers (U1-U4) require AND of price signal and activity signal (5a), and each trigger releases at most a fixed budget per window (cap decided by the owner). The collateral valuation never uses r.
5. Dead-oracle rule: if stamp is older than MAX_AGE, consumers fall back to option 4. Prerequisite: an all-N refresh so old siblings do not exist (range form compiled, not proven; section 3.6) or, alternatively, a small population (N <= 64) refreshed per round by a batch that is cheap enough to be fully replaced each time.
6. Open for the owner: B and MIN_GAP, MAX_AGE, k and n and who holds the keys, who pays the publisher (20-130 USD/day at one round per 10 s, section 6), whether r shares the KAS oracle UTXO (5d).
What could go wrong even then: a quorum that is not independent; a thin venue feeding the median (cost table section 5); price lag during a real crash because of the bound; permanent loss of the quorum with a stale-sibling attack on the fallback.

## 10. Testnet-10 test plan (NOT executed)
All on TN10, owner-authorised network only, throwaway key, caps as in t4 (net spend <= 300 TKAS).
T1 Genesis and 1 to 2 `update` of price/app.ag (N=2 to 16): chain mass vs local (958/2352 per `use`), fee floor accepted at 100 sompi x mass; negative txs rejected by the node: +2.0001%, price 0, ms-domain lock_time, lock = stamp+gap-1.
T2 Clock behaviour on the node: stamp lag versus virtual DAA over 1 hour; refusal of lock_time above the live DAA (not finalised); MIN_GAP enforcement from two publishers racing on one lineage (conflict refused as in t4 section 5).
T3 Population growth to N = 64, 256, 425 by `update` batches (87 inputs at 2.1 G sompi); fee-paying input sized near covenant values; `use` round on chain at 256 and 425: record API mass, transient, confirmation time.
T4 N to N refresh: find the accepted input form for a consumed range (the tests/range.rs failure), run R1-R7 locally, then on chain; then the stale-sibling attack: after a refresh, try `use` and `oracle_dead` on an old sibling: must fail because it is spent.
T5 Three-covenant co-spend: vault (KAS oracle) + Gate (ENRK price) in one tx, declared outputs for both oracles; 180 vaults + 2 price inputs; record transient (expected about 870k to 880k).
T6 `depeg_trigger` / `oracle_dead` with the real node: exact boundary, and understated lock_time attempt.
T7 Publisher vanish drill: stop updates, measure real time in DAA for MAX_AGE (DAA/s on TN10 differs from mainnet 8.3/s sample), then fire `oracle_dead`.
T8 Hot UTXO with two price families under 60 back-to-back spends as in t4 section 5.
T9 2-of-3 quorum engine run and on chain (wrong key set, duplicate index, malformed signature).
T10 Off-chain replay (no chain): feed KuCoin KAS candles and a synthetic ENRK/peg series (r4 raw data) through the bound B and MIN_GAP: detection delay for 5/10/30% depeg, false-trigger rate at a 3% band, manipulation duration needed.
T11 Optional, only if the owner wants option 2: a constant-product pool with TWAP accumulator on TN10, attack scripts at depths 10k/100k/500k to compare with the table in section 5.
Pass criteria to be set by the owner before running (not invented here).

## 11. Limits and unverified points
- Engine runs are LOCAL-ENGINE only; the node adds finality, relay and mempool rules. Constants B, MIN_GAP, MAX_AGE, PRICE_MAX are test values, not proposals.
- N to N refresh with a counted range compiled but did not run (harness input form unknown); all claims about closing the stale-sibling hole through `n` are DERIVED.
- Option 2 and the quorum median (5b) were not built. The key-chain rotation was not compiled.
- Cost table uses a textbook constant-product model with fee 0.3%; real pool design and tick structure unknown; no ENRK data exists. KAS depth is a single calm snapshot (r4 section 8).
- Third-party data: DefiLlama TVL (two DEXs on Igra/Kasplex), search-result summaries for RAI oracle history and Kaspa DEX status are SECONDARY. Maker DAI price handling, Liquity v1 and Frax v3 were not verified from primary sources.
- DAA-per-second figures are from 20 s samples (AUDIT 13.3b), so any "seconds" conversion is approximate.
- KaspaDollar (competitor with a claimed PoW miner oracle, r3) could not be verified: web search returned only a press article without design details.
