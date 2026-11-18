# econ-a3: stability fee, junior remuneration, surplus routing on an immutable UTXO system

Status 2026-11-17: owner decisions since this report: execution layer is Kaspa L1, Igra not retained (2026-11-13); stability fee recurring, fees never burned (a burn option is excluded). Passages on Igra and on burning are kept as history.

Superseded in part by econ-t4 (executed on testnet-10): timestamp lag 130-140 s (not tens of seconds); harvest max 5 vaults per tx and surplus routing max 3 (not 160-180 / 150); hot UTXO 6.0-9.6 spends/s. See econ-v4 section 'P16 A3 compiled claims vs econ-t4 executions'.

Date 2026-11-10. Research and design feasibility only. Repo not modified, no transaction executed, no secrets read, nothing under scratchpad/tn10 read.
Everything labelled "proposal for owner decision" is an option, not a decision.
Tags: VERIFIED = read in source or compiled by me (file:line or snippet path); DERIVED = arithmetic or reasoning from verified facts; UNVERIFIED = not checked / must be tested.
Snippets: /private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/econ/a3/s1..s7 (compiled with the prebuilt argentc; COMPILE = accepted by the compiler, NOT executed on any engine or network).
Path prefixes: RK = scratchpad/src1/rusty-kaspa (master 4863866f), SS = scratchpad/src_silverscript/s (HEAD 443d519), AG = /Users/simoes/ENRK_stablecoin/argent (e76ee07), AUD = docs/design/AUDIT-2026-11-09.md, P5A/P5B/R3 = scratchpad/reports/p5a..., p5b..., r3....

## 0. Fact base used (from the files named in the brief, re-checked where it matters)

- UTXO model, 10 blocks/s nominal; measured DAA rate 11.9/s (TN10) and 8.3/s (mainnet) in a 20 s sample (AUD 13.3b). Plain tx submit-to-confirm about 8 s; 180-vault liquidation confirmed in about 10 s (AUD 13.3b). [VERIFIED by lead, executed]
- Mass: compute 500k, transient 1M, storage 500k per block (AUD 13.1). Fee floor `100 sompi x max(compute, 0.5 x transient)` (AUD 13.3b). Transient about 4,760 per vault input, so about 200 vaults per liquidation tx; 180 vaults + 1 price UTXO executed: 218,385 compute, 866,620 transient. Oracle ladder constants: 759 compute / 1,556 transient per `use` input (A), 839 / 1,876 (B); 642 (A) / 532 (B) inputs per tx by transient (P5A s3, s4).
- Storage mass of a covenant output is about `4 x 10^12 / value_in_sompi` (plurality 2, KIP-9; AUD 13.3b). So a covenant output of 1 KAS costs about 40,000, of 0.1 KAS about 400,000, of 10 KAS about 4,000 storage mass; block limit 500,000. Genesis of about 100 vaults of 9 KAS was the measured ceiling. [DERIVED from VERIFIED formula; the exact mixed-input/output case must be measured]
- Time primitives (AUD 13.1; SS docs/TUTORIAL.md:519-535; SS silverscript-lang/src/compiler/builtin_types.rs:67,162; builtin.rs:61-62): `tx.daa >= x` / `tx.time >= x` (CLTV, absolute lower bound on lock_time), `this.ageDaa >= x` (CSV on the spent UTXO's age), and the raw reads `OpTxLockTime()` and `OpTxInputDaaScore(i)` (creation DAA of input i). No current-DAA or current-time read, no deadline. Argent accepts all of them: snippet s1 (COMPILE: OpTxLockTime, OpTxInputDaaScore on three accrual entries, Vault script 1,871 B, state 84 B).
- KCC-20: no mint, burn, supply or controller (R3 s1; AUD 13.3). Argent's ICC example shows a controller pattern outside KCC-20: `MinterProxy.mint` requires `controller_id.co_spent()`, controller `Minter` holds remaining `amount` (AG examples/icc/kcc20_asset.ag, minter.ag). Its transfer keeps `amount` and has no split or merge. [VERIFIED source]
- Oracle (variant A): `PriceRoundState {publisher, round}`; `use` recreates the UTXO unchanged (so its creation DAA is reset on every vault touch); `sweep` splits 1 to 2 and increments `round` (examples/enrk/a/oracle.ag:15-60). Stale siblings are valid forever unless the sweep provably consumes all of them (P5A s3, Design 3.A). [VERIFIED]

## 1. Lazy accrual of the stability fee (accrual clock)

### 1.1 What clock is actually possible
1. Consensus bound (VERIFIED, RK consensus/src/processes/transaction_validator/tx_validation_in_header_context.rs:61-87): a tx is final if `lock_time < accepting DAA score` (DAA domain, below 5x10^11) or `< median time` (timestamp domain), OR if every input has `sequence == u64::MAX`, in which case lock_time is ignored. CLTV (RK crypto/txscript/src/opcodes/mod.rs:874-918) fails when the input's sequence is MAX.
2. Consequence A: a raw `OpTxLockTime()` read WITHOUT a CLTV check can be set to any huge value by a spender who sets all sequences to MAX (overstatement). Safe pattern: `require(tx.time >= temporal(anchor))` (or `tx.daa`) first, then `OpTxLockTime()`. Then `anchor <= L < accepting time`. COMPILE: s2 (daa), s6 (time). The CLTV rejection of the MAX-sequence case is read in source, not executed. [VERIFIED reading + compile; behaviour on engine UNVERIFIED, test on TN10]
3. Consequence B (the main point): the spender chooses L anywhere in [anchor, now). He can UNDERSTATE, never overstate. A fee that grows with claimed elapsed time is therefore enforceable only against actors who want L high (liquidators, keepers, fee collectors). The payer (vault owner) will claim L = anchor and pay nothing. Path independence makes it worse: understating at every touch is free, because the anchor then stays low. [DERIVED; no counter-primitive exists: AUD 13.1 "no deadline primitive"]
4. `OpTxInputDaaScore` of a co-spent input is consensus-set and cannot be forged, but it is only "last time that UTXO was created". Oracle price siblings are recreated by every `use`, so a spender picks the stalest sibling (understate again), and nothing makes the freshest sibling mandatory. [DERIVED from oracle.ag `use`]
5. Domain choice: DAA score runs at 8.3 to 11.9 per second (AUD 13.3b), so a "DAA per year" constant gives about +/-30% error on the annual rate. The timestamp domain (`tx.time`, milliseconds, bounded by median time of past blocks) avoids that; its lag behind wall clock (median time window) is UNVERIFIED, probably tens of seconds. Proposal for owner decision: timestamp domain.

### 1.2 Options
- C-A "stamp at each touch, claimed lock_time" (s1 `touch_locktime`, s2). State: `anchor` in vault (8 bytes). Pros: no oracle dependency, tiny. Cons: UNSAFE for owner-initiated actions (zero fee by always claiming L = anchor). Only safe for permissionless pokes. Not acceptable alone.
- C-B "oracle-carried clock" (s6, s7 COMPILE): `PriceRoundState` gets `clock` (ms), written at `sweep` as `OpTxLockTime()` after a monotone CLTV (`tx.time >= temporal(clock)`). Every vault action that already co-spends the price UTXO adds `require(L >= price.clock)`; the owner cannot claim a time older than the last sweep. Accrual = rate x (L - anchor). Lag of the clock = sweep cadence, the same as price staleness. Trust: the publisher can only understate its stamp (less fee), not overstate; it is already trusted for the price. Cons: (i) inherits the stale-sibling problem: an owner can use an old sibling with an old clock and old price; fixing it needs the atomic complete sweep (P5A Design 3.A, not executed) or accepts the same exposure that exists for prices; (ii) +8 bytes per price UTXO state; (iii) clock stalls if the publisher stalls (fees stop, but the system is also frozen at that point); (iv) `sweep` for N = 640 already uses 97.5% of compute: adding code needs a re-measurement. [DERIVED, compile only]
- C-C "round counter as clock" (s1 `touch_round`, COMPILE): fee per oracle round, `round` already exists (oracle.ag:15-16). Pros: no new field, no time primitive. Cons: effective annual rate = rate_per_round x rounds_per_year, set by publisher cadence (an unbounded trusted parameter). A floor on cadence cannot be enforced with `this.ageDaa` on the swept UTXO because `use` is permissionless and recreates the UTXO, so any griefer resets its age and can block sweeps indefinitely (DERIVED from oracle.ag `use`; test on TN10). Use only if the owner accepts publisher-defined fee time.
- C-D "dedicated clock UTXO, anyone may tick" (same code as s6 minus price): a tick needs `tx.time >= clock` and sets `clock' = OpTxLockTime()`. Pros: separates the fee clock from the price trust path; anyone can tick, incentivised by a tip from the fee pool. Cons: a new shared UTXO that every owner action must co-spend (read = spend and recreate: contention, section 6), stale-clock liveness depends on a keeper being paid.

### 1.3 How a never-touched vault pays
Permissionless `harvest` (s7, COMPILE, Vault script 1,122 B, state 150 B): anyone spends the vault with the price UTXO, claims L (honest-high is in the keeper's interest), computes `fee_kas = debt x rate x (L - anchor) / year x SCALE / price`, outputs `next` vault (value reduced by fee_kas, `anchor = L`, vault at or above MCR), a fee note, and a keeper tip. The fee is paid in KAS from collateral at the current price (a falling KAS price costs more KAS, constant in ENRK terms). Failure modes: (a) no keeper acts: fee not collected, but accrued time is preserved in `anchor`; nothing lost except delay, and the vault is eventually harvested or liquidated; (b) a harvest that would push the vault under MCR is refused by the script in s7, so an unhealthy vault goes to liquidation first and the fee must come from liquidation proceeds, which needs a waterfall rule (open); (c) overflow: `debt x elapsed_ms x rate` and `fee_units x PRICE_SCALE` must be bounded (UB spec lets the compiler assume no overflow; AUD 13.2), so debt, elapsed and scale need range proofs; (d) keeper tips below about 0.1 KAS cannot be separate outputs (storage mass 400,000 or more per output), so tip and note need minimum values, and harvest must wait until `fee_kas >= MIN_NOTE`. [DERIVED]

### 1.4 Liquidation must include accrued fee
Liquidator-supplied L is honest-high (cannot exceed real time), so including `accrued(L - anchor)` in the ICR test is safe against owners. Owner-side actions need the oracle clock. [DERIVED]

### 1.5 Mass for harvest (DERIVED, not measured)
Per vault input about 4,760 transient (measured for liquidation) plus 3 outputs of roughly 100 to 200 bytes: about 5.5 to 6 k transient per vault, so about 160 to 180 vaults per tx by transient. Storage is the real cap: each covenant note of value X costs 4x10^12 / (X x 10^8) mass, so X = 10 KAS gives 4,000 (about 120 notes per tx), X = 1 KAS gives 40,000 (about 12 per tx). Fee at floor: 100 x max(compute, 0.5 x transient), about 0.2 to 0.45 KAS for a 180-vault tx (liquidation analogue). Must measure on TN10: a 3-output harvest of 1, 10, 100 vaults with notes of 1, 5, 10 KAS.

## 2. Collecting the fee into a place kFIAT holders can claim

No shared mutable state on L1, so every "pool" is a UTXO (or a set) that some spender must consume and recreate.

### F1 global fee-pool UTXO, every harvest deposits into it
Each harvest co-spends the pool and recreates it larger. Pros: simplest accounting. Cons: contention on every fee event (section 6); a batch harvest of K vaults could deposit once per tx, but each vault script cannot see a shared output split without a leader actor. Not recommended.

### F2 fee notes + permissionless consolidation (proposal for owner decision)
Harvest creates independent `FeeNote` UTXOs (s7). No contention at harvest time. Consolidators (anyone, tipped) batch notes into the pool: per note input about 1.6 k transient (oracle-ladder analogue, UNVERIFIED for this script), so about 600 notes per tx (transient), one pool spend per tx. Pros: contention moves off vault actions; consolidation is batchable and retryable. Cons: minimum note value (storage), an extra actor, and notes are real UTXOs (UTXO-set growth, each costs storage mass at creation). Failure: sub-minimum fees stay as unharvested time in the vault (delay, not loss).

### F3 settlement-only payment (no notes, no mid-life pool contact)
Fee accrues inside vault state (`fee_owed`) and is paid to the pool only at close, partial withdraw or liquidation. Liquidation is a batched single shot (about 200 vaults, one pool spend). Pros: least state, no dust problem, no keeper accounting. Cons: junior holders are paid late and only as vaults leave; fee due from vaults that never close is credit exposure against collateral that may fall; the fee is an unfunded promise until settled. Hybrid (F2 above a size, F3 below) possible.

### F4 rotating set of M pools
Vault action picks a pool by hash(outpoint) mod M; contention divided by M; holders then need all M pools (claims aggregate across pools or pools merge per epoch). Only useful if F1 were chosen.

Trust: none beyond covenant code and the oracle clock. Failure: pool griefing (a permissionless `deposit` entry spent with 1 sompi at the confirmation rate starves legitimate claimants; mitigate with minimum deposit and by making claim require the token UTXO).

## 3. Distribution to kFIAT holders without enumerating holders

### D1 pull-claim accumulator, index per token UTXO (s5 COMPILE)
Token state `{owner, amount, idx_paid}`; pool state `{tok_covid, idx, supply}`. `claim` co-spends pool and token, pays `amount x (idx - idx_paid) / SCALE`, sets `idx_paid = idx`; the pool forces the exact successor token with `require kf.outputs become` (compiled; Pool script 1,008 B, 2 entries). `deposit` raises `idx` by `deposit x SCALE / supply`. The index lives in the pool UTXO state (the only mutable shared object); anyone can update it via `deposit` (the F2 consolidator).
Pros: holdings are never enumerated; a flash holder gains nothing because the checkpoint travels with the token; claims batch (K tokens + 1 pool).
Cons and unsolved parts:
 - `supply` denominator. KCC-20 has no supply (R3). A custom controller/minter must hold `outstanding`, updated at every mint and burn. A single counter is a hot UTXO; sharded counters need a tx that reads all K shards at deposit time (K at most about 200 inputs by transient). [DERIVED]
 - Fungibility: KCC-20 is fungible only if `extension_commitment` is identical (R3); different `idx_paid` per UTXO breaks that. Options: weighted-average checkpoint on merge (round up; conserves entitlement within rounding), or forced claim before any transfer (puts the pool on the transfer path: rejected). Compatibility with Final KCC-20 and kccs #14 (extended state vs consolidation) is UNVERIFIED.
 - New mints must start at the current index; a minter can only know it by co-spending the pool (pool on the mint path, rate = vault opens) or by reading an epoch value from the oracle; otherwise `idx_paid = 0` would drain history.
 - Overflow: `amount x (idx diff)` with SCALE 10^12 exceeds 2^63 at realistic supplies; scale and bounds need range proofs (UB, AUD 13.2).
 - Payout dust: a payout costs 10^12/v (ordinary) or 4x10^12/v (covenant) storage mass; claims below about 1 KAS cost 10^4 or more each, so a minimum due is required or a 200-holder batch hits the 500k cap. [DERIVED]

### D2 epoch snapshots with per-epoch pots
Epoch e has pot UTXO `P_e` with frozen denominator `S_e` (supply at epoch start); token state `{amount, claimed_epoch}`; claim of epoch e pays `amount x pot_e / S_e`; mints start at the current epoch (so they first earn e+1, which removes "mint just before distribution"). Contention is spread over fresh UTXOs per epoch. Cons: a token claims epoch by epoch (365 spends for an idle year unless pots chain remainders), the epoch counter needs the oracle `round`/clock, `S_e` still needs the sharded supply read. Fallback if D1's pool contention measures badly.

### D3 distribution at liquidation/settlement events only
Fees stay with the vault; routed to a pot with a snapshot denominator when the vault is liquidated or closed. Pros: no index, no continuous supply read. Cons: remuneration is event-driven and can be near zero in a calm market, against the owner decision that fees remunerate holders.

### D4 series tokens (kFIAT minted per vault or cohort)
Fees from vault v belong to kFIAT minted from v; no global denominator. Breaks fungibility (one price per series). Not recommended.

Direction (proposal for owner decision): F2 + D1 with sharded supply counters; D2 as fallback; reject D4.

## 4. Routing of auction surplus (S1 owner, S2 junior, S3 reserve) in the liquidation tx

Single-shot; no shared state beyond the co-spent price UTXO. s4 COMPILE: `Vault.liquidate` emits `{refund: Refund, junior: Pot, reserve: Pot}` with `refund.value == surplus x S1%`, `junior.value == surplus x S2%`, `reserve.value == remainder` (rounding to S3); vault script 966 B. Compile lesson: two actors with identical state shape fail ("conservative frame rule found an ambiguity between actors JuniorPot and Reserve"), so use one `Pot` actor with a tag or different state shapes. [VERIFIED compile]
 - S1 owner refund: actor with `checkSig(owner)` (s4 `Refund`). An ordinary-address output cannot be enforced through `emits none` (unconstrained); not tested otherwise.
 - S2 junior: `Pot` that feeds F2/D1 like a `FeeNote`. One pot per liquidated vault unless a batch leader aggregates (UNVERIFIED).
 - S3 reserve "counted as collateral": on L1 the reserve is an unattributed set of UTXOs; counting it in any ICR needs a global sum. OPEN; the owner must define how reserve UTXOs are consumed (waterfall only, or pro-rata redemption).
Constraints: (1) each output of value v costs about 4x10^12/v storage mass; 200 vaults with 1 KAS S2 notes cost 200 x 40,000 = 8M, impossible, so minimum amounts (below minimum everything to one destination) are mandatory. (2) Percentages S1/S2/S3 are immutable constants and need owner values. (3) Three extra outputs add about 1.5 to 2 KB transient per vault, so about 150 vaults per tx instead of 200 (DERIVED).
Trust: oracle price only. Failure: stale price (stale-sibling problem) affects surplus exactly as it affects liquidation.

## 5. Mandatory junior share at mint

Enforced per vault without global supply: one issuer entry mints both tokens and the vault records both amounts. s3 COMPILE: `Issuer.open(total_debt, ...)` computes `k = total_debt x 30 / 100`, `e = total_debt - k`, requires `enrk.outputs become {proxy, recipient(e)}` and `kfiat.outputs become {proxy, recipient(k)}`, emits `vault` with `{debt_enrk: e, debt_kfiat: k}`; two `observes` (two covenant ids) over the ICC `MinterProxy`/`KCC20` shapes. Pros: the 30% is arithmetic in one entry; no global kFIAT state; the vault carries `debt_kfiat` so close/repay can require a proportional burn. Cons: (i) controllers are covenant-specific (KCC-20 has no controller binding); the ICC minter keeps a remaining `amount`, a global cap UTXO; (ii) the issuer UTXO plus two MinterProxy UTXOs are spent on every open: contention at the vault-open rate, so use K parallel issuers with separate caps (global cap = sum of K caps); (iii) ENRK must be mintable only through `Issuer.open`, otherwise ENRK-only positions exist; (iv) repay/close must burn kFIAT proportionally (another controller entry, same contention class). Not tested: execution; interaction with Silverscript #252 (AUD 13.2).

## 6. Contention and latency: simulation inputs

Measured (AUD 13.3b): plain tx accepted in about 8 s; N=256 oracle round confirmed within seconds; 180-vault liquidation in about 10 s; DAA 11.9/s (TN10), 8.3/s (mainnet). All others below are DERIVED or UNVERIFIED.
 - Hot shared UTXO serial rate. Conservative (wait for confirmation): one confirmed spend per 8 to 10 s (about 8,600 to 10,800 per day). Optimistic (chained in mempool): up to about 1 per second (UNVERIFIED; P5A Design 3.C says chained spends of one outpoint across a 10 BPS DAG must be tested). Competing spends of one outpoint: one wins, the loser is rejected and pays no fee, so failure shows as retries. Sim parameters: service time S in {1, 10} s; arrival rate lambda per pool; utilisation rho = lambda x S, keep rho below 0.5.
 - Batching multiplies a hot UTXO: one pool spend serves about 200 vault-class inputs or up to about 600 small-note inputs (transient), but payouts are capped by storage mass: about 12 to 125 payouts per tx for 1 to 10 KAS payouts.
 - Vault touches per second are bounded by oracle contention first (P5A), not by the fee pool, if F2 is used (harvest does not touch the pool).
 - Fee income for sizing (DERIVED): junior yield = fee rate r / junior share: r=1% gives 3.3%, r=3% gives 10% per year on kFIAT face at a 30% share (consistent with P5B Decision E3).
 - Harvest cadence: interval = X x price / (D x r / year). Example D = $1,000, r = 2%, X = 10 KAS at $0.0295 gives $0.295 / ($20/yr) = about 5.4 days (price from AUD 13.3).
 - Keeper economics: tx fee floor about 0.0025 KAS for a 2.5 k-mass single-vault tx and 0.2 to 0.45 KAS for a 180-vault tx; below any sensible note, so tip minimums come from storage dust rules, not network fees.
Inputs for the economic models: (a) clock lag = sweep cadence (publisher-defined); (b) harvest delay distribution (keeper activity); (c) minimum note and minimum claim; (d) hot-UTXO service time S and conflict rate; (e) K shards for supply and issuer; (f) kFIAT holder share of fee net of keeper tip and tx fees; (g) fraction of vaults never harvested (credit exposure of unpaid fee).

## 7. Ranking by implementability

L1 today, easiest first:
 1. Surplus routing in the liquidation tx (s4): single shot, no shared state; needs minimum amounts and a decision on S3.
 2. Mandatory 30% junior share via paired issuer (s3): arithmetic only; needs sharded issuers; custom controller, not KCC-20.
 3. Harvest with oracle-carried clock and fee notes (s6, s7): compiles; depends on the stale-sibling fix; needs storage-mass measurements.
 4. Event-only distribution (D3 / F3): simplest, weakest remuneration.
 5. Pull-claim accumulator (D1, s5): compiles; denominator and mint checkpoint unsolved.
 6. Epoch pots (D2): heavy; fallback.
Igra EVM (brief): all of it is routine storage logic (rewards-per-token accumulator, `block.timestamp`, one pool contract, supply as a storage variable); contention is solved, the cost is gas plus the bridge/exit constraints already in AUD 13.3. Not analysed further.

## 8. Main unsolved problems
 1. A trustless accrual clock for the payer: only an oracle-carried (or keeper-ticked) clock bounds the payer, and it inherits stale-sibling and publisher liveness risks. No deadline primitive.
 2. A supply denominator for pro-rata distribution without a hot global counter (sharded counters untested).
 3. kFIAT token: KCC-20 has no controller/mint/burn and per-UTXO index state conflicts with fungibility (kccs #14); wallet and indexer support unknown.
 4. Dust and storage mass: minimum note, tip, claim and S2 amounts; exact storage mass of mixed harvest and claim txs not measured.
 5. Overflow and undefined behaviour in fee and index math on an immutable contract (AUD 13.2).
 6. S3 "reserve counted as collateral" has no L1 form without global state.
 7. Griefing of a shared pool through permissionless entries; liveness depends on paid keepers.
 8. Fee paid in KAS falls with the collateral in the very scenario where junior is called (wrong-way risk, P5B Decision E3).

## 9. To test on testnet-10 (nothing executed here)
 1. s2/s6: CLTV with sequence MAX rejected; lock_time above accepting time rejected; `OpTxLockTime()` equals the tx lock_time; timestamp-domain lag against the chain.
 2. Chained spends of one outpoint: confirmed per second and per block; loser behaviour under competing broadcasts (hot-UTXO service time S).
 3. Harvest tx (s7 shape): storage mass with 1, 10, 100 vaults, notes of 1, 5, 10 KAS; tip minimums.
 4. Pool `claim` (s5 shape) with 1, 10, 100 token inputs: compute, transient, storage; maximum payouts per tx.
 5. Paired mint (s3 shape): execution, mass, Silverscript #252 interaction.
 6. Surplus routing (s4 shape): execution with 1 and 100 vaults, minimum amounts.
 7. Oracle `sweep` carrying `clock` at N = 640 (mass); the griefing case that `use` resets UTXO age.
 8. Sharded supply counters: reading K = 50 and 200 shards in one tx.

## 10. Proposals for owner decision (options only)
 - Clock: C-B oracle-carried clock in the timestamp domain, conditional on the stale-sibling fix; C-C only if publisher-defined fee time is acceptable.
 - Collection: F2 notes + consolidation; F3 as small-vault fallback.
 - Distribution: D1 with sharded supply counters; D2 fallback; reject D4.
 - Surplus: S1/S2 as arithmetic splits with minimum amounts; S3 needs the owner to define how reserve UTXOs are counted and consumed.
 - Junior share: paired issuer with K shards.
 - Owner inputs required: fee rate and dust minimums, keeper tip rule, S1/S2/S3 percentages, whether unpaid fee at liquidation ranks above or below the junior waterfall.

## Snippet index (all COMPILE only)
s1 three accrual clocks (lock_time, round, input DAA); s2 CLTV-guarded lock_time; s3 paired ENRK/kFIAT issuer 70/30; s4 liquidation surplus split to three outputs (first build failed on identical actor shapes); s5 pull-claim accumulator pool + indexed token; s6 oracle price UTXO with `clock` written at sweep via CLTV + OpTxLockTime; s7 harvest with fee note, keeper tip, price conversion, MCR guard.
