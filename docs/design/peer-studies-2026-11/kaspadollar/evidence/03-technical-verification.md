# Kaspa Dollar (KSD) - technical and mathematical verification

Date of verification: 2026-11-15. Scope: technical/mathematical claims. All web content treated as untrusted data. No contact made with anyone; no wallet address recorded (addresses in the roadmap page were replaced by "[ADDRESS REDACTED]").

Evidence files (this folder): `03-site-snapshot-{whitepaper,how-it-works,docs-roadmap,why-stablecoins,contact}-2026-11-15.txt` (text extracted from kaspadollar.com HTML fetched 2026-11-15; figures/SVG removed, so Figure 1/2 content and chart values are NOT captured), `03-check.py` + `03-check-output.txt` (maths), `03-miner-sample.py` + `03-miner-sample-output.txt` (pool-tag aggregate).
Note: the page is at /docs is titled "Roadmap and funding".

## 1. What the site says (summary, 2026-11-15)
- Whitepaper: working document "awaits peer review", "parameters, proofs, wording and design can change", single author (A. Safstrom, described as Kaspa core contributor and author of KIP-16).
- KAS-collateralised CDP; R_o=250% (open/mint/withdraw), R_l=200%, penalty p=5%, min debt 10 KSD, oracle = median of coinbase-payload votes (13 B: "KVOT"+ver+price) over 6,000 blocks (~10 min), valid if votes >= 50% of blocks; ZK proof (RISC Zero, Groth16 or STARK) over KIP-21 miner-payload commitments; mint price rises <= 10%/h, liquidation price falls <= 25%/h; stale > 30 min => freeze; no price for 30 days => settlement; net issuance cap M=50,000/day with k=8 minting UTXOs; launch gate 90% voting for 30 days.
- Roadmap page: fundraiser target 5,000,000 KAS closing 1 Jan 2027; build Jan-Apr, testnet May, audit Jun-Aug, mainnet September (year not stated; implicitly 2027); 72% / 28% funds split.

## 2. Maths re-derivation (03-check.py, stdlib only; output in 03-check-output.txt)
| Item | Result |
|---|---|
| Eq. (4) x=(R_l d - c l)/(R_l-1-p) | Correct: post-liquidation ratio = exactly 2.0 for all tested rho in (1.05,2). x=d exactly at rho=1+p; x>d for rho<1+p (consistent with the whitepaper's full-liquidation branch). |
| Worked example (how-it-works) | Reproduced: x=1,926.3 KSD (13.2% of debt), KAS received value 2,022.6 (site: 2,023), left 25,427 vs 12,714 KSD (site: same), penalty 96.3 (site: 96). Starting ratio 27,450/14,640 = 187.5%. All numbers consistent. Site rounds in reader's favour only. |
| Theorem 1 (cap) | B=M/(2k)=3,125; 2B=6,250/UTXO; 8x6,250=50,000. Arithmetic correct. The 50,000 is a worst-case burst in any 24 h window; sustained rate is M/2=25,000/day (check script). The proof argument (budget at start + refill, each <= B) is sound for net supply provided "proven time" cannot exceed real time; proven dt is bounded by chain selected-parent timestamps, which miners can skew (whitepaper itself cites a 132 s tolerance); effect small. Caveat: repay/burn credits budget up to B, so burn-and-remint cycles are possible but net supply bound still holds. |
| Theorem 2 (thresholds) | Algebra consistent: control a>=pi/2, stop a>pi-g. pi=0.9,g=0.5 -> 45% / 40% (matches). pi=1 -> 50%/50%. |
| "25% minimum" (how-it-works) | pi/2 at pi=g=0.5 = 25%: consistent. But the whitepaper's own stop-the-oracle threshold pi-g falls to 0 as pi->g (5% at pi=0.55). The headline "needs a majority" holds only while participation stays near 100%; the 90% launch gate is not an invariant after launch (only g=50% is enforced afterwards). See 3.1. |
| 60% / 50% backing | 1-1/2.5=60% and 1-1/2=50%: arithmetic correct. The 60% figure applies only to a vault at exactly 250% never touched; a vault sitting at 200% (any vault after a partial liquidation, which returns it to exactly 200%) tolerates 50%. Whitepaper (5) states the 50% correctly; how-it-works headline uses 60% for the "KSD" box. Also "price has to fall 20% from opening to be liquidatable" = 1-2/2.5 = 20% correct. |
| Rate-limit numbers | m doubles in 7.27 h (site 7.3); l halves in 2.41 h (site 2.4); l /10 in 8.00 h (site 8.0). Correct. Recovery after a -40% round trip: mint price needs 5.4 h to climb back (not stated on site). |
| Fall-lag numbers | (1-F)^(-8/60)=1.039 < 1.05 (site 1.04); 1-0.75^(10/60)=4.68% (site 4.7%); h for D=20%: 0.606 h = 36 min (site 36 min); D=40%: 1.606 h (site 1.6 h). Correct. Extra: D=50%: 2.24 h = 134 min. |
| ATH fall rate | 1-0.17^(1/19,700)=0.0090%/h (site 0.009%). 27 months=19,723 h. Correct arithmetic. (Price history itself UNVERIFIED.) |
| Funding split | 72%/28% of 5,000,000 = 3,600,000 / 1,400,000. Correct. |

## 3. Issues, unstated assumptions, edge cases (analysis; items marked [A] are my analysis of the published text, not claims the site makes)
3.1 [A] Participation decay. After the 30-day 90% launch gate, only g=50% applies. At pi=0.6 a single 32.7% pool (the whitepaper's own number) exceeds the stop threshold (pi-g=10%) and, at pi<=0.727, can freeze the oracle alone; control needs pi/2. The security argument therefore depends on sustained near-universal voting, which depends on miner incentives that the whitepaper says are "not yet decided" (pre-launch rewards) and "first estimate" (85/10/5 split).
3.2 [A] Votes come from pool operators, not hashers. The coinbase payload is built by whoever builds the block template (the pool or solo miner); pool participants cannot vote independently. The "hashrate share" analysis is therefore a share of operator-controlled templates. Whitepaper partly acknowledges ("centralization factor not known within these pools"). Measured: top two tag families ~52% in my sample (section 5).
3.3 [A] Thin-market oracle risk. A4 assumes voters read independent exchange sources; if KAS spot books are manipulable or all voters use the same few venues, the median can be moved without any hashrate attack. Rate limits (10%/h, 25%/h) bound but do not remove this. Not discussed in the paper.
3.4 [A] Liquidation price lag in real crashes. Liquidation is profitable only if l <= (1+p)P. A fall faster than 25%/h leaves l above (1+p)P for 36 min (-20%), 96 min (-40%), 134 min (-50%); during that time liquidators cannot profit and only the 50% buffer protects backing. The paper acknowledges this ("a fall deeper than 50% can leave debt unbacked"). Note KAS has had single-day falls larger than 25% in the past: UNVERIFIED here (no price data pulled).
3.5 [A] Redemption peg floor weakened by l. Redemption pays x/l KAS per KSD with l >= median >= market in falls: redeemers receive less than $1 of KAS per KSD (up to the lag, e.g. ~4% at the design speed, much more in a sudden fall), so the arbitrage floor ("buy at 0.97, redeem for 1.00") quoted on how-it-works is not available when it is most needed. Conversely after a rise a stale low l lets redeemers/liquidators take KAS below market value (whitepaper 7.1 acknowledges).
3.6 [A] Vault choice. Redeemers choose any vault with rho(l)>=1 (Liquity redeems lowest-ratio first). Whitepaper argues redemption does not lower rho(l); it does lower rho(P) when l<P (stale low l) and lets a redeemer target a specific victim vault (e.g. one that cannot react). No ordering rule or fee dampener exists besides beta=0.1%.
3.7 [A] No hysteresis: liquidation returns vault to exactly 200%, so any later tick down makes it liquidatable again; each liquidation pays p=5% of the repaid amount plus oracle fee (0.1%, floor 1 KAS). Repeated small liquidations can compound penalties on the owner (griefing by a liquidator with oracle timing).
3.8 [A] Dust/griefing. Min debt 10 KSD; min oracle fee 1 KAS (about $0.037 at the site's example price 0.0366). Whitepaper says the floor "sets a cost for spam"; at that price the floor is negligible relative to attacker gains, and for 10 KSD vault liquidation the liquidator's 5% (0.50 KSD) must exceed network fees (post-Toccata min fee 100 sompi/gram per toccata-guide) - likely positive, not quantified by the site.
3.9 [A] 50% vote threshold / window: windows overlap and "any anchor may end a window"; Delta-t clipping (eq. 1) prevents re-counting, shown in Theorem 4; I found no flaw. Proof relies on RISC Zero soundness (A3) and on the chain-block access window; the "about 12 hours" auto-freeze is consistent with finality depth 432,000 blocks at 10 bps (finality_depth defined in rusty-kaspa params; exact value not read; UNVERIFIED).
3.10 [A] Stale price / 30 min halt: priced actions (mint, withdraw, liquidate, redeem) stop; add collateral/repay/close continue. During halts nobody can liquidate, but owners can only improve. Stage-three bad debt falls on KSD holders (how-it-works says so honestly).
3.11 Settlement: after 30 days without update, holders redeem at the last median at no time limit. Asymmetry: vaults below 100% at that price are not redeemable against, so shortfall stays with holders (stated on how-it-works).
3.12 Oracle manipulation with the 2 largest miners: whitepaper itself states (29 Oct 2026 data) that two largest pools (57.1%) can do both attacks; its only defences are rate limits, the 50,000/day cap and an unproven social argument ("miners leave a pool that attacks in public"). how-it-works: "Nothing in the protocol penalises an attacker beyond the lost oracle reward". Unbacked issuance cap 50,000 KSD/day => bounded in absolute terms, but relative to a young system's supply (unknown) could be the entire supply.

## 4. Contradictions between pages / internal inconsistencies
- Oracle design: whitepaper = permissionless miner votes. Roadmap (/docs) deliverables list "publisher software", "membership covenants", "publisher ejection, membership changes" in testnet scope, "publishers run the oracle", "membership covenants" in audit, and Contact page lists "publisher candidates". That describes a permissioned publisher/membership set not present in the whitepaper (whitepaper contains 6 covenant types: vault, factory, minting, liquidation, token, fee treasury; no membership covenant). Either leftover text from an earlier design or an undisclosed second oracle path. UNVERIFIED which.
- Backing headline: how-it-works says the KAS price "can fall 60% before this KSD is unbacked"; whitepaper bases the guarantee on 50% (R_l=200%). Differ by vault state (see section 2).
- how-it-works: "The upcoming whitepaper will support the above stated facts with proofs" while the whitepaper is already linked from that page and online (the page text appears stale).
- how-it-works describes a 90%/30-day launch gate but says "protocol continues ... with its 50% vote threshold" afterwards (consistent with whitepaper but contradicts the "majority of the network" framing in the abstract when participation is <100%).
- Whitepaper says Groth16-vs-STARK choice "to be decided"; Groth16 is not quantum-safe (KIP-16 text says so). Unresolved design choice.
- how-it-works: liquidation "done by anyone, via a P2P gossiping layer (for the OGs: Stroemnet P2P)" - unexplained, no protocol mechanism described in the whitepaper (UNVERIFIED).
- why-stablecoins: "design has been stress-tested through several market cycles" refers to Maker/Liquity, not to KSD (no KSD code public; Contact page: GitHub "published when the repository is public").
- Whitepaper "Toccata hard fork added ... covenants, KIP-16, KIP-21": consistent with release notes (section 6).
- Whitepaper Section 2 claim "no deployed system has taken a price from the host chain's own miners without a consensus change" - a negative claim; I did not search exhaustively: UNVERIFIED.

## 5. Dependency status on Kaspa mainnet (as of 2026-11-15)
| Item | Evidence | Result |
|---|---|---|
| Toccata hard fork active on mainnet | rusty-kaspa release v2.0.0 (published 2026-06-05, https://api.github.com/repos/kaspanet/rusty-kaspa/releases/tags/v2.0.0): "scheduled to activate on mainnet at DAA score 474,165,565, roughly June 30, 2026 16:15 UTC". api.kaspa.org/info/blockdag on 2026-11-15 ~10:30 UTC: virtualDaaScore 593,184,413 (> activation), block header version 2, pastMedianTime = 2026-11-15 10:32 UTC. Releases v2.0.1 (2026-06-15), v2.1.0 (2026-09-22, "post-Toccata consensus streamlining", standalone ZK SDK crate for RISC Zero Groth16/STARK). | Active on mainnet (inferred from DAA score > activation score and v2 headers; I did not submit/observe a covenant transaction on mainnet). |
| KIP-16 (OpZkPrecompile) | kaspanet/kips kip-0016.md header "Status: Active"; precompiles Groth16 tag 0x20 and RISC0-Succinct tag 0x21; cited in v2.0.0 notes. | Merged, Active. |
| KIP-17 (covenants/introspection) | kip-0017.md "Status: Active", Updated 2026-05-31. | Active. |
| KIP-20 (covenant IDs) | kip-0020.md "Status: Active", Updated 2026-05-28. | Active. |
| KIP-21 (sequencing commitment, miner payload root) | kip-0021.md "Status: Active", Updated 2026-05-28; section 6.5.2 commits raw coinbase payload bytes of all mergeset blocks with block hash and blue_work: matches whitepaper's MinerPayloadRoot description. Accessor doc: OpChainblockSeqCommit limited by access threshold F = finality depth. | Active; matches. |
| KCC-1, KCC-2, KCC-20 | kaspanet/kccs README table: KCC-1, 2, 20 "Final" (KCC-20 created 2026-08-21, requires KCC-1/2, KIP-20); KCC-23 Draft. KCC-20 text: no "mint"/"burn" matches (consistent with whitepaper: "KCC-20 does not define a mint or a burn"). Note: KCC is a convention, not consensus. | Final as conventions; no mint/burn defined: consistent. Whitepaper dates (21 Oct) differ from KCC-20 "Created 2026-08-21" - finalisation date not checked (UNVERIFIED). |
| Coinbase payload vote (KVOT, 13 B) vs consensus | rusty-kaspa params.rs: max_coinbase_payload_len = 204 (all networks), coinbase.rs serialises blue score(8)+subsidy(8)+SPK version(2)+SPK len(1)+SPK script+extra_data; extra data is free-form bytes. With a 34-byte Schnorr script, 204-53=151 B left; 13 B fits. Observed mainnet coinbase extra data already carries free-form pool strings. | Consistent with consensus. Votes are not validated by consensus (any bytes allowed), so well-formedness is enforced only in the ZK guest. |
| Block rate | Measured 574 DAA-score increase in 60 s (about 9.6 blocks/s) on 2026-11-15 => ~10 bps assumption ok; W=6,000 blocks ~ 10 min. | Consistent. |
| ZK verification inside script/mass limits | KIP-16 section 9: Groth16 verification 1.65 ms (~134x ECDSA), STARK 9.08 ms (~738x ECDSA), priced in sigop-equivalents. toccata-guide (rusty-kaspa docs): "doubling of the transient mass limit to allow ZK-STARK proofs"; min fee 100 sompi/gram*max(compute grams, 2*tx bytes). Whitepaper's proofs wrap the receipt in Groth16/STARK (constant size). I did not find a published number for the compute/mass of the KSD update transaction (extra opcodes: treasury, seqcommit, covenant state, plus the proof), nor a successful mainnet demo. | Feasible in principle (opcode exists, STARK/Groth16 fit by design); fitting the complete KSD update transaction within limits is UNVERIFIED. Proving cost/latency (delta=3 min assumed in paper) UNVERIFIED. |
| KSD itself on testnet/mainnet | Roadmap: testnet May, mainnet September (year implicit 2027); GitHub "published when the repository is public". | Not deployed; no code available to review. |

## 6. Miner concentration data point (29 Oct 2026: 32.7% / 57.1%)
- Source cited by the whitepaper: miningboard.com/mining/kaspa/pools (accessed 29 Oct 2026). I did not fetch it (UNVERIFIED directly).
- Independent aggregate (03-miner-sample.py, api.kaspa.org, 2026-11-15, 2,223 consecutive blocks, ~3.7 min, grouped by coinbase extra-data pool tag, no addresses): humpool 30.7%, F2Pool 21.5%, ViaBTC 11.3%, wpool 3.2%, kaspa-pool.org 2.9%, 2Miners 1.7%, Kryptex 1.0%, others/untagged 24.3% (includes untagged and unmapped tags). Top two tagged families 52.2%; top three 63.5%.
- Interpretation: same order of magnitude as the whitepaper (32.7% single, 57.1% top two); within sampling error for a 3.7-minute sample (binomial sd about 1 point for 30%) and different date, tag grouping and methodology. Largest pool share confirmed approximately; top-two share 52% vs 57% is NOT confirmed exactly. Tag attribution is by software string, not on-chain proof of ownership. The 2223-block sample is too short to estimate hashrate share to better than a few points.

## 7. Prior-art claims (only explicit ones)
- "Maker's liquidation at penalty; Liquity's redemption as peg floor and no interest" - accurate in general terms (not verified against the cited papers' text here: UNVERIFIED but consistent with common knowledge).
- Maker/Liquity "read prices from signed feeds" - Maker uses permissioned oracle feeds, Liquity used Chainlink (and Tellor fallback): "signed feeds" is a simplification; not checked at primary source.
- Terra and Slinky as stake-weighted median votes with slashing: general description plausible, not verified.
- BIP 100 "numbers voted in coinbases, supermajority, capped step": matches the BIP's well-known design (not re-read).
- why-stablecoins: "overcollateralized design introduced by MakerDAO's SAI in 2017 and refined by Liquity in 2021" - SAI launched Dec 2017; Liquity mainnet April 2021: plausible, not re-checked. "Nobody ... can freeze a balance" is a claim about KSD that depends on the KCC-20 token covenant authority scheme (KCC-2): UNVERIFIED.
- Statistics on why-stablecoins (USDT 182B, USDC 72B, 46T volume, Aave 12.3B): third-party figures dated Oct 2026; NOT verified (outside my technical scope; note arithmetic 182+72+46=300 ok).

## 8. Claims table
| Claim | Where | Verified? | Method | Result |
|---|---|---|---|---|
| Eq. (4) liquidates to exactly 200% | WP 6.2 | Yes | 03-check.py | Correct |
| Example: x~1,926 KSD, USD 2,023, left 25,427 / 12,714, loss 96 | HIW 3 | Yes | 03-check.py | All numbers reproduce |
| 250%/200%/100% bands; liquidation after -20% | HIW 2 | Yes | arithmetic | Correct |
| 60% fall tolerated | HIW 1-2 | Partly | arithmetic | Only for untouched vault at 250%; 50% for vaults at 200% |
| 50% fall tolerated at 200% | WP 8.2, Table 3 | Yes (arithmetic) | arithmetic | Correct under stated assumptions |
| Theorem 1: <= 50,000 KSD/24h, B=3,125, k=8 | WP 8.1 | Yes (arithmetic and argument) | 03-check.py | Correct; sustained 25,000/day; assumes honest timestamp-based dt |
| Theorem 2: pi/2 control, pi-g stop; 45%/40% at pi=90% | WP 8.3 | Yes (algebra) | 03-check.py | Correct; weak at low pi |
| Never less than 25% network hashrate to control | HIW 5 | Yes | algebra | Correct (pi=g) |
| Largest miner 32.7%, top two 57.1% (29 Oct 2026) | WP 8.3 | Partly | api.kaspa.org tag sample | ~30.7% / ~52% observed 15 Nov; cited MiningBoard source not fetched |
| m doubles >= 7.3 h; l halves 2.4 h; /10 8.0 h | WP 8.3 | Yes | arithmetic | Correct |
| Fall lag 1.04 < 1.05; 4.7%; 36 min; 1.6 h | WP 8.2 | Yes | arithmetic | Correct |
| Coinbase payload <= 204 B, vote 13 B | WP 5.1 | Yes | rusty-kaspa params.rs/coinbase.rs | max_coinbase_payload_len=204; extra data free-form; fits |
| ~10 blocks/s, W=6000 ~ 10 min | WP 3, 5.2 | Yes | DAA rate 574/60 s | ~9.6 bps |
| Toccata added covenants, KIP-16, KIP-21 | WP 1 | Yes | releases, DAA vs activation | Active on mainnet (inferred) |
| KIP-16/17/20/21 exist and are Active | WP refs | Yes | kips repo headers | Active |
| KCC-1/2/20 Final; KCC-20 has no mint/burn | WP 3, 4 | Yes | kccs README/text | Final; no mint/burn found |
| OpChainblockSeqCommit returns commitment for chain block within finality depth | WP 3 | Partly | KIP-21 accessor doc | Matches (access threshold F = finality depth); 12 h figure unverified |
| MinerPayloadRoot commits hash, blue work, payload digest | WP 3 | Yes | KIP-21 6.5.2 | Matches |
| Groth16/STARK verification feasible on L1 | WP 5.3 | Partly | KIP-16 benchmarks | Opcode exists; full KSD tx fit and 3 min proving delay unverified |
| Oracle is miner-vote only (no trusted committee) | WP 1, HIW 5 | Contradicted/unclear | roadmap text | Roadmap mentions publishers/membership covenants |
| "Needs majority of network to stop oracle" | Abstract | Conditional | algebra | Only at 100% participation |
| Peg floor via redemption | HIW 4 | Partly | analysis | Weakened by l >= median in falls |
| Nobody can freeze a balance | WHY 6 | Unverified | - | Depends on KCC-20/KCC-2 authority |
| No deployed system took price from host-chain miners without consensus change | WP 2 | Unverified | - | Negative claim, not searched |
| KSD tested; code public | HIW/WHY | Not available | Contact page | Repo "published when public" |

## 9. Not verified / could not access
- MiningBoard page (the whitepaper's source for 32.7%/57.1%) not fetched; Oct 29 data cannot be reproduced; my sample is 15 Nov, 2,223 blocks.
- Figures 1-2 and SVG charts from the site not captured in the text snapshots.
- No KSD code, testnet, GitHub repo or explorer data found (site says not yet public). No contract/mass numbers for the KSD update transaction.
- No independent price-history data (KAS -83% ATH to Oct 2026, daily crash magnitudes) was pulled.
- Mainnet activation inferred from DAA score and v2 header version; no covenant transaction observed.
- KCC-20 finalisation date (21 Oct per whitepaper vs Created 2026-08-21 in file) not reconciled.
- Prior art characterisations (Maker, Liquity, Terra, Slinky, BIP 100, Reflexer) not re-read at primary source; Reflexer not mentioned by the site.
- Third-party statistics on why-stablecoins (DefiLlama, a16z, Crypto Briefing, Aavescan) not checked.
- Proving-time delta (3 min), proof sizes for the chosen system, and the claim that windows can be recursed with RISC Zero chunk receipts were not tested.
