# econ-x1b: all-N oracle population refresh at a changed price (testnet-10)

Date 2026-11-11. Testnet-10 only, owner-approved step 1b. Findings and measurements only, no design decision.
Tags: EXECUTED-ON-CHAIN (txid + API mass), EXECUTED-LOCALLY (builder runs the real script engine, MAINNET mass params), COMPILED, DERIVED.
Sources and logs: SP/econ/x1b (oracle.tmpl in a/ and b/, a/oracle_ctl.tmpl, x1b.rs harness copied to SP/w/argent/tests/x1b.rs, drv.py, sc.py, vsc.py, csc.py, ledger.jsonl, logs/local_*.txt, out/*.json). Key file used only through the Rust harness; not printed or copied. Repo untouched.

## 1. Answer to the open question: the accepted input form for a consumed range
The v3 failure ("expects 2 arguments, got 0") came from spending the other population inputs through the leader entry `refresh`. The accepted form: the other N-1 inputs are spent through a no-argument **`delegate follow() consumes { lead: <leader actor> }`** entry; only the first input of the covenant group runs `refresh(sig, new_price)` with `consumes { olds: Follower[0..=N-1] }`. The leader's active input is not part of `olds` (olds.length = N-1). Inputs must be ordered leader first (slot 0), then slots 1..N-1 (a different order is refused). COMPILED + EXECUTED-ON-CHAIN.

Two forms built (price in state, `PriceRoundState {publisher, round, price, slot, n}`, value unchanged, so no storage mass in a round):
- (a) single actor `PriceRound` (leader = slot 0 and followers = same actor; `delegate follow` on the same actor; every UTXO carries the loop code).
- (b) two actors `Leader` (slot 0, refresh logic) and `Follower` (slots 1..N-1, small script). Vault observes `Follower`.
Guards in `refresh` (test constants, MOVE_BPS = 1000 = 10 %): publisher signature; new_price > 0; new_price within +-10 % of the old price; leader slot 0; **olds.length + 1 == n** (n in every state, conserved); news.length == olds.length(+1); per consumed sibling: same publisher, **same round**, **same price**, **slot == i + 1**, same n; value of each output equal to its input; every output gets round + 1, new price, same slot, same n. `delegate follow` also requires lead.round == round. Test-only publisher `drain` entry (leader + followers, `emits none`) was added to each contract and used for the final recovery.

## 2. Local cases (EXECUTED-LOCALLY, N = 4, both forms; logs/local_a_n4.txt, local_b_n4.txt; N = 8, 16, 32 also run)
ACCEPT: +5 %, -10 % and +10 % (bound edges). REJECT (script engine, "script failed: script ran, but verification failed"): wrong signer; +10.01 %; -10.01 %; price 0; output price differs from the argument; one output at another price; one output with round not +1; missing sibling (last, and a middle one); N inputs but N-1 outputs; extra output sibling (N+1 outputs); duplicated output slot; duplicated input slot; mixed rounds (last sibling at round-1, sibling at round+4); mixed prices; one sibling value changed; n changed in one output; inputs out of order (variant a: engine refusal; variant b: builder "unknown entry `Follower::refresh`"). Extra INPUT sibling (N+1 inputs): refused by the builder pre-check "requires between 1 and 4 same-covenant inputs, found 5" (the script bound MAXF is the same limit; not reproducible as a node refusal because the builder will not emit that tx). Drain: publisher ACCEPT, wrong signer REJECT.
Not all refusals above can be individually attributed to one guard from the engine message (it is the same generic failure); each case differs from the positive case in exactly one aspect.

## 3. On-chain refresh measurements (EXECUTED-ON-CHAIN; every refresh also changed the price: 1.00 -> 1.05 -> 0.9975)
Mass: API-reported mass = compute mass. Transient/storage from the same MassCalculator the node uses (local, MAINNET params). Fee = exact floor 100 x max(compute, transient/2) + 200 sompi, accepted by the node (storage mass is NOT part of the floor). Value per UTXO = 15e6 x N sompi (>= 8e6 x N). Fee input about 3.5 x the UTXO value, storage 2.5k - 91k, always under 500k. Confirmation = submit to is_accepted (7 s typical; outliers 17-85 s on this testnet).

| Form | N | refresh txid (round 1) | API mass (compute) | transient | storage | fee (sompi) | confirm s |
|---|---|---|---|---|---|---|---|
| b | 4 | a9ed67b84078f4cd8ed0278b90a7dd8d195dac6b9171c1e45d2dd90bc2df23f6 | 17,346 | 43,224 | 91,475 | 2,161,400 | 8.5 |
| b | 8 | 251b9999acf2aa5e5bebcd0a81ab98af6445f48f1f16d2ccd4385714d61174ad | 38,806 | 91,544 | 35,474 | 4,577,400 | 7.1 |
| b | 16 | ef1682433fcd59399b0a2bba85428a17ace320a8a798556fab95c1d938475e5e | 96,443 | 188,252 | 11,852 | 9,644,500 | 7.2 |
| b | 32 | 5fd2a644257241392dba7fb8e0856ede9faca56b777b95a5179e4611419e0e31 | 270,508 | 381,632 | 4,089 | 27,051,000 | 7.2 |
| b | 46 | ec433b4681e2f8c67717d622604f18851bf52f7e8438e48912ae1f65e41acdf4 | 487,182 (97.4 % of 500k) | 550,808 | 2,503 | 48,718,400 | 6.9 |
| a | 4 | f3d99239113dfe6503fc3a1d39f614788e83a44350e1f5bf886f3c79a0d7d218 | 21,433 | 67,172 | 91,503 | 3,358,800 | 6.8 |
| a | 8 | 8545b083bce4cff73b3364413a3ebd7dcdc3d1ceed36a59f0ce66a6f87732bdb | 75,293 | 265,092 | 35,601 | 13,254,800 | 52.2 |
| a | 15 | 3808fb6e253d7bb120171bd584160d4b00f0e5217cda3ed3572cb7774f658969 | 254,737 | 929,308 (92.9 % of 1M) | 13,452 | 46,465,600 | 7.5 |

Each size also ran a second refresh (same mass), genesis and drain (txids in ledger.jsonl): e.g. b46 second refresh abe472126f52..., drain a6739c1c83a7... (447,778); b32 drain 662d75db1017... (244,002); a15 drain e143806130678050... (238,077).
Genesis (N price UTXOs in one tx, EXECUTED-ON-CHAIN): b4 89feef35... 3,454; b8 94187a17... 5,282; b16 9f14f5a3... 8,938; b32 b172520d... 16,250; b46 4c6032a1... 22,648; a4 b87a5c44..., a8 5644683b..., a15 5102631a...; storage mass about 297k-303k with the genesis input sized N x value + 0.3 TKAS (value 15e6 x N).

Largest N before a limit (EXECUTED-LOCALLY refusals with exact builder messages, MAINNET params; the same limits are node-enforced):
- (a) single actor: N = 15 passes (on chain), **N = 16 refused: "transaction transient mass 1057220 exceeds limit 1000000"**. Binding: transient (the whole loop code is in each sigscript; about 62k transient per input at N = 15).
- (b) leader/follower: N = 46 passes (on chain, 487,182), **N = 47 refused: "transaction compute mass 507273 exceeds limit 500000"**; N = 48 522,964, N = 64 853,920, N = 96 1,751,132 refused likewise. N = 128 does not compile: "compiled redeem script is 274369 bytes, exceeding the 250000-byte signature-script limit".
- Compute for (b) is quadratic in N (array append in the loop): fit c(N) = 3,602 N + 151.6 N^2 (reproduces 96,443 at 16, 270,508 at 32 and 487,182 at 46 within 0.2 %). Transient (b) is linear, about 12.0k per input (so about 83 inputs if compute were not binding). DERIVED ceiling: (b) 46, (a) 15. A refresh covering the 640-UTXO population of earlier tests is not possible with this form; population N is bounded by about 46.
- Marginal cost per extra sibling (b, 32 -> 46): about 15.5k compute, 12.1k transient, versus the `use`-ladder constants of earlier tests (759 / 1,556): an all-N refresh is about 20 x more expensive per UTXO than a value-preserving `use` round.

## 4. Stale-sibling attack (item 2)
(i) Old pre-refresh sibling through a vault read, EXECUTED-ON-CHAIN (b, N = 8, vault: collateral 1.6 TKAS, debt 1e8, ICR 160 at price 1.0). Price path 1.00 -> 0.90 (round 2, vault liquidatable, ICR 144) -> 0.99 (round 3, ICR 158.4, not liquidatable) -> 0.891 (round 4, ICR 142.6).
- ATTACK 1: liquidate reading the OLD round-2 sibling (price 0.90, would pass the script) after the round-3 refresh. Built locally (script passes), submitted: node REFUSED: "Rejected transaction 56bd5e4b33e6496728c247af2e5c108789a7b443dd4b20f76192f9c39f69330a: transaction 56bd5e4b... is an orphan where orphan is disallowed".
- ATTACK 2: plain `use` of the round-1 sibling (slot 1) after refreshes: same node message (tx baf897e862fe...). ATTACK 3: `use` of a round-3 sibling after the round-4 refresh: same message (tx 7cb63f3de13c...).
- The node's text is its generic missing-input message ("orphan"), not a "double spend" text; the cause is DERIVED: the refresh transaction consumed all N old outpoints, so an old sibling does not exist any more. Impossible by consumption, as expected.
(ii) Unrefreshed sibling: the guarded `refresh` makes it impossible to build (see 2: missing sibling, N-1 in and out, rejected by `olds.length + 1 == n`; a middle sibling left out also rejected). Guard: **the all-N completeness check** (`olds.length + 1 == n`, n copied into every state, plus `slot == i + 1` which excludes duplicates and substitutes, plus equal round and price among consumed siblings). Rejection is EXECUTED-LOCALLY (the builder will not emit an invalid tx, so no node message exists).
(iii) NEGATIVE CONTROL (the attack with the guard removed), EXECUTED-ON-CHAIN, variant a N = 4 with an extra entry `refresh_partial` that is identical but lacks the `n`/slot checks (SP/econ/x1b/a/oracle_ctl.tmpl; never to be used as a design): partial refresh of slots 0,1 to 0.90 (tx 9521f6027296ae1b960acdc5c23deb7b3332ca62bd684a01ab83a6fd2b8624eb); population is now {0,1} at round 2 price 0.90 and {2,3} at round 1 price 1.00. Vault (collateral 3.0 TKAS, debt 1.0) `withdraw` of 1.0 TKAS (needs ICR >= 200): reading the FRESH sibling slot 1: REJECT locally (ICR 189); reading the STALE sibling slot 2 (price 1.00): **ACCEPTED and confirmed on chain, tx 56f30dfc3d18a876d8708c11df802fd5fe51f1cb2288ace0fe2c101659c38cb1, mass 11,990**. So without the completeness check a vault reads a price that is two rounds old, forever (the stale siblings could not even be refreshed again by the guarded entry because it requires equal round and price among consumed siblings, so they stay stale until drained one at a time, which needed a solo `drain_one`).

## 5. Vault read after a price-changing refresh (item 3), EXECUTED-ON-CHAIN, variant b N = 8
Declared-outputs vault of the audit (variant B vault, observing Follower; fixed_b/vault.ag with the type name changed).
- Liquidation at the NEW price 0.891 (ICR 142.6 < 150) of vault (txid 9c9be31a5795cafb...): tx fc825931b41d9dc3866bff088f301c9a93c3fad7d3ee57e8df7803f4c00b74de, mass 3,369 (compute), accepted (first submit hit a DNS error of the wRPC resolver, resubmitted same tx). It reads the price from the state of the round-4 sibling; the price UTXO was recreated by `use` and a following all-N drain over the recreated sibling passed.
- Not liquidatable: at price 0.99 (ICR 158.4) and at 0.95 the liquidate build fails locally ("script ran, but verification failed"); at the pre-refresh price 1.00 (ICR 160) the same. EXECUTED-LOCALLY only (the builder cannot emit it).
- Same pass locally for variant a (price 0.90 accepted, 0.95 and 1.00 refused). Vault-read cost: `use` of a follower + liquidate: b 3,369 compute / 10,156 transient, a 7,221 / 23,164 (the whole oracle script is in the sigscript for a).
- Control run: liquidation at 0.729 (vault 2.0 TKAS) tx d8fabba0f13d5071dc4d32162730e2857690debb9c785dad20ede480bfa43f9d, mass 10,462.

## 6. Cost comparison (a) vs (b) and publisher cost (item 4)
Measured fee per refresh at the relay floor (100 sompi/gram): see table 3. Per UTXO per refresh: (b) N=4 0.0054 TKAS, N=16 0.0060, N=32 0.0085, N=46 0.0106; (a) N=4 0.0084, N=8 0.0166, N=15 0.0310.
At equal N: (a) costs 1.2x compute / 1.6x transient at N = 4, 1.9x / 2.9x at N = 8; (b) is cheaper everywhere and reaches N = 46 versus 15. Only (a) puts the loop code in every price UTXO (every `use` and vault read pays for it).
DERIVED publisher cost at 1 refresh / 10 s (8,640 / day) at the floor fee, TKAS/day (fee units are the TKAS of this testnet, not a price statement): b N=4 187; b N=8 395; b N=16 833; b N=32 2,337; b N=46 4,209; a N=4 290; a N=8 1,145; a N=15 4,015. Per refresh: 0.0216 / 0.0458 / 0.0964 / 0.2705 / 0.4872 and 0.0336 / 0.1325 / 0.4647 TKAS. Fee scales with compute (quadratic in N for b), so refreshing 4 UTXOs eleven times costs less than one N = 46 refresh... (compare: 11 x 0.0216 = 0.24 vs 0.487). One-per-minute cadence divides these by 6. Block-filling policy under mainnet contention is not tested; N = 46 uses 97.4 % of the compute limit and was included in 6.9 s on a lightly loaded testnet.

## 7. Spend record and recovery (item 5)
Start balance 1,326,675,492,643 sompi (13,266.75 TKAS); end 1,326,165,126,043; **net spend 510,366,600 sompi = 5.104 TKAS, all transaction fees** (72 accepted transactions: splits, genesis, refreshes, vault/liquidation, drains). Every test contract was drained (publisher-only `drain`/`drain_one`); the vault collaterals were recovered through liquidation and withdraw payouts. No covenant value of this work remains locked (API address listing: 73 plain UTXOs, none covenant-bound; 4 plain funding leftovers of 153.9 and 317.7 TKAS are ordinary coins). Budget 100 TKAS respected. Full per-tx ledger: SP/econ/x1b/ledger.jsonl.

## 8. Refusals and incidents (exact messages)
- Node, stale attacks: "Rejected transaction <txid>: transaction <txid> is an orphan where orphan is disallowed" (3 times, section 4).
- The same message also appeared 5 times for split transactions spending a not-yet-known parent while two copies of my driver script ran concurrently (my error: a backgrounded driver was launched twice; I killed both; no value lost, two redundant genesis-funding UTXOs were created). One later drain of the b8 vault was refused with the same message only because the liquidation it depended on had a DNS failure and was resubmitted first.
- wRPC resolver: 'failed to lookup address information: nodename nor servname provided, or not known' twice (drain b46, liquidation b8); resubmit succeeded.
- Builder/local: transient 1057220 > 1,000,000 (a, N=16); compute 507273 > 500,000 (b, N=47); redeem script 274,369 > 250,000 bytes (b, N=128).
- First storage-aware fee choice (fee = 100 x storage mass) exceeded the genesis change output and made a zero-value output (panic in the mass calculator, harness defect, fixed by using the documented floor).
- Splits and the first runs overpaid fees (storage-based) by about 0.01-0.02 TKAS each; counted in the spend.

## 9. Limits and unverified points
Testnet-10 lightly loaded, single sample per row; mass for transient/storage is the local calculator, not read from the node (the API reports compute only). Constants (MOVE_BPS, value sizing) are test values. Extra input sibling and "not liquidatable" cases exist only as builder refusals. The publisher key signs everything: this tests structure, not key compromise. Large-N behaviour beyond 46 is DERIVED (refused locally). Mixed-round refusal is by the leader loop; the delegate `follow` adds its own round check.
