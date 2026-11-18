# P2 Rust audit - contracts/igra/src (read-only, 2026-11-09)

Status 2026-11-17: owner decisions since this report: execution layer is Kaspa L1, Igra not retained (2026-11-13); stability fee recurring, fees never burned (a burn option is excluded). Passages on Igra and on burning are kept as history.
Test run: `cargo test --offline` (CARGO_TARGET_DIR in scratchpad): 119 passed, 0 failed, 0 ignored. Claim "119" confirmed.
Per module: kaspa_tokens 24, oracle_feeds 16, circuit_breaker 13, kaspa_adapter 11, peg 11, stability_pool 11, types 10, liquidation 7, lib 6, errors 5, vault 5.
All paths under /Users/simoes/ENRK_stablecoin/contracts/igra/src. Note: `contracts/igra/target` exists in repo dir (pre-existing, not touched).

## (a) Deviations from FROZEN_PARAMETERS / stale values
1. [BLOCKER-spec] Auction floor 85% instead of 75% (FROZEN s4: the "single most consequential revision"; at 85% nothing clears past -61%).
   types.rs:80 `end_price: u8, // 85%`, types.rs:106 `end_price: 85`, lib.rs:68 `LIQUIDATION_END_PRICE: u8 = 85`, liquidation.rs:3-15 docs ("85%", "free profit 5-15%").
   Tests assert only start>end (lib.rs:164), so a stale floor passes. Rec: set 75 at the 3 places, add a test pinning 75.
2. [important] Fee split 80% Stability Pool / 20% Treasury (types.rs:119-120,141-142; lib.rs:71-72,98; stability_pool.rs:6,49,58). FROZEN s6: treasury 20% until 2.5M cap then 0% forever; no pool share; Stability Pool is "fix or remove" (s9, s10.5). No treasury cap constant/logic exists anywhere (grep treasury: only these constants).
3. [important] Fee denomination: spec = KAS taken from vault collateral (FROZEN s6, so enrk_supply == sum debt_enrk). Code adds fee to ENRK debt: vault.rs:136,139 (`debt_enrk += amount + fee`), vault.rs:217 for kFIAT. The returned fee is not minted/routed anywhere: the debt exists with no corresponding token supply, so supply != sum(debt) (invariant broken by design).
4. [important] Mint fee applied to kFIAT too (vault.rs:191); spec lists one mint fee 2%, ok, but the fee counts toward the 30% cap numerator (vault.rs:200) while TokenLayer cap ignores fees (two inconsistent cap definitions, see (g)).
5. [important] Redemption/seniority absent (see c). Redemption fee const exists only (types.rs:118, lib.rs:75).
6. [minor] Liquidation fee 4% / mint 2% / redemption 1% / ICR 200 / MCR 150 / peg weights 40-30-20-10 / breaker 10% & 360 min / duration 120 / kFIAT cap 30 : match.
7. [important] Peg clipping [0.1,5.0] present (peg.rs:65) but it is also applied to each input index (peg.rs:113, kaspa_adapter.rs:94, oracle_feeds.rs:77,140) = silent saturation of oracle failure into a plausible price. Stale feeds only warn and proceed (oracle_feeds.rs ~L300-312: `warn!("Energy feed is stale")` then continues) = fail-open; breaker not tied in.
8. [important] Circuit breaker is never invoked: `require_active`/CircuitBreaker not referenced from vault.rs, liquidation.rs, stability_pool.rs (grep). The "override: none" breaker protects nothing.
9. FROZEN s9: attempt_buyback "computes a cost, never debits it" confirmed: stability_pool.rs:118,127,136 (cost computed, only enrk_balance reduced; no bid, no counterparty). Pure burn of the pool's own balance. Known; spec says fix or remove.

## (b) Functions with no test (grep for call sites; only call sites inside test modules or other code counted)
VaultManager (vault.rs): tests exist for create_vault, get_vault, mint_enrk (once, asserts only debt>100), deposit_collateral, total_enrk_debt.
- mint_kfiat vault.rs:170: ZERO callers/tests. (kaspa_tokens.rs:619+ tests are TokenLayer::mint_kfiat, a different function.)
- burn_enrk vault.rs:245: zero tests (kaspa_tokens.rs:726 is TokenLayer).
- burn_kfiat vault.rs:286: zero tests (kaspa_tokens.rs:710,753 are TokenLayer).
- withdraw_collateral vault.rs:358: zero tests.
- close_vault vault.rs:408: zero tests.
- get_liquidation_candidates vault.rs:435: zero tests.
- also untested: total_kfiat_debt, total_collateral, vault_count, calculate_fee (only indirectly via mint_enrk), VaultManager::new failure paths (kfiat cap bounds vault.rs:40).
LiquidationManager: submit_bid (liquidation.rs:171), finalize_expired_auction (:273), get_auction_price (:116), calculate_fee: zero tests. Only start, price progression, calculate_collateral_for_bid, listing, expiry tested.
Cap test gap: the 30% cap on the VaultManager path is untested; 24 tests cover TokenLayer only.
Severity: important (money-moving paths with the most bugs below have no tests).
Coverage of vault.rs overall = 5 tests for 568 lines incl. 12 public mutators.

## (c) Seniority cascade and redemption
NOT IMPLEMENTED. grep redeem|redemption|senior|cascade|waterfall: only error variants (errors.rs:98-108), fee constants, comments (types.rs:199 "senior tranche", vault.rs:5-12 docs "ENRK is redeemable", "kFIAT bears liquidation losses first"). No function redeems; no lowest-ICR ordering; no 100% min ICR guard; no loss waterfall. finalize_expired_auction (liquidation.rs:285-290) is a stub: "For this skeleton, we just remove the auction" - collateral and debt vanish from accounting; vault status never moves to Liquidating (grep: Liquidating never set); nothing burns the debt after submit_bid.
Severity: BLOCKER for any claim that mechanisms #1 (redemption) and the loss cascade exist. Docs (vault.rs:11-12, lib.rs:5) overclaim.

## (d) submit_bid dimension inconsistency - CONFIRMED (blocker)
liquidation.rs:202-219: `required_bid = debt_f64 / (kas_price * price_multiplier)` is KAS units (debt in stablecoin / price). `bid_f64` is compared to it directly (:213) but bid_amount is documented as stablecoins (doc at :128 "bid_amount_in_stablecoins"; :222 passes it to calculate_collateral_for_bid which treats it as stablecoin). So the sufficiency check compares stablecoin vs KAS.
Additional errors in same function:
- Direction inverted: calculate_collateral_for_bid (:152-153) `kas = bid * pct/100 / kas_price`. A descending-price auction should give MORE KAS per stablecoin as price falls: kas = bid / (kas_price * pct/100). Code gives less. required_bid (:207) correctly divides by pct, collateral multiplies; mutually inconsistent.
- Bid can exceed requirement and still receive (bid*pct/price) up to all collateral; no partial fill, no refund, no change; any single bid settles the whole auction and deletes it (:233).
- Fee computed on bid (:230) but never deducted from collateral/bid or routed; vault debt not burned, vault status not updated, surplus collateral not returned to owner.
- No bid-vs-debt cap (bid > debt accepted).
- `bid_f64 as u64` display only.
- Uses SystemTime::now inside (:186) -> non-deterministic, untestable (explains zero tests).
Rec: rewrite in integer fixed-point, one unit system, partial fills, explicit settlement; test.

## (e) Two ICRs for the same vault - CONFIRMED
calculate_icr takes kfiat_price (types.rs:216). vault.rs:142 (mint_enrk) and :266 (burn_enrk) hardcode `1.0`; mint_kfiat (:220), burn_kfiat (:311), withdraw_collateral (:389), get_liquidation_candidates (:445), start_liquidation (liquidation.rs:62) use caller-supplied kfiat_price. A vault with debt_kfiat>0 and kfiat_price != 1 yields different ICR depending on the path (e.g. mint_enrk passes at 1.0 while liquidation sees <150%). Root cause = KFIAT-DEFINITION-GAP.md: kfiat_price is never produced by anything. Severity important/blocker (liquidation vs mint disagreement; also the same applies to enrk_price: caller-supplied everywhere, never from peg.rs).
Also peg unit: collateral_value = kas * kas_price, debt = enrk * enrk_price; ENRK pegged to kWh index while kas_price in unspecified units (USD?) - unit of account undefined.

## (f) f64 usage (grep count of "f64" lines): types 16, vault 27, peg 14, liquidation 19, stability_pool 9, kaspa_adapter 12, oracle_feeds 24, circuit_breaker 1, kaspa_tokens 1 (comment only: module is integer-only, claim verified).
RISKY (money/collateral/ICR/cap):
- types.rs:216-226 calculate_icr: BigInt->f64 (loses precision > 2^53 ~ 9e15 base units, = 90M tokens at 8 dec; to_f64 on huge BigInt gives inf not error; `unwrap_or(0.0)` turns failure into ICR 0 or INF debt==0 -> INFINITY). Returns percent as f64 then truncated `icr as u16` (vault.rs:143,146,221,224,267,312,390; liquidation.rs:65) - NaN -> 0, saturates at 65535.
- types.rs:230 is_under_collateralized: f64 compare against MCR (liquidation trigger decided by float).
- vault.rs:204-208 kFIAT cap ratio via f64 (the same invariant is exact BigInt in kaspa_tokens.rs:311-318,395-402). Cap check can pass at boundary or fail spuriously; `kfiat_ratio as u64` truncation.
- vault.rs:457-471 calculate_fee: bps as f64, debt as f64, `fee_f64 as u64`: truncates (rounds DOWN, in user's favour: should round up), saturates at u64::MAX, precision loss > 2^53. Same in liquidation.rs:301-315, stability_pool.rs:58-71 (deposit_fees: 80% share by f64; share + remainder != total, 20% treasury unaccounted).
- liquidation.rs:148-161,202-219 bid/collateral math f64 `as u64`.
- stability_pool.rs:114-136,175-188 cost/buyable f64.
- types.rs:250-259 auction price: f64 + `as u8` truncation (price steps down early; minor).
ACCEPTABLE (oracle indices / peg, not balances): peg.rs weights/index (indices are ratios clipped to [0.1,5]), kaspa_adapter.rs 12 / oracle_feeds.rs 24 (hashrate, USD/kWh, normalised indices). But risk: f64 non-determinism across platforms if ever run on-chain; and PegPrice.value feeds prices consumed by vault paths.
peg.rs:86-96, circuit_breaker.rs:79-80: f64 for deviation - acceptable type but see (g) for cast bugs.
Rec: replace money/ICR/cap/fee with BigInt fixed-point (basis points, price as scaled integer); keep indices f64 off-chain only.

## (g) Other findings
G1 [important] peg.rs:94-96 is_peg_healthy: `Self::peg_deviation(peg).abs() as u8` where peg_deviation is i16 (truncated, :89). i16 -> u8 `as` WRAPS: deviation 256% (peg 3.56) -> 0 -> "healthy". Also truncation: 10.99% -> 10 -> healthy at threshold 10.
G2 [important] circuit_breaker.rs:120 `((now - last_oracle_update_seconds) / 60) as u16`: u16 wraps at 65536 min (45.5 days): oracle dead 45.5 days -> downtime 0 -> no pause. Also `now - x` u64 underflow: panic in debug / wrap in release if timestamp is in the future (-> huge, spurious pause or wrap).
G3 [important] circuit_breaker.rs:79-90: `deviation.abs() as u8` saturates (fine) but NaN -> 0 = healthy; truncation 10.9 -> 10 not > 10. Breaker also has no way to ever unpause (by design) but is not wired (a8).
G4 [important] Unchecked u64 subtraction on time: types.rs:249 and :264 (`now_seconds - self.started_at_seconds`), oracle_feeds.rs ~L125-133 is_fresh (3 copies) and fetch_all_indices cache (`now_seconds - cached_at`). Panic/overflow if clock skew. peg.rs:175 correctly uses saturating_sub.
G5 [important] burn_enrk/burn_kfiat (vault.rs:264-270, 309-315) require post-burn ICR >= 200% (icr_minimum): a vault at 160-199% cannot repay partially (repayment only improves ICR) - and cannot withdraw below MCR; trapped vault. Also no status check (burn on Liquidating/Closed vault succeeds), burning debt does not require/consume any token (no link to TokenLayer).
G6 [important] close_vault (vault.rs:408-432): returns `VaultZeroDebt` error when debt > 0 (misnamed), never returns/zeroes collateral (status=Closed, collateral_kas retained, no payout), no status check (can re-close), price args unused (`_kas_price`).
G7 [important] VaultManager and TokenLayer are unconnected: debt in vaults (vault.rs) vs supply in kaspa_tokens.rs; mint_enrk in vault does not mint tokens; no invariant `enrk_supply == sum(debt_enrk)`; cap enforced twice with different formulas (vault.rs f64 incl. fees; kaspa_tokens exact excl. fees). KFIAT cap is checked against vault debts at vault.rs:195-198 by summing all vaults (O(n) per mint; also counts Closed/Liquidating vaults).
G8 [important] No reentrancy/atomicity model: functions clone vault, mutate clone, insert (OK) but all state in-memory HashMap with SystemTime::now (vault.rs:74,150,... ~10 sites; liquidation.rs 6 sites): non-deterministic wall clock in a "contract" - not usable on Igra EVM or Kaspa L1; cannot be replayed. No access control: no caller identity on any VaultManager method (anyone can mint/withdraw/close any vault id). Reference-implementation only.
G9 [minor] create_vault accepts any non-empty owner string (vault.rs:63), no address validation (TokenLayer validates via KaspaAddressValidator). `next_vault_id += 1` unchecked (u64, unreachable).
G10 [minor] types.rs:125 `stability_pool_allocation + treasury_allocation` u8 add can overflow (panic debug) for values > 127 each.
G11 [minor] liquidation start_liquidation (liquidation.rs:71-77) blocks a second auction for any existing auction of the vault (including expired ones never finalized -> vault can never be re-liquidated unless finalize called); debt_to_cover snapshot includes kFIAT and ENRK summed without price (stablecoin units mixed, :91).
G12 [minor] kaspa_tokens.rs:458 ratio_percent `to_u8().unwrap_or(100)`: floor % and cap-reporting fine; kaspa_tokens burn uses `to_u64().unwrap_or(0)` in error payload only (cosmetic, 148/steady). OK.
G13 [minor] kaspa_adapter: build_*_tx are string stubs ("tx_mint_enrk_...") not transactions; address validation is prefix-based.
G14 [minor] Documentation overclaims: lib.rs:5 "Five self-regulating mechanisms", vault.rs:11-12 redeemable/kFIAT-first-loss, stability_pool.rs:9-22 buyback - none implemented as described.
G15 [positive] kaspa_tokens.rs: integer-only, exact cap inequality (:311-318,:395,:424-431), checked-then-applied, supply invariant. Best module. Its 24 tests are the real coverage.
G16 [minor/positive] No `unsafe`, few non-test unwrap: all unwrap() are in #[cfg(test)]. Non-test panics = the u64 subtractions above only.

## Summary of severities
Blocker: auction floor 85 vs 75 (a1); redemption + cascade absent, finalize stub (c); submit_bid units/direction/settlement broken, untested (d); two ICRs / kfiat_price undefined (e).
Important: fee denomination/treasury cap/80-20 stale (a2,a3); breaker not wired & wraps (a8,G1,G2); f64 in ICR/cap/fee (f); untested VaultManager mutators (b); trapped-vault burn rule (G5); close_vault no payout (G6); vault/token unlinked (G7); no access control/wall clock (G8); fail-open oracle (a7); time underflow panics (G4).
