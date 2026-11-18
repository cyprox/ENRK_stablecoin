# Frax Finance — durability review and comparison with ENRK

**Date:** 2026-11-11. **Status:** read-only study. Nothing here is a design
decision: every "idea for ENRK" is a proposal awaiting owner validation.

**Revision note (same day):** first draft was written from docs and the
`staked-frax-erc4626` branch only. After reading the deployed-code repository, the audit
PDFs and the chain, one claim of the first draft is **withdrawn** (see 2.3: frxUSD does
have pause, freeze and owner burn) and several items are now verified rather than
reported.

**Sources read:**
- docs.frax.com (about 35 pages), gov.frax.finance (FIP-188, 419, 428, 430, 432, 441,
  threads 1371 and 3899, 3839), DefiLlama and CoinGecko APIs (2026-11-11).
- Code, cloned and read, nothing executed: `staked-frax-erc4626` (branch `public`,
  2025-08-27), `frax-tokens` (HEAD `e16bfc3`, 2026-04-07), `fraxlend` (2025-11-12),
  `frax-solidity` (legacy FRAX, 2026-11-02).
- Audit PDFs read in full with pdftotext: Zellic (7 Jul 2025, 13 Feb 2026, 19 Oct 2026),
  ChainSecurity (17 Jul 2025), Codespect (26 Oct 2026, **not analysed**), Trail of Bits
  (11 Jun 2021, summary page only).
- Chain, read-only, public RPC (`eth_call` and `eth_getStorageAt` only, no transaction,
  no key), Ethereum mainnet, 2026-11-11.

**Not read / unverified:** frax.com/transparency (JavaScript page, empty); Snapshot
results (FIP-188, 419, 428, 430, 432, 441: pages are JavaScript shells); March 2023
depeg price history (CoinGecko returned HTTP 401); Active Reserve / AMO history; the
Codespect router report; `frax-tokens` Fraxtal and LayerZero contracts; Fraxlend IRM
parameters on docs.frax.finance; incidents (DefiLlama hacks file read only in part, no
Frax entry seen in the part read, not exhaustive); rekt.news.

---

## 1. What Frax is today

Frax renamed its tokens in FIP-428 (March 2025), which confuses data sources:

| Name today | Old name | Nature |
|---|---|---|
| frxUSD | (new, FIP-419, Dec 2024) | Fiat-redeemable stablecoin, custodial reserves |
| Legacy Frax Dollar (L-FRAX) | FRAX | The fractional-algorithmic stablecoin, being wound down |
| FRAX | FXS | Commodity asset: Fraxtal gas, veFRAX staking |
| sfrxUSD | | Yield-bearing wrapper of frxUSD |
| FPI | | CPI-indexed stablecoin; **FIP-448 (Nov 2026) proposes winding it down** |

**frxUSD design.** Reserves are described as BUIDL, USTB, JTRSY, WTGXX, AUSD held by
regulated custodians and managed by Frax Inc under a DAO delegation (FIP-432, July 2025;
the DAO can revoke it by vote). Minting and redeeming go through one `frxUSDCustodian`
contract per reserve token, each with a `mintCap`. The peg is 1:1 redemption, not an
algorithm; no price oracle in the 1:1 path. Docs state there is no guarantee of redeeming
in any particular asset.

**Migration policy (FIP-430, Apr 2025).** The DAO "will no longer guarantee 1-to-1
migration" from Legacy FRAX; two separate balance sheets (Legacy FRAX and frxUSD);
FXB bonds redeem in Legacy FRAX; "under no conditions will there be new frxUSD minted
into sfrxUSD". FIP-441 (Jan 2026) caps FRAX supply at 143 M, removes the 3 % tail
emission and says Legacy FRAX is winding down "over months".

**sfrxUSD yield.** Capital is allocated by governance to venues (Ethena, Superstate,
Aave, Curve, Convex, Euler, Fraxlend, Morpho, Gearbox, Royco...). FIP-447 proposes
raising the Aave v4 cap from 20 M to 50 M. Docs advertise "4.1 % APY" (undated).

## 2. Durability assessment

Summary: frxUSD is an issuer-controlled, RWA-backed stablecoin. Its code is audited
and its upgrade path is better than average (multisig plus a 24 h timelock), but it
carries explicit freeze, pause and burn powers, its reserves cannot be reconciled from
the chain alone, and its supply, token and product set are contracting.

### 2.1 Market data (2026-11-11)
- frxUSD: CoinGecko 94.5 M supply (price 0.999995); DefiLlama 91.1 M (-10.5 % in 30
  days). Legacy FRAX: CoinGecko 219.2 M vs DefiLlama 140.2 M (-7.6 % in 30 days); gap
  unexplained. FRAX (ex-FXS): -80.5 % in a year, all-time low 0.2166 on 2026-11-08.
- On chain, Ethereum frxUSD `totalSupply` is 85.25 M (DefiLlama shows 74.8 M on Ethereum;
  gap unexplained). sfrxUSD on Ethereum: 30.35 M shares, 37.02 M frxUSD of assets (price
  per share about 1.22).
- Aggregator extremes only (no depth): frxUSD low 0.97622 (2025-02-17), high 1.088
  (2026-04-12). The March 2023 SVB/USDC depeg history was **not** obtained.

### 2.2 Positives
- No algorithmic peg in frxUSD; 1:1 redemption path.
- **Upgrade path is constrained on chain.** The frxUSD proxy admin's owner is a timelock
  with `delay()` = 86,400 s (24 h), administered by a Safe v1.3.0 with 4 signatures out of
  7 (the same Safe is frxUSD's `owner`). The frxUSD implementation read from the proxy
  slot equals the implementation Zellic matched to source on 2026-10-28.
- Audits (section 4): no Critical or High in any 2025-2026 Frax report read; Zellic
  verified deployed bytecode for Ethereum frxUSD and sfrxUSD.
- Per-custodian mint caps (on chain: USDC custodian cap 400 M, WTGXX 25 M, USTB 5 M,
  BUIDL and USDB 100 k each).

### 2.3 Concerns
1. **Freeze, pause and burn powers (correction of the first draft).** The deployed token
   source (`frax-tokens`, `FrxUSD2.sol`) has `isPaused`, a `freezeMany`/`freeze` function
   for the owner and delegated freezers, and **`burn` / `burnMany` where the owner
   burns tokens from arbitrary accounts**; `_update` lets the owner bypass pause and
   freeze. Zellic (Jul 2025, 3.2) and (Oct 2026, 3.13) discuss these roles, including
   that freezing `address(0)` blocks every non-owner mint, burn and bridge operation.
   My first draft said "no pause, blacklist or freeze": that was true only of the older
   `staked-frax-erc4626` branch and is withdrawn. On chain: `isPaused()` = false;
   `isFreezer(owner)` = false (the owner can freeze directly).
2. **Reserves cannot be reconciled from the chain alone.** Read on the five custodian
   contracts listed in the docs: USDC custodian `frxUSDMinted` = 277.3 M against 0.54 M
   USDC held; WTGXX 2.0 M minted vs 14.6 M WTGXX tokens held; BUIDL 0 minted vs 15.9 M
   BUIDL held; USTB 0 minted vs 0.998 M USTB (unit price not read); USDB 1.5. Tokens held
   in these five contracts total roughly 31 M units (plus USTB), against 85.25 M
   frxUSD on Ethereum. This is not proof of under-collateralisation: the docs say backing
   sits with custodians managed by Frax Inc, and the counters and balances move
   independently of each other (the RWA coordinator and `shuffleToRwa` move reserves out).
   It does mean the backing is not verifiable from these contracts, and the
   `frxUSDMinted` counter (277 M) is larger than total supply for reasons I could not
   establish. The custodian addresses Zellic lists (e.g. the USDC one) are not minters
   and have cap 0, so they are not yet active.
3. **Custodian owner can remove backing.** `recoverERC20` (owner only) transfers any
   token, including the active backing, to the owner without reducing `frxUSDMinted`.
   Confirmed in code and listed by Zellic (Oct 2026, 3.8) as an explicit "trusted
   custody" assumption (rated Informational; they recommend refusing the backing token or
   limiting to a surplus above a liability floor). Not fixed in the version I read.
4. **sfrxUSD upgrade path is weaker.** The sfrxUSD proxy admin's owner is a Safe with
   3 signatures out of 5. I found no timelock in that chain (I only checked the owner's
   type and threshold, not every storage slot).
5. **The registered minters include the 24 h timelock itself** (the address of the proxy
   admin's owner appears in the frxUSD `minters_array`), next to the five custodians and
   three other contracts I did not identify. The token imposes no cap on a minter: caps
   live only in the custodians.
6. **Contracting business.** Supply -10 % in 30 days, FRAX token -80 % in a year, FPI
   proposed for wind-down, Legacy FRAX winding down, "viable borrower economics were
   not" (IRM thread 3899: the sfrxUSD/frxUSD Fraxlend pair has zero-utilisation rate
   cut from 3.36 % to 1.50 %, goal 179 k$ borrowed).
7. **Bad-debt precedent.** Illamalend WFRAX market on Fraxtal: proposal estimates under
   100 k$ (offers 95 k crvUSD), a comment estimates about 140 k crvUSD. No decision seen.
8. **Docs inconsistencies:** two official pages give different Ethereum "frxUSD"
   addresses; I resolved it on chain: `0xCAcd...6E29` is frxUSD ("Frax USD") and the
   other page lists the Legacy FRAX address under the frxUSD label. Also: "daily" vs
   "weekly" sfrxUSD distribution; chain counts 20+ / 26 / 23; "fully backed by tokenized
   Treasury funds" while USDC and USDB are accepted mint assets; the docs date the two
   Zellic stablecoin reports to October 2026 while one PDF is dated 13 Feb 2026.
9. **Test coverage (Zellic Oct 2026, 4.2):** of 2,503 behaviour markers, 582 were
   matched to a qualifying test; the rest are not proof of absence of tests.

### 2.4 Code facts from the earlier branch (`staked-frax-erc4626`, not the deployed one)
- `StakedFrxUSD2.minter_burn_from` calls `_burn` with no allowance (any minter can burn
  any holder's sfrxUSD); `FrxUSDCustodian.setMintRedeemFee` uses `||` where `&&` was
  meant; `setMintCap` has no upper bound; sfrxUSD price per share is
  `stored * exp(rate * elapsed)` with a timelock-set rate and the comment
  `// CHECK THIS MATH!!!` six times. Zellic (Jul 2025, 3.5) also flags the fee check.

## 3. Audit record (PDFs read)

| Report | Date | Result |
|---|---|---|
| Zellic, FraxNet / frxUSD / Custodian / RWARedemptionCoordinator | 7 Jul 2025 | 0 Critical, 0 High, 1 Medium (missing slippage check in `shuffleToRwa`), 5 Low, 2 Info. Low items include owner unable to burn frozen tokens, unvalidated `maxSlippage`, wrong fee check. |
| ChainSecurity, Frax Upgrade (sfrxUSD, FraxtalERC4626MintRedeemer) | 17 Jul 2025 | 0 Critical/High/Medium, 10 Low (6 corrected, 1 specification changed, 3 risk accepted: ERC-4626 breakage, rounding, proxy name mismatch). Code corrected: stale vs fresh oracle price usable by caller. |
| Zellic, Frax (USD Stablecoin) | 13 Feb 2026 | 0 Critical/High, 2 Medium (branded custodian passes shares where assets expected for non-18-decimal collateral; cross-chain amounts truncate to zero), 4 Low, 4 Info. |
| Zellic, frxUSD Ecosystem | 19 Oct 2026 (bytecode match 28 Oct) | 20 findings, 0 Critical/High/Medium, 7 Low, 13 Info. Covers custodians, FrxUSD2/3, SfrxUSD2/3, OFT adapters, rate limiter, Tempo chain integration, router. |
| Codespect, Fraxswap Router Multihop V2 | 26 Oct 2026 | Not analysed. |
| Trail of Bits, Frax Finance (legacy FRAX) | 11 Jun 2021 | 27 findings: 7 High (mostly from Aragon's voting contract), 0 Medium, 5 Low, 11 Info. |

The audits cover contracts, not the custody of the reserves ("key custody" is an explicit
non-goal in Zellic's reports). Bug bounty: lowest of 10 % of the exploit and 10 M$, paid
in frxUSD+FRAX, proof of concept required, issues needing admin keys excluded.

## 4. Fraxlend and legacy FRAX (code read)

**Fraxlend** (isolated pairs): `liquidate(sharesToLiquidate, deadline, borrower)` is
permissionless, with **no close factor** (any share amount). Liquidation uses the *low*
price of a dual oracle; a full ("clean") liquidation pays `cleanLiquidationFee` (docs
default 10 %), a partial one 90 % of that; an access-control flag `isLiquidatePaused`
can stop it. When the leftover collateral is non-positive, **the borrower's remaining
debt is written off against the lenders' `totalAsset`** — bad debt is socialised to
suppliers, not to other borrowers (the opposite of Monolith). Max LTV is immutable per
pair (about 75 % volatile, 90 % stable).

**Legacy FRAX collateral ratio** (genesis defaults in `Frax.sol`): `global_collateral_ratio`
starts at 100 %, `refreshCollateralRatio()` moves it by `frax_step` = 0.25 % per call,
with a 1 h cooldown and a ±0.5 % price band around 1 $, lowering the ratio when the
price is above the band and raising it below. The ratio was 87.25 % in May 2022 (forum)
and 92 % in Feb 2023; FIP-188 proposed a permanent 100 % target "retiring the
algorithmic backing". The date at which it reached 100 % was not found. Values could
have been changed after genesis.

## 5. Comparison with ENRK

| Topic | Frax (frxUSD) | ENRK (per repo state) |
|---|---|---|
| Backing | Custodial RWA / fiat-equivalent reserves | Over-collateralised vaults |
| Peg | Redemption against reserves | Oracle price UTXO, liquidation, loss waterfall |
| Trust | Issuer, custodians, KYC edge; owner can freeze, pause, burn, recover backing | Covenant-enforced; no issuer reserves |
| Upgrade | Proxy; 4-of-7 Safe + 24 h timelock (frxUSD), 3-of-5 Safe (sfrxUSD) | Not implemented; execution layer decided: Kaspa L1 (owner, 2026-11-13) |
| Bad debt | Fraxlend: lenders absorb; stablecoin side: case-by-case DAO | Waterfall (cascade not yet implemented per audit; loss-absorption structure is an open owner decision, the waterfall is the current candidate) |
| Liquidation | Fraxlend: no close factor, fee 10 % clean / 9 % dirty, pausable | 180 vaults in one tx on one price (TN10) |
| Footprint | 26 chains via LayerZero / CCTP | One chain, no bridge |

Frax's current stablecoin does not solve the problem ENRK solves (a decentralised,
collateral-backed stablecoin with no issuer). Its value to ENRK is as a counter-example
and for a few mechanics.

## 6. Ideas for ENRK — proposals only, none validated

1. **State the opposite of Frax's admin powers as design invariants:** no freeze, no
   pause, no owner burn from arbitrary accounts, no sweep of backing. These are
   precisely the powers Zellic lists on frxUSD; a covenant can refuse them by
   construction. Candidate property to write into the specification. (ENRK's frozen circuit breaker does pause mint and burn; whether it may ever act on liquidations is an open owner decision, ECONOMICS-VERIFICATION section 9 item 2.)
2. **Constrained upgrades if any upgrade exists:** the frxUSD pattern (multisig behind a
   24 h timelock) shows a minimum; ENRK, being UTXO-based, may not need upgrades at all.
3. **Per-family issuance caps** (custodian caps) compared with ENRK's `MinterProxy` and
   Q1c oracle-binding question; Frax's caps are owner-settable and unbounded, ENRK's
   should be covenant-fixed (the Argent issuance-cap example is bypassable, ECONOMICS-VERIFICATION P11; the cap design is open).
4. **Fraxlend bad-debt rule** (write-off against suppliers) as a data point next to
   Monolith (write-off against all borrowers) when choosing who absorbs a loss.
5. **No close factor plus clean/dirty fee** (full liquidation pays more) as an incentive
   shape to compare with ENRK's multi-vault liquidation.
6. **Legacy FRAX collateral-ratio mechanism** is a catalogue of what ENRK should not
   implement: a controller moving the ratio by price, which Frax itself retired.
7. **Publish what Frax does not:** caps, fees, backing, key holders. The reserve
   reconciliation problem (2.3 item 2) is the argument for on-chain verifiable backing.
8. **Do not borrow:** KYC edge, delegation to an issuing company, custodial reserves,
   multi-chain bridge surface, a yield curve set by an admin rather than measured.

## 7. Next steps (need owner go)

- Read the Codespect report and the `frax-tokens` Fraxtal and LayerZero contracts.
- Get Snapshot results and the March 2023 price history (needs another data source).
- Reconcile reserves: identify where the USDC behind the 277 M counter sits (custodian
  attestations, RWA coordinator flows) and price USTB.
- Check the sfrxUSD proxy chain for timelocks (all admin slots), and the Fraxtal
  frxUSD owner.
- Run the Frax test suites (Foundry is now installed) on the cloned repositories.
