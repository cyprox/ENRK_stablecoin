# econ-t4: fee-mechanism tests on Kaspa testnet-10 (clock, harvest, surplus routing, paired mint, hot UTXO)

Date 2026-11-11. TESTNET-10 only. No design decisions. Repo /Users/simoes/ENRK_stablecoin untouched. The key file was used only through the Rust harness (never printed).
Tags: EXECUTED-ON-CHAIN (txid + API-reported mass) / EXECUTED-LOCALLY (argent builder runs the real script engine at build time) / DERIVED / COMPILED. SP = the scratchpad directory (/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad).
"API mass" is the `mass` field of api-tn10.kaspa.org/transactions/<id>; it equals the compute mass in every case below. Storage mass is computed locally (MassCalculator, same formula as the node) and confirmed by the node refusals quoted.

## 0. Previous run (stopped at the owner's request) and what I redid
Already on chain from the previous run: `b49ede08...6021` (clock genesis, 5 KAS locked, API mass 2083) and `d1575684...1263` (poke_time, mass 2583). Its covenant output d157...:0 (5 KAS) holds a state I could not reconstruct: my candidate state gave a different script hash, so I did not reuse it. It has no exit entry, so those 5 KAS stay locked. A third tx file (5aac..., all sequences MAX) was never submitted.
I reused: harness shape (t4_common.rs, t4_clock.rs, clock/app.ag, t4sub.sh). I redid: a fresh clock covenant with its own genesis (the previous one had the wrong anchor domain for my tests), and every test below. I fixed two harness bugs: tx.id() is stale after a post-build patch (so the fund chain was wrong after MAX-sequence patching), and a stale tx json could be resubmitted after a failed build (rm before build).

## 1. CLOCK (clock/app.ag; entries poke_time = CLTV on ms domain then OpTxLockTime, poke_daa = same in DAA domain, raw_read = OpTxLockTime without CLTV)
Node time facts (clockinfo bin, 5 samples): past_median_time lags wall clock by 130.6 to 140.0 s (132.1, 140.0, 133.9, 131.9, 130.6); tip block timestamp lags wall by 50 to 140 ms. Finality = lock_time < past median time (ms domain, lock >= 5e11) or < virtual DAA (DAA domain).
| case | result |
|---|---|
| poke_daa, lock = daa-300, seq 0 | EXECUTED-ON-CHAIN 751c265b...ad64, mass 2583, 7.4 s |
| poke_time, lock = pmt-1000, seq 0 (anchor in ms domain) | EXECUTED-ON-CHAIN 3f603c81...669d, mass 2583, 7.3 s |
| poke_time, lock = pmt(queried ~2 min earlier)+1000 | EXECUTED-ON-CHAIN 54064ee0...bb5f, mass 2583, 8.0 s (not a boundary test: pmt had moved on) |
| poke_daa, lock = daa+100000, seq 0 | REFUSED: `transaction input #0 is not finalized` (nothing spent) |
| poke_time, lock = wall-60 s, seq 0 | REFUSED: `transaction input #0 is not finalized` |
| poke_time, lock = pmt+60 s, seq 0 | REFUSED: `transaction input #0 is not finalized` |
| raw_read, lock = 9e18, seq 0 | REFUSED: `transaction input #0 is not finalized` |
| raw_read, lock = 9e18, ALL sequences MAX (patched after build) | EXECUTED-ON-CHAIN 3884f885...c00a, mass 2583, 67.0 s. State raw_seen = 9000000000000000000: the A3 overstatement claim is CONFIRMED |
| poke_time, lock = now+600 s, all sequences MAX | REFUSED: `failed to verify the signature script: Unsatisfied lock time: transaction input is finalized` |
| poke_daa, lock = daa+100000, all sequences MAX | REFUSED: same message |
| poke_time, lock below anchor | EXECUTED-LOCALLY refused: `Unsatisfied lock time: locktime requirement not satisfied -- locktime is greater than the transaction locktime: 1794383090752 > 1794383000000` |
| any CLTV entry, sequence MAX (builder) | EXECUTED-LOCALLY refused: `Unsatisfied lock time: transaction input is finalized` |
| poke_time with anchor 0 (DAA-size value) and an ms lock_time | EXECUTED-LOCALLY refused: `script ran, but verification failed` (cause inferred: CLTV domain mismatch; not isolated) |
Conclusions: (a) CLTV first rejects a MAX-sequence input, as claimed; (b) a raw OpTxLockTime read with all-MAX sequences accepts any value (no consensus bound), as claimed; (c) the anchor stored in state must be in the same domain as the lock_time used; (d) the usable "now" in the ms domain is the median time, 130 to 140 s behind wall clock on this network; the DAA domain has a much smaller lag.
Covenants created: genesis a847fc93...5ffd (cov 9eb915ec, used for DAA and raw tests) and cfe099fe...ad70 (cov 726946f3, ms tests); 5 KAS each, no exit entry.

## 2. HARVEST (harvest/app.ag, test copy of A3 s7; harness t4_harvest.rs)
Test-only changes, needed to run at all: (1) the s7 order of the MCR guard `next.value*p*100/PRICE_SCALE/debt` overflows int64 at 10.8 KAS and p=1e8: EXECUTED-LOCALLY refused `Number too big: Product exceeds 64-bit signed integer range`; reordered to `next.value*p/PRICE_SCALE*100/debt`. (2) Elapsed time in seconds (debt*ms*rate also overflows at realistic debt). (3) RATE multiplier 24000, MIN_NOTE 1 KAS, BOUNTY 40%: test-only constants, NOT proposals, chosen so that minutes of real time give a fee above the minimum. (4) FeeNote/Tip spendable by the test key. Vault 12 KAS, debt 4e8, price UTXO 1 KAS.
Minimum-note rule: fee 0.959 KAS < MIN_NOTE, EXECUTED-LOCALLY refused `script ran, but verification failed`.
| batch K | API mass (compute) | transient | storage | fee paid | txid | confirm |
|---|---|---|---|---|---|---|
| 1 | 5234 | 9176 | 166,626 | 0.25 KAS (over-paid) | d69e6bd4...df3e | 46.7 s |
| 2 | 8052 | 15608 | 263,725 | 0.01 | b2a718f9...9234 | 8.3 s |
| 3 | 10870 | 22040 | 363,262 | 0.0115 | 8b67e154...a94e | 67.1 s |
| 4 | 13688 | 28472 | 434,363 | 0.015 | 872dea0a...997d | 7.3 s |
| 5 | 16506 | 34904 | 477,301 | 0.019 | 363e77f3...64db | 7.1 s |
| 6 | 19324 | 41336 | 706,350 | - | refused | - |
K=6 refusal: `transaction storage mass of 706350 is larger than max allowed size of 500000`. Largest accepted batch with 12 KAS vaults, tip 0.4 x fee, note 0.6 x fee: 5 (fee 1.2 to 2.5 KAS per vault, tips 0.5 to 1.0 KAS). Marginal storage per vault is about 97k, dominated by the tip and note outputs (4e12/value each). Fee floor is NOT the storage mass: it is 100 x normalized transient (transient/2): refusals `transaction has 1000000 fees which is under the required amount of 1102000 for normalized transient mass 11020` (K=3) and `1423600 ... 14236` (K=4); K=2 passed at 0.01 KAS with storage mass 263,725.
Also: 14-input reclaim refused at 0.03 KAS: `under the required amount of 3704400 for normalized transient mass 37044`.
Mistake of mine, recorded as a lesson: I edited the .ag after the vault genesis; the node refused every spend with `failed to verify the signature script: false stack entry at end of script execution` (tx 872efeb..., f60de97...) while the builder accepted locally. The builder does NOT compare the rebuilt script with the on-chain script hash; a source/state mismatch shows only at the node. I restored the old source and reclaimed the 14 vaults (EXECUTED-ON-CHAIN 75a65cae...03aa, API mass 33,882, 168 KAS back), then regenerated. Second set reclaimed in 15de5635...6c19 (14 inputs).
Not tested: harvest by a second keeper, oracle `clock` ahead of lock_time (refusal path), notes/tips consolidation. 30 notes/tips (28.8 KAS) are still on chain, spendable by the test key (take entry), not collected.

## 3. SURPLUS ROUTING (surplus/app.ag, test copy of A3 s4; harness t4_surplus.rs)
Vault 12 KAS, debt 8.5e8, price 1 KAS: surplus 3.5 KAS -> refund 1.75 / junior 1.05 / reserve 0.70 (50/30/remainder, s4 placeholders). Arithmetic splits verified by the engine (build) and by the node.
| liquidation | API mass | transient | storage | txid | confirm |
|---|---|---|---|---|---|
| K=1 (12 KAS) | 5103 | 8652 | 157,935 | 0f5566f1...7b82 | 27.2 s |
| K=2 | 7790 | 14560 | 275,872 | 25ed2e85...4baa | 7.3 s |
| K=3 | 10477 | 20468 | 393,766 | 2ebcf643...26eb | 27.0 s |
| K=4 | refused | | 511,612 | 2c0c9424... | `transaction storage mass of 511612 is larger than max allowed size of 500000` |
| K=1 (3 KAS vault, surplus 0.9) | 5103 | 8652 | 499,085 | 84dcae83...c942 | 51.5 s |
| K=2 (3 KAS vaults) | refused | | 958,173 | 64221674... | same message |
| K=50 (3 KAS vaults) | refused | local compute 136,766, transient 298,144, 52 inputs, 152 outputs | 22,933,072 | d60cd3c3... | same message |
Vaults per transaction: 3 at 12 KAS, 1 at 3 KAS; the limit is the storage mass of the three covenant outputs (4e12/value each), not compute or transient. Creating 50 vaults in one genesis is also refused (666,651 > 500,000, 3 KAS each); 25 per genesis accepted (333,325; 200e47e4..., 333dee2c...). The 21 refund/junior/reserve outputs were recovered on chain (3b94f9d8...c26c, API mass 26,833) and 53 vaults reclaimed (daa81e98...1bcb, API mass 118,544, 54 inputs). Test-only changes: pots/refund spendable by the test key, ICR product reordered (same overflow as in section 2). No minimum-amount rule was tested (s4 has none).

## 4. PAIRED MINT (mint/app.ag, test copy of A3 s3; harness t4_mint.rs)
Change needed: the two asset covenant ids are entry arguments, not Issuer state. With the ids in state, the Issuer covenant id and the MinterProxy `controller_id` would depend on each other through the genesis hash (cyclic), so the covenants cannot be created (DERIVED, not executed). Single genesis with three groups instead.
- EXECUTED-LOCALLY: `open(1000)` builds (compute 6036, transient 14,464, 3 inputs, 6 outputs); with kFIAT amount 301 instead of 300 it is refused: `input 0 script failed: script ran, but verification failed`.
- EXECUTED-ON-CHAIN: genesis 6766e5f9...8bad (API mass 2997, 7.7 s); open 11728849...5e1d (API mass 7568, transient 15,152, storage 113,029, 7.3 s): ENRK 700 + kFIAT 300 minted and a vault recording both debts, in one transaction. A wrong-ratio transaction was not sent to the node (it cannot be built). Issuer and proxies have no exit entry: 18 KAS locked plus 5 KAS in the outputs.

## 5. HOT UTXO THROUGHPUT and Silverscript #252
Price UTXO `use` spends, each tx also chained on the fund change (all-sequential dependency), fee 0.006 KAS, API mass 2416 each.
- 20 back-to-back (one connection): all 20 accepted by the mempool in 1.56 s; all included, block_time of first/last 1794385468970 / 1794385471055 = 2.09 s, accepting DAA 608849283..608849309: about 9.6 spends/s.
- 60 back-to-back: all accepted by the mempool in 4.76 s (about 80 ms per submit round trip); all included within 9.97 s block_time span (6.0 spends/s), first inclusion 0.76 s after the first submit; DAA span 101. No "too many ancestors" limit was reached at depth 60.
- Competing spends of one outpoint: A accepted (a23bdfc8...5704, included 0.64 s later); B refused immediately: `output (795b832ba33fd8bb08c373e730773c3e84d3e3ab5397a500bfce9bfb7538a193, 0) already spent by transaction a23bdfc80c67a6f2618a9de85c47253c0c7e6808d8b902b25b172b5f99755704 in the mempool`; resubmitted after A confirmed: `transaction 57e8e32f... is an orphan where orphan is disallowed`. Nothing spent by the loser.
- #252 (readInputStateWithTemplate + validateOutputState in one entry): present together in compiled entries Vault.harvest and Issuer.open (and with validateOutputStateWithTemplate in Vault.liquidate). No compiler crash; all three EXECUTED-ON-CHAIN and accepted (harvest K1-K5, liquidate K1-K3, open). Not a proof of absence of other effects.

## 6. Funds and cleanup
Start 3331.06 TKAS, end 3266.75 TKAS: net 64.3 TKAS out (cap 300). Composition: about 10 KAS in my two clock covenants plus 5 KAS in the previous run's, 2 KAS price UTXOs (1 KAS each, spendable by `use` only), 23 KAS paired-mint structures, 28.8 KAS harvest notes/tips (recoverable), fees about 0.7 KAS. No background process left running (checked with ps).

## 7. Reproduction (all under SP/tn10; env TN10_DIR=SP/tn10 T4SRC=SP/econ/t4 are set by the scripts)
- clock: `tn10/ckpoke.sh <poke_time|poke_daa|raw_read> <lock> <seq> ; tn10/t4sub.sh t4_ck_poke.json <tag>`; add PATCH=1 for the MAX-sequence variants; time: `tn10/pmt.sh`.
- harvest: `tn10/hv.sh hv_vault_genesis`, `tn10/hvrun.sh "<vault idx list>" <tag> <fee>`; reclaim `VIDS=.. tn10/hv.sh hv_reclaim`.
- surplus: `tn10/sp.sh sp_vault_genesis`, `tn10/sprun.sh "<idx list>" <tag> <fee>`, `tn10/sp.sh sp_reclaim|sp_take`.
- mint: `tn10/t4run.sh t4_mint mt_local|mt_genesis|mt_open`.
- hot: `K=60 FEE=600000 tn10/t4run.sh t4_harvest hot_chain_build; target_rpc/debug/submit_many tn10/t5_0*.json; tn10/t5poll.sh`; conflict: `FUND2="<txid idx amount>" tn10/t4run.sh t4_harvest hot_conflict_build; submit_many t5c_a.json t5c_b.json`.
- sources: SP/econ/t4/{clock,harvest,surplus,mint}/app.ag; harnesses SP/w/argent/tests/t4_*.rs; result logs SP/econ/t4/log/*.txt; submit_many bin SP/rpc/src/bin/submit_many.rs.
Caveats: wRPC resolver often fails with a DNS error (retried). Confirmation time varies 7 to 67 s in the same session (not caused by tx size). Constants in sections 2 and 3 are test values, not proposals.
