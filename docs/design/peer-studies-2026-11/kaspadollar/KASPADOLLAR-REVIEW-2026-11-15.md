# Kaspa Dollar (KSD) — due-diligence review

**Date:** 2026-11-15. **Status:** read-only study. Nothing here is a design decision for ENRK.
**Subject:** https://kaspadollar.com/ (pages /, /how-it-works, /whitepaper, /docs "Roadmap and funding", /why-stablecoins, /contact).
**Method:** three independent evidence passes (GitHub and code; team, accounts, domain, fundraiser; technical and mathematical), then a spot-check of key facts by the author of this synthesis. Raw evidence and per-claim sources are in [`evidence/`](evidence/). Nothing was posted, sent or signed up to; nobody was contacted. No wallet address is stored in any file of this folder (the site's fundraiser address is referred to as "the address published on /docs").

Tags: **VERIFIED** (checked at a primary source or by calculation, on 2026-11-15), **SECOND-HAND** (reported by a third party, primary not opened), **UNVERIFIED** (not checked or not checkable), **ANALYSIS** (my reading of the published text, not a claim of the site).

---

## 1. Bottom line

KSD is a **pre-launch design with a funding campaign**, not a product. No token, no testnet, no public code, no audit exists. All the arithmetic that was recomputed reproduces (equation 4, the worked example, Theorems 1 and 2, rate-limit and lag numbers); the figures and charts, Theorems 3-4 and the price-history claims were not checked. The evidence found on the person and the on-chain fundraiser is consistent with what the site says. The open issues are about the design's assumptions (oracle, participation, redemption floor), one unexplained contradiction about a permissioned "publisher" set, and the absence of anything that can be inspected.

## 2. What was verified

| Claim | Result | Source (all accessed 2026-11-15) |
|---|---|---|
| No public repository | **VERIFIED.** The /contact page says GitHub is "published when the repository is public". GitHub API returns 404 for users/orgs `kaspadollar`, `KaspaDollar`, `kaspa-dollar` (re-checked by me); repository search for "kaspadollar" returned 0 results on my and the reviewer's runs (the first evidence pass recorded 2 third-party hits, STP-KAS/kaspa-builders and kaspa-master-file, apparently from a broader query; neither is project code). | `evidence/01-github-code.md` |
| Founder authored KIP-16 | **VERIFIED.** Header of `kip-0016.md`: "Authors: Alexander Safstrom (@saefstroem)", Status Active (re-checked by me). | `evidence/01-kip16-header.txt` |
| Founder is a "Kaspa core developer" | **PARTLY.** 11 commits on `rusty-kaspa` master since 2023-11-21: 6 under the current login `saefstroem` (2025-01-06, 2026-02-05, 2026-02-08, 2026-04-19, 2026-04-27, 2026-06-23; list re-checked by me) and 5 under the former login `starkbamse` (same GitHub account id; found by the independent reviewer in a clone of the repository), which matches the 11 contributions of the contributors endpoint (rank 11 of 47). 13 PRs of which 1 open and 1 closed unmerged (not re-run by the reviewer, API rate limit). He is not shown as a maintainer in what was checked. Whether he is an official core-team member: **UNVERIFIED** (no official Kaspa source found). | `evidence/01-github-code.md` §3 |
| "With the help of the rest of the Kaspa core team" | **UNVERIFIED.** One named core developer (Michael Sutton) is reported **SECOND-HAND** (Cryptoast 2026-10-26) to have pledged technical help; the primary post was not opened. No official endorsement and no denial found. | `evidence/02-team-accounts-fundraiser.md` F7 |
| KIP-17, 20, 21 authors as cited | **VERIFIED**, and all four KIPs (16, 17, 20, 21) are marked Active (commit of 2026-07-15). KIP-21 was edited again on 2026-11-01. | `evidence/01-github-code.md` §4 |
| KCC-20 "Final, 21 October" | **VERIFIED** (status advanced to Final by commit "KCC-20: advance to Final (#41)", 2026-10-21). The founder is **not** an author of KCC-20 (authors: Helfer, Sutton, Newman, Billot); he wrote KCC-0 (process document). KCC-20 defines no mint or burn, as the whitepaper says. | `evidence/01-github-code.md` §5, `03` §5 |
| Toccata active on mainnet | **VERIFIED by inference.** Release v2.0.0 sets activation at DAA score 474,165,565 (about 2026-06-30); mainnet DAA score on 2026-11-15 was about 593.2 M with v2 block headers. No covenant transaction was observed on mainnet. | `evidence/03-technical-verification.md` §5 |
| Coinbase vote fits consensus | **VERIFIED.** `max_coinbase_payload_len` = 204 bytes, extra data is free-form, vote is 13 bytes. Consensus does not validate votes; only the proof guest does. | `evidence/03` §5 |
| Mathematics (eq. 4, worked example, Theorems 1 and 2, rate-limit and lag numbers) | **VERIFIED by recomputation** (`evidence/03-check.py`, output in `03-check-output.txt`). | `evidence/03` §2 |
| Domain | **VERIFIED.** Registered 2026-08-21 (Cloudflare registrar, registrant redacted); TLS certificate issued 2026-10-14; first on-chain receipt and launch post 2026-10-23. | `evidence/02` §3 |
| Fundraiser figure | **VERIFIED.** On-chain balance 640,011.27 KAS equals the homepage 640,011; 848 transactions, all incoming, none outgoing; first receipt 2026-10-23, last 2026-11-15. | `evidence/02` §4 |
| Miner concentration "32.7% / 57.1% (29 Oct)" | **PARTLY.** My independent sample (2,223 blocks, 2026-11-15, by pool tag): 30.7% largest, 52.2% top two. The cited MiningBoard page was not fetched. | `evidence/03` §6 |

Tagging note: in section 4 below, A, B (what the pages say), F (arithmetic), G, H (what is Active), I (chain figures) and K state facts read or recomputed. C, D and E and the readings inside G and I (for example "refunds depend on the operator") are ANALYSIS. J and the sentence about meme-token fees being mixed into the total are UNVERIFIED hypotheses. "None exists" means "none found on 2026-11-15".

## 3. Design as published (summary)

KAS-only overcollateralised CDP on Kaspa L1 covenants (not KRC-20, not another chain). Open/mint at ≥250%, liquidation below 200% down to exactly 200% (partial), penalty 5%, minimum debt 10 KSD. Redemption at $1 of KAS per KSD from a vault chosen by the redeemer. Net issuance capped at 50,000 KSD in any 24 h window (burst bound; 8 minting UTXOs with budget B = 3,125, each able to hold up to 2B; sustained rate 25,000/day). Oracle fee 0.1% (floor 1 KAS) on priced actions. No stability fee is stated. Price = median of miner votes in the coinbase payload over 6,000 blocks (about 10 min), valid if ≥50% of blocks vote, posted with a ZK proof (RISC Zero; Groth16 or STARK not decided). Mint price rises at most 10%/h; liquidation price falls at most 25%/h. After 30 min without a valid price, priced actions stop; after 30 days, anyone can trigger final settlement. Launch gate: 90% of blocks voting for 30 days.
Plan (site): fundraiser to 2027-01-01 (target 5,000,000 KAS, refund if missed), build Jan-Apr, testnet May, audit Jun-Aug (1,400,000 KAS), mainnet September. The year is not written on the page; 2027 is inferred.

## 4. Findings and open issues

Severity is my judgement; none is a proof of a defect, all come from published text.

**A. Not inspectable.** No code, testnet, audit, or bug bounty. The whitepaper calls itself a working document that "awaits peer review" and says parameters, proofs and wording can change. Every protocol property is therefore UNVERIFIED as implemented. The "stress-tested through several market cycles" sentence on /why-stablecoins concerns Maker and Liquity, not KSD.

**B. Contradiction on who runs the oracle (unexplained).** The whitepaper describes permissionless miner votes only. The /docs roadmap lists "publisher software", "membership covenants", "publisher ejection and membership changes" and says "publishers run the oracle"; /contact asks for "publisher candidates". Either text is left over from an earlier design, or a second, permissioned path exists. The whitepaper has no membership covenant (six covenant types). UNVERIFIED which. The whitepaper also says "the deployer funds the treasury at genesis" without defining the deployer's powers, and describes no upgrade or pause mechanism.

**C. Oracle security depends on sustained participation and on pool operators (ANALYSIS).** Thresholds hold as written (control needs π/2 of voting hashrate, stopping needs more than π−g; 45% and 40% at π=90%). But after the 30-day launch gate, only g=50% is enforced. At π=60% the stop threshold is 10%; a single 32.7% pool (the whitepaper's own figure) can freeze the oracle alone whenever π < 82.7% (stop condition a > π − 0.5; at the 90% launch gate it needs more than 40% and cannot). The earlier "72.7%" in `evidence/03-*` is an arithmetic slip, corrected here after the independent review (`REVIEW-INDEPENDENT-2026-11-15.md`, finding 1). The "needs a majority of the network" framing holds only near 100% participation. Votes are written by whoever builds the block template, which in pooled mining is the pool operator. The whitepaper itself says the two largest pools together (57.1%) could run both attacks; its defences are the rate limits, the issuance cap, and a social argument ("miners leave a pool that attacks in public"). The one critique found in public (SECOND-HAND, 2026-11-10) is the same concentration point.

**D. Price correctness rests on an unenforced assumption (ANALYSIS).** Assumption A4 says more than half of voting hashrate reads independent exchange prices. Nothing in the protocol enforces it. A thin KAS spot market could move the median without any hashrate attack.

**E. The redemption peg floor weakens in a fall (ANALYSIS).** Redemption pays x/ℓ KAS where ℓ is the liquidation price, at or above the median in a fall. Redeemers get less than $1 of KAS per KSD exactly when the arbitrage "buy at 0.97, redeem at 1.00" is needed. Redeemers can target any vault above 100% on ℓ, with no ordering rule (Liquity redeems lowest ratio first).

**F. Liquidation lag in fast falls (VERIFIED arithmetic, acknowledged by the whitepaper).** With the 25%/h limit, liquidations are not profitable for 36 min after a −20% drop and about 1.6 h (96 min) after −40% (both in the whitepaper); 134 min after −50% is this study's recomputation, not a whitepaper figure. A fall deeper than 50% in a halt can leave debt unbacked; the protocol does not socialise or mint to cover losses (holders bear them).

**G. Headline inconsistency.** /how-it-works says KSD survives a 60% fall; that holds only for an untouched vault at 250%. After any partial liquidation a vault sits at 200% and tolerates 50%, which is what the whitepaper states. Also, /how-it-works still says the whitepaper is "upcoming" although it is online.

**H. Dependency on young primitives.** Covenant, ZK and sequencing opcodes are Active but KIP-21 was edited on 2026-11-01. Whether the complete KSD update transaction (proof verification, commitment access, covenant state) fits mass limits is UNVERIFIED, as is the assumed 3-minute proving delay. Groth16 is not quantum-safe (KIP-16 says so) and the choice between Groth16 and STARK is open.

**I. Funding and governance of the campaign.** One named person. 72% of the target (3,600,000 KAS) is for "development fees, relationship building, travel, promotion and marketing, representation of Kaspa", not itemised. No multisig or escrow is described for the collection address; refunds, if the target is missed, depend on the operator ("No guarantees can be made"; exchange senders must email a withdrawal proof). Contributions are concentrated: the largest single receipt is 200,000 KAS (about 31% of the balance); whether any large inputs are insider-linked is UNVERIFIED. Raising is at 12.8% of target 23 days after the first receipt, at a roughly steady pace (about 229k KAS from 2026-10-23 to 31 Oct, about 25k/day; about 411k in November to the 15th, about 27k/day). The site promises month-end publication of outgoing transactions; none exist yet, which is consistent with no outflows. The funds are unspent on chain.

**J. Related third parties.** A separate `$KDOLLAR` meme token site (kdollar.space, run by a third party, says it is not affiliated with the development team) claims its trading fees go to a "KaspaDollar Initiative wallet". UNVERIFIED, and it was not checked whether that wallet is the collection address. This matters because meme-token fees could be mixed into the displayed total.

**K. Discrepancy between my evidence passes: resolved.** One pass reported 11 commits (latest 2025-01-06), another 6 (latest 2026-06-23). The independent reviewer explained it: the account was renamed (`starkbamse` to `saefstroem`, same account id), so a filter by the current login shows 6 and the full history shows 11. Both passes were incomplete in different ways.

## 5. Things I could not check

- X profile of @KaspaDollar and @asaefstroem (HTTP 402): age, followers, history.
- Wayback Machine (HTTP 429): site history and any changed or removed claims.
- Domain registrant (redacted); private repositories; non-GitHub hosting; any KSD code under another name.
- Official Kaspa channels (Reddit, Telegram, Discord, forum) were not reachable.
- Primary texts of Sutton's X post and Medium article.
- Price history (KAS drawdown claims on the site), third-party market statistics on /why-stablecoins, primary texts of Maker, Liquity, Terra, Slinky, BIP-100 characterisations, and the negative claim "no deployed system took its price from the host chain's own miners without a consensus change".
- MiningBoard source of the 32.7%/57.1% figures.
- Figures and charts of the whitepaper (text snapshots only).
- The year of the audit and mainnet dates (not written on the site).

## 6. Statements the review does not make

Nothing here says the project is a scam, nor that it is sound. Positive facts: authorship of KIP-16 is true, the on-chain counter matches the site, funds are unspent, refund terms are published, the maths reproduces, the whitepaper states its own weaknesses (concentration, fall beyond 50%). The negatives are the absence of inspectable artefacts and the issues in section 4.

## 7. Evidence index

`evidence/01-github-code.md`, `02-team-accounts-fundraiser.md`, `03-technical-verification.md`; text snapshots of the five site pages dated 2026-11-15 (wallet address redacted); `03-check.py` / `03-check-output.txt` (recomputation, standard library only); `03-miner-sample.py` / `03-miner-sample-output.txt` (pool-tag sample); raw KIP and commit extracts prefixed `01-`.
