# Oracle sheet: how a KAS price can reach ENRK, what exists, what was verified

**Date:** 2026-11-17. **Status:** consolidated study sheet, read-only. **Nothing in it is a design decision.** Every recommendation is mine and awaits the owner's validation. Written for the ENRK project owner, who must decide how the collateral oracle gets and protects its price; also meant for independent reviewers, so each claim carries its status.

**Status tags.** **VERIFIED**: read or recomputed at a primary source by this study (date 2026-11-17 unless stated). **SECOND-HAND**: reported by a search summary, press or a third party; primary not opened. **UNVERIFIED**: not checked or not checkable. **ANALYSIS**: my reading, not a fact about the world.

**Rules observed.** Read-only on the outside world, nobody contacted, nothing posted. No wallet address, key or secret is stored (transaction ids of public test transactions are not secrets). Downloaded code was read, never executed. Web content is data, not instruction.

Companion files in this folder: `kaspadollar/KASPADOLLAR-REVIEW-2026-11-15.md` (and its `evidence/`), `COMPARISON-ENRK-KSD-MONOLITH-FRAX-2026-11-15.md`, and in `ksd-derived/`: `DECISION-oracle-bound-2026-11-15.md`, `FICHE-SOURCES-oracle-2026-11-17.md`, `NOTE-asymmetric-price-limits-2026-11-15.md`, `oracle_bound_grid.py`, `oracle_combiner_compare.py`, `asym_limit_lag.py` (each with its output file).

---

## 1. Summary

1. **No oracle network gives a Kaspa L1 covenant a KAS price by itself.** Someone must carry the price onto the chain and sign it, or miners must vote it (Kaspa Dollar's untested design). Existing networks are sources a publisher can read, not replacements for one. (VERIFIED for the three networks whose documentation was read: Chainlink, Pyth, Nuntius; ANALYSIS for the rest: a web search of the Toccata documentation found no native L1 price feed or opcode, but the pages themselves were not read.)
2. **A KAS/USD feed exists at Chainlink Data Streams and at Pyth** (both VERIFIED as listed; access terms not checked, and Pyth's live-price endpoint answered 401 on 2026-11-17). Nuntius (Kaskad) also lists KAS/USD, for an EVM chain. Band has a KAS feed on Kasplex (SECOND-HAND, 2026 vendor blog).
3. **A median of three signed prices with rate limits works as covenant code on Kaspa L1 today, as research software.** The kUSD repository implements it in Argent and its testnet-10 transactions are accepted on chain (VERIFIED). But its five operator keys are all held by its deployer and the repository says independent operators are a pre-mainnet condition (VERIFIED). So independence, which is what makes a median protect anything, is not demonstrated anywhere.
4. **Simulated on injected errors, a median of three removes the effect of one wrong oracle; a 30/30/40 weighted mean does not** (one oracle at 0 gives a price of 0.60 to 0.70 with the mean, about 1.00 with the median). With two oracles wrong in the same way, a bare three-oracle median is worse than the mean (kUSD's 3% spread guard, not modelled by the script, changes this: section 8). The assumptions are illustrative (section 6).
5. **Hourly rate limits on the price (KSD's 10%/h up, 25%/h down) cost a liquidation delay of about 1 hour for a 200% vault (after a drop of at least 30%) and would almost never bind on observed daily KAS moves** (worst day −24.9%; daily data cannot test an hourly limit). Their value is against oracle errors, which no ENRK model measures yet (section 7).
6. **ENRK's audited collateral oracle has no bound on a single-round price move** (audit I26, open). ANALYSIS: "price > 0" is already refused in variant B; a floor and a ceiling close price 0 and absurd values but do not bound moves inside their range.
7. **Open owner decisions** are in section 10. The data cannot make them alone: the main one is who the independent operators would be.

## 2. The question in ENRK terms

- ENRK vaults are judged against a KAS price held in oracle UTXOs. The current design is a **single publisher key** (`sweep` needs its signature); variant A of the prototype accepted a price of 0, variant B refuses 0 but has no rate or range limit; a per-sweep bound of ±10% with a minimum gap exists only as an executed test (`econ-v4` P20, test constants). A per-sweep bound alone allows about ×117 to ×300 per hour at one-minute gaps (`ECONOMICS-VERIFICATION` §2); the ×304 of section 7 is exactly 60 sweeps per hour, while 117 to 300 is the range at measured block rates. (From the repository, read on 2026-11-17.)
- There is no governance after launch (frozen parameters); "no pause" is this study's reading of an immutable design, not a sentence of the frozen document. The only reaction available to vault owners during a bad price is to add collateral or repay. A bound therefore matters mainly because it gives them time.
- Two different prices exist in ENRK: the **KAS price in USD** (collateral; this sheet) and the **peg index** (hashrate, energy, fees, adoption; a separate open question, not covered here).

## 3. Reference designs

### 3.1 Kaspa Dollar (KSD): miners vote the price
Source: full review in `kaspadollar/KASPADOLLAR-REVIEW-2026-11-15.md`.
- Median of votes written in the coinbase payload over 6,000 blocks (about 10 min), valid if at least half of the blocks vote, posted with a ZK proof; mint price rises at most 10%/h, liquidation price falls at most 25%/h; priced actions stop after 30 min without a price; settlement after 30 days. Pre-launch: no public code, testnet or audit (VERIFIED as of 2026-11-15; not re-checked on 2026-11-17).
- Maths recomputed and consistent after the corrections noted in the KSD review (VERIFIED). Weak points (ANALYSIS): after launch only 50% participation is enforced, so a 32.7% pool (whitepaper figure; my own sample gave 30.7%) can freeze the oracle alone whenever participation is below 82.7%; votes are written by pool operators; price correctness assumes voters read independent markets; the roadmap page mentions "publishers" and "membership covenants" that the whitepaper does not.
- Lesson for ENRK: the only published design that removes a publisher key; it is a specification, not a working system.

### 3.2 kUSD (github.com/Kali123411/kUSD): committee oracle in Argent
- Repository exists: MIT, created 2026-11-14, 8 commits, one GitHub account (author names Kali123411, and k402 on the three merge commits), Rust harness and Argent contracts, a file of instructions for an AI assistant (VERIFIED). README: "TN10 testnet research software. Not audited. Not a product. Not for real value." (VERIFIED).
- `contracts/v2/ag/oracle.ag` (VERIFIED by reading): five operators sign prints offline; anyone relays three prints from distinct operators; price = median of the three; accepted only if the three agree within 3%; mint price follows the price down at once and up at most 10%/h; liquidation price follows up at once and down at most 25%/h; each refresh applies at most one hour of rate; anyone can freeze after 1 hour of silence and settle after 30 days; three operators other than the replaced slot can rotate a key; the signed time (DAA score) is the feed's clock, with a co-spent input proving no print is in the future. The code comment calls the limits "KSD-style safety rails": the code comment labels them "KSD-style" and the numbers match KSD's (ANALYSIS: they were copied).
- Four of its testnet-10 transactions (oracle genesis, two refreshes and a key rotation) are accepted on chain (VERIFIED through api-tn10, 2026-11-17).
- Snapshot caveat (VERIFIED, README): the public repository is the 2026-11-14 snapshot; the live testnet-10 deployment has moved on and may differ from the code read.
- README: operator keys are held by the deployer; independent operators are a pre-mainnet gate (VERIFIED). The tests it claims (182 in the README, 116 in the whitepaper) were **not run** by me (UNVERIFIED).
- Properties (ANALYSIS from the code comments): one bad operator cannot move the price; two colluding operators move it only within the 3% band if the relayed set includes an honest print, but the relayer chooses which three of five prints to relay; free movement needs three of five, and the rate limits bound even that.
- Lesson for ENRK: shows the median of three and the asymmetric limits are expressible and executable in Argent on the L1. It is a singleton oracle UTXO; ENRK's design uses a population of price UTXOs for throughput reasons measured on testnet-10 (hot-UTXO figures in `econ-v3`); the two were not compared.

### 3.3 KUSD "oracle-free" (github.com/bitcoffee0/kusd)
- Different project with the same ticker. Experimental, testnet-10, inspired by Frankencoin: independent positions, challenges and Dutch auctions, an equity reserve (VERIFIED by README).
- Its liquidation price is a **fixed reference parameter** (the README: a deterministic Module parameter) (0.035 KUSD/KAS in the test fixtures), explicitly "not a live price feed" (VERIFIED by README). So the price problem is replaced by a fixed parameter and auction discovery; whether the peg holds is unknown. The "independent review" repository (STP-KAS) describes itself as a Grok pass, not an audit, and its own verdict says the peg without a DEX is "unproven" (VERIFIED as text; its transaction claims were not re-checked by me).
- Lesson: a design direction (auction-based discovery) for later study; it does not solve the same problem as a price feed.

### 3.4 Hyperliquid: two-layer weighted median
Source: the official oracle and robust-price-indices pages (structure and weights below VERIFIED by the independent reviewer on 2026-11-17); HIP-3 and the incidents are SECOND-HAND and were not read. Community pages list other weights; the mark-price page has a second weight set (3, 2, 2, 1, 1 over perpetual mid prices).
- Each validator publishes, about every 3 seconds, the weighted median of exchange mid prices (weights reported as 3, 2, 2, 1, 1, 1, 1, 1 over Binance, OKX, Bybit, Kraken, KuCoin, Gate, MEXC, Hyperliquid spot); the final price is the stake-weighted median across validators. The mark price used for liquidations is the median of three inputs (oracle plus a 150-second EMA of the gap, the local order book, and perpetual prices on other venues). Per-asset exclusions apply when a source is too thin.
- Incident, March 2025 (SECOND-HAND, press and postmortems): a thin spot market was pushed to squeeze a large short, liquidations followed, and validators then imposed a settlement price and delisted the contract; critics called it centralised, citing the concentration of stake. A 2026 incident of 57 M$ liquidations after an oracle anomaly on an equity perpetual is reported by KuCoin (not read in detail).
- Lesson (ANALYSIS): weighted medians of deep venues are the industry norm; a thin asset can still be manipulated; Hyperliquid could intervene by hand, ENRK (immutable, no pause) could not, so protection has to be in the rules.

### 3.5 Existing oracle networks and what covers KAS
| Network | Mechanism (SECOND-HAND comparisons, 2026) | KAS coverage |
|---|---|---|
| Chainlink Data Streams | independent nodes, pull model | **VERIFIED**: docs list stream `KAS/USD-RefPrice-mainnet-production` (CEX price, crypto market hours); 16 operators listed on the page (not independently assessed); access terms not checked |
| Pyth | publishers post prices, pull model, 200 ms channel | **VERIFIED**: feed `Crypto.KAS/USD` in the public Hermes listing; live-price endpoint answered HTTP 401 on 2026-11-17, terms not checked |
| Band Protocol | validator network | SECOND-HAND: KAS feed live on Kasplex (L2), vendor blog |
| Nuntius (Kaskad) | enclave (AWS Nitro) fetches exchanges, removes outliers, volume-weighted median, signs; contract accepts registered enclave keys | **VERIFIED** in its docs: KAS/USD from Bybit, CoinGecko, MEXC, KuCoin, Gate, Bitget, HTX (no Kraken); EVM (Igra), not L1; repository Apache-2.0, created 2026-03-16 |
| Quex | Intel TDX attested oracles for EVM chains | no KAS feed found (repository read: contracts verify attestation) |
| RedStone, API3, Chronicle, Switchboard, DIA, UMA | various (push or pull, first-party, whitelisted, custom, optimistic) | SECOND-HAND descriptions only; KAS coverage not checked |
| Zealous Swap TWAP | on-chain time-weighted price of a small DEX | pools are small (about 191 k USD locked, 15 k USD daily volume on 2026-11-12, SECOND-HAND DeFiLlama); not a safe source |
| Threshold (edenbd1/oracle-kaspa) | one backend takes the median of CoinGecko and CoinMarketCap every 15 s and anchors a hash in a testnet transaction | **VERIFIED** by README: one backend takes the median of CoinGecko and CoinMarketCap and anchors a hash (ANALYSIS: a single central backend, not a decentralised oracle; the project describes itself as a prediction-market app); the demo URL answered 404 |
None of these networks can be read by a Kaspa L1 covenant directly (ANALYSIS; no bridge to L1 script found). A publisher could read them and sign.

### 3.6 Wrapped KAS (wKAS, iKAS, WIKAS)
Three different tokens are confused under one name (SECOND-HAND): a custodial ERC-20 wKAS issued by Chainge on Ethereum (contract address unconfirmed, reports of blocked withdrawals and a large depeg, no primary report); iKAS, Igra's gas token via a canonical bridge; WIKAS, a wrapped iKAS in Zealous Swap pools. A 2026 signature-bypass in Kasplex's KRC-20 indexer drained pools and iKAS withdrawals to L1 were paused (press, amounts disagree). ENRK uses native KAS on L1: none of these is collateral or a price source (ANALYSIS).

## 4. Where a price can be read

Measured on 2026-11-10 (depth, `r4-market.md`) and 2026-11-17 (tickers, `sources_snapshot_2026-11-17.txt`); see `FICHE-SOURCES-oracle-2026-11-17.md`.
| Venue | Quote | 24 h volume 2026-11-17 (KAS) | Bid depth within 1% / 5% (USD, 2026-11-10) |
|---|---|---|---|
| Kraken | USD | 19.96 M | 134 k / 269 k |
| Bybit | USDT | 19.13 M | 27 k / 59 k |
| KuCoin | USDT | 17.95 M | 19 k / 39 k |
| Gate | USDT | 15.96 M | 7 k / 42 k |
| Bitget | USDT | 7.12 M | 13 k / 35 k |
| MEXC | USDT | no answer once | 4 k / 27 k |
Prices of the five that answered were within 0.29% (0.02714 to 0.02722); KAS was 8% below 2026-11-10 (VERIFIED, one snapshot).
Observations (ANALYSIS): five of six venues are USDT-quoted; the aggregators read the same venues; the cheapest pair to push 5% among the six holds about 62 k USD of displayed depth (MEXC + Bitget), about 98 k among Kraken/KuCoin/Bybit; a calm, week-old, displayed-only snapshot, so orders of magnitude only. Rate limits, terms of use and uptime of each API are UNVERIFIED.

## 5. Independence: the real constraint

- A median of three protects against one wrong oracle only if the three cannot fail together: different operators, keys, servers, source sets, quote currency (ANALYSIS).
- No existing system verified here demonstrates it for a KAS price on L1: kUSD's five keys sit with one deployer; KSD has no code; ENRK has one publisher; Nuntius is an enclave run by Kaskad on EVM.
- Operators for ENRK are a human and economic question that no data answers (who, paid how, liable for what).

## 6. How to combine prices (simulation, illustrative)
Script `ksd-derived/oracle_combiner_compare.py`, output saved, deterministic. **Assumptions, not measurements:** honest noise 0.5% per oracle; injected errors of the listed shapes; a vault at 200% is wrongly liquidated if the price falls below 0.75.
- One oracle reports 0 (the I26 case): weighted mean 30/30/40 gives 0.70 (a 30% oracle) or 0.60 (the 40% oracle), so every fresh 200% vault becomes liquidatable; median of three gives about 1.00.
- One oracle at ×2 or ×5: weighted mean gives 1.30 to 2.60; median about 1.00.
- Two oracles wrong the same way: the median follows them completely (0 or ×2); the weighted mean is diluted (0.30 to 0.40 for zeros). This is for a bare three-oracle median: the script does not model kUSD's 3% spread guard or its five-operator structure, under which two colluders must still take a third, honest print.
- Calm market: standard deviation 0.29% (mean) against 0.33% (median).
- The weighted median of 30/30/40 is always the middle value, i.e. the plain median.
- One oracle offline: two values remain, a median of two is their average and no longer protects; the rule when oracles are missing or disagree must be set in advance (not studied).

## 7. How fast the price may move (bounds)
Scripts `oracle_bound_grid.py`, `asym_limit_lag.py` and notes in `ksd-derived/`.
- A per-sweep limit has to be sized together with its minimum gap: 10% per sweep at one-minute gaps allows ×304 per hour; 2% per 10-minute gap allows ×1.13 per hour; 1% per 10 minutes needs about 11.5 hours to reflect a −50% real fall (VERIFIED arithmetic).
- KSD-style 25%/h downward limit on the liquidation price (analytic, ENRK's MCR 150%): a vault minted at 200% becomes liquidatable about 60 minutes after a sudden drop of at least 30% (a 20% drop does not make it liquidatable), 33 minutes at 175%, 107 minutes at 250% (only if the gap is at least 50%); real ratio at that moment 1.40, 1.20, 1.00 after −30%, −40%, −50% if the price stays flat; 1.33, 1.14, 0.95 with a continued 5%/h fall (assumption). ENRK's 120-minute auction adds separately.
- Such a limit would almost never bind on observed daily moves (worst day −24.9% in 1,285 days, `r4-market.md`); its value is against oracle error or manipulation, which is not modelled anywhere in the repository; and daily data cannot test an hourly limit by construction. Intraday KAS data is not held.
- Tighter bounds also allow larger refresh populations on L1 (spec §2.4, exact maximum N not established).

## 8. Architectures compared (ANALYSIS)
| | Single publisher (ENRK today) | Median of 3 signed prints (kUSD style) | Miner vote (KSD) | Existing network read by a publisher | Fixed price + auctions |
|---|---|---|---|---|---|
| Works on L1 today | prototype executed | **research code executed on testnet-10** | no code | yes, via a signer | testnet research |
| Who must be trusted | one key | 2 of 3 relayed prints; needs real independence | pool operators, participation | the publisher plus the network | nobody for price; peg unproven |
| One wrong source | fatal | harmless | harmless if participation stays high | depends on the network | n/a |
| Two wrong sources | n/a | bare median of 3: fatal; kUSD with 5 operators and 3 relayed prints: the price stays within about 3% of an honest print, free movement needs 3 of 5 | needs a share of hashrate | n/a | n/a |
| Missing evidence | bound, I26 | independence, audit, tests not run by me | everything | access terms | peg |

## 9. Candidate course of action (mine, not a decision)
1. Proposal: a floor and a ceiling in the oracle and in every vault entry (price > 0 is already refused in variant B); this closes price 0 and absurd values but does not bound moves inside the range.
2. Proposal: prefer a median of at least three independently operated prices over a weighted mean, if the independence condition can be met; otherwise do not claim the protection.
3. Proposal: size a per-time bound (move and gap together) only after an hourly crash model and an oracle-error scenario exist; keep asymmetric limits for later.
4. Proposal: use deep venues, at least one USD-quoted, and exclude sources too thin to matter, as Hyperliquid does per asset; refresh depth before choosing.

## 10. Decisions asked of the owner
1. Floor, ceiling and price > 0 in oracle and vaults: yes or no?
2. A per-time bound in principle (yes, no, after an hourly model)? Who sets the constants, by which criteria (crash lag accepted, reaction time needed if a key is stolen)?
3. Combination rule: median of three, weighted, or other; what happens when an oracle is missing or they disagree?
4. Independence criteria for operators; who they would be.
5. Source criteria: at least one USD-quoted source; aggregators allowed or not; networks (Chainlink, Pyth, Nuntius) as inputs only.
6. Refresh the depth measurement first (one-shot, ideally on a day KAS moves more than 8%)?

## 11. Not verified or not done
- Terms, costs and limits of the Chainlink and Pyth feeds; any KAS feed on RedStone, API3, Chronicle, Switchboard, DIA.
- kUSD's tests (182 per its README) and everything except `oracle.ag` and four transactions; Threshold, Quex and the bitcoffee0 code beyond their READMEs.
- Hyperliquid official pages, current weights, and the 2026 incident details.
- Stressed-market depth and depth beyond 5%; intraday KAS prices; the effect of oracle manipulation on ENRK (no model).
- Cost, in transaction mass, of reading three prices inside each vault on L1; contention behaviour of a singleton versus a population oracle.
- The peg index sources (separate question).

## 12. Evidence index
KSD: `kaspadollar/evidence/`. Sources and depth: `FICHE-SOURCES-oracle-2026-11-17.md`, `sources_snapshot_2026-11-17.txt`, repository `r4-market.md` and `~/ENRK_market_data/`. Simulations and outputs: `ksd-derived/*.py`, `*_output.txt`. kUSD: cloned read-only on 2026-11-17 in the session scratchpad (not kept in the repository); relevant file `contracts/v2/ag/oracle.ag`, commit history of the repository, three testnet-10 transaction ids listed in its `docs/pitch/evidence/INDEX.md`. Chainlink: page `docs.chain.link/data-streams/crypto-streams`. Pyth: `hermes.pyth.network/v2/price_feeds?query=kas`. Nuntius: `docs.kaskad.app/docs/oracle-integration`.
