# P5a - Kaspa L1 feasibility for ENRK (research, read-only on the repo)

Date: 2026-11-09. Repo not modified. Experiments were compiled in the scratchpad only
(`.../scratchpad/exp/{fix,atom,two,inapp}`) with the repo's prebuilt
`argent/target/debug/argentc` (Argent e76ee07). Nothing was executed on a node or in the mass harness.

Legend: VERIFIED = read in primary source (file/line, or URL fetched; web pages were read through a
fetch tool that summarises, so "VERIFIED(web)" = primary URL, summarised text). SECONDARY = news,
blogs, repo-internal docs restating others. UNVERIFIED = inference or not tested. DERIVED = my arithmetic
from verified constants. COMPILED = compiled with argentc, not executed.

Source shorthands
- RK = rusty-kaspa a41a333 at `~/.cargo/git/checkouts/rusty-kaspa-410e06d1fde91a92/a41a333/`
- SS = silverscript 3ed9733 (= v1.0.0) at `~/.cargo/git/checkouts/silverscript-841a3a94387c7d80/3ed9733/`
- AG = `/Users/simoes/ENRK_stablecoin/argent` (e76ee07)
- KIP-n = https://raw.githubusercontent.com/kaspanet/kips/master/kip-00nn.md

## 0. Ground facts used below

| # | Fact | Source | Status |
|---|---|---|---|
| F1 | Toccata mainnet activation DAA 474,165,565, about 2026-06-30 16:15 UTC; implements KIPs 16/17/20/21 | RK `consensus/core/src/config/params.rs:724`; https://github.com/kaspanet/rusty-kaspa/releases/tag/v2.0.0 | VERIFIED / VERIFIED(web) |
| F2 | "activated Toccata ... on June 30"; covenant txs about 2.4k/day in Aug, no token/stablecoin/oracle apps mentioned; Argent "not yet release-ready" | https://buttondown.com/kaspalytics/archive/issue-1-toccata-live-covenant-usage-a-block/ | SECONDARY |
| F3 | Opcodes: OpCovInputCount 0xd0, OpCovInputIdx 0xd1, OpCovOutputCount 0xd2, OpCovOutputIdx 0xd3, OpAuthOutputCount 0xcb, OpAuthOutputIdx 0xcc, OpInputCovenantId 0xcf, OpOutputCovenantId 0xd5. Genesis outputs are NOT visible to OpAuth*/OpCov*. Covenant id = BLAKE2b("CovenantID") over authorizing outpoint + ordered authorized outputs (index, value, spk). A continuation output can only be authorized by an input with the same covenant id. No protocol cap on authorized outputs. | KIP-20 sections "Covenant ID Derivation", "Script Opcodes", "Continuation Output Rules", "Limits"; RK `crypto/txscript/src/opcodes/mod.rs:1438,1517-1560` | VERIFIED |
| F4 | `num_covenant_outputs(id)` counts all continuation outputs with that id, whoever authorized them | RK `crypto/txscript/src/covenants.rs:52-90` | VERIFIED |
| F5 | Script ints: 8-byte; OpMul/OpDiv use `checked_*` and raise an error on overflow / div by zero at engine level | RK `opcodes/mod.rs:769-800`; KIP-10 (8-byte arithmetic, silent on overflow) | VERIFIED |
| F6 | BUT Silverscript declares overflow and div-by-zero undefined behaviour: the compiler may fold/remove the check and the spend then succeeds | SS `UNDEFINED-BEHAVIOUR.md:1-64` | VERIFIED |
| F7 | KIP-9 mentions the 100,000 "standard" cap only in the mempool/P2P rule; block limit 500,000; no transient mass in KIP-9 | KIP-9 "Standard and Block Mass Limits" | VERIFIED(web) |
| F8 | In RK the 100k cap is `MAXIMUM_STANDARD_TRANSACTION_MASS_PRE_TOCCATA`, applied to compute, transient and storage; it is dropped 30 min before Toccata activation "and ever after"; only block-fit limits remain. Toccata limits compute 500k / transient 1M / storage 500k. Transient = 4 x tx bytes. `max_tx_inputs`=1000. Min fee = 100 sompi x max(compute, 2 x tx bytes). | RK `mining/src/mempool/check_transaction_standard.rs:21-60,70-100`; `consensus/core/src/config/params.rs:686,699,419`; `consensus/core/src/mass/mod.rs:367`; `docs/toccata-guide.md` ("Fee Adaptation") | VERIFIED |
| F9 | KIP-17 script limits post-Toccata: element 1,000,000 B, script 1,000,000 B, 1M ops. No opcode in the KIP-17 list returns "current time/DAA score" (only OpTxInputDaaScore = creation score of an input, OpTxLockTime). | KIP-17 "New and Existing Opcodes", "Script Limits" | VERIFIED(web); the absence is read from the list, UNVERIFIED against the full opcode table |
| F10 | Argent ICC: `id.co_spent()` is "only a presence check"; "presence is not the same as authorization scope". `observes` describes the COMPLETE observed input/output groups ("Allow open observed groups" is a follow-up). Observed and spawned ranges are rejected by the compiler. | AG `docs/icc-semantics.md` (Co-spend presence); `docs/followups.md` ("Allow open observed groups"); `docs/entry-clause-ranges.md` header | VERIFIED |
| F11 | Leader/delegate: ordinary entry of a leader actor without `consumes` requires `|I(c)|=1`; coordinated leader entries own the whole continuation group; delegates cannot be told apart per entrypoint (Property 7). | AG `docs/security-invariants/leader-delegate-input-groups.md` Rules 3,5,6; Property 7 | VERIFIED |
| F12 | Range bounds are compile-time, `0<=min<=max<=512`, lowered to an unrolled loop. | AG `docs/entry-clause-ranges.md` "Compile-time bounds" | VERIFIED |
| F13 | Silverscript v1.0.0 SECURITY.md still says "experimental and has not reached its first stable release"; no audit text found. Argent README: "not yet release-ready ... will still need further audit". Kaspa docs: "start in Silverscript" for production; Argent "design direction and prototype". | SS `SECURITY.md:3-5`; AG `README.md:38-43`, `SECURITY.md:5`; https://docs.kaspa.org/toccata/argent | VERIFIED / VERIFIED(web) |
| F14 | KCC-20 is Final (created 2026-08-21): state {amount, owner, owner_scheme, borrow_scheme, borrow_guard, extension_commitment}; default 3 inputs/3 outputs; supply conserved by transfer; "does not define a minting model", no burn, and does not say how a controller learns the token covenant id. | https://raw.githubusercontent.com/kaspanet/kccs/main/kcc-0020.md | VERIFIED(web) |
| F15 | Silverscript KCC20 book: "examples, not a production token standard". Mint = a `isMinter` branch owned by a controller covenant id; ONE KCC20Minter covenant bound by `init` using `OpOutputCovenantId(0)` in the asset genesis tx; mint is exactly 1 asset input -> 2 asset outputs. | SS `docs/kcc20-book/src/introduction.md`, `kcc20-overview.md`, `kcc20-minter-contract.md` | VERIFIED |
| F16 | Argent KCC20 example: `MinterProxy` stores ONE `controller_id`, `mint` requires `controller_id.co_spent()`; "KCC20 bootstrap with spawns" and "Launch proofs" are follow-ups, not shipped. | AG `examples/icc/kcc20_asset.ag`, `minter.ag`; `docs/followups.md` | VERIFIED |

## 1. Problem 1 (BLOCKER): vault + oracle co-spend is impossible as written

Confirmed. VERIFIED by reading `argent/build/enrk_a_vault/sil/Vault.sil` (liquidate/withdraw:
`OpCovOutputCount(oracle)==0`) and `PriceRound.sil` (`use` requires `OpAuthOutputCount(active)==1`, `sweep` 2),
plus F3/F4: a spent oracle input that is continued produces a continuation output with the oracle id, so the
count is >=1. Contradiction is structural. The `observes` block in `examples/enrk/a/vault.ag` declares only
`inputs`, and Argent lowers "no declared outputs" to `OpCovOutputCount == 0` (COMPILED, below).

Fixable with current primitives: YES. The canonical pattern is in AG `examples/icc/minter.ag` (observer
declares the foreign `outputs {...}` and `require asset.outputs become {...}`) and `docs/icc-semantics.md`
("Observes").

Design 1.A (recommended first): vault declares the oracle output and requires it to become the same state.
- COMPILED (scratchpad `exp/fix/vault.ag`): add to `liquidate`
  `outputs { round: OracleFeed::PriceRound }`, `PriceRoundState prev_round = state(oracle.inputs.round);`
  `require oracle.outputs become { round <- OracleFeed::PriceRound(prev_round) };`.
  Generated Sil now has `OpCovInputCount==1`, `OpCovOutputCount==1`, `OpCovOutputIdx(oracle,0)` and
  `validateOutputStateWithInputTemplate(...)`. `argentc build` succeeds.
- Cost (argentc inspect): Vault script 805 B -> 964 B (+159); `liquidate` sigscript 815-831 -> 974-990 B.
- Attempt `require(oracle.outputs.round.value == oracle.inputs.round.value)` did not compile
  ("undefined identifier: oracle"); value equality is already enforced by `PriceRound::use` itself, so it is
  not needed for soundness on the oracle side. `withdraw` needs the same edit (it still shows `==0`).
- Pros: smallest diff, uses documented pattern, oracle `use` stays untouched. Cons: +159 B per vault spend;
  the observe is closed ("exactly one oracle input"), so one liquidation tx can read only one price UTXO
  (fine: K vaults can share that single input, each checks count==1 and reads the same idx - UNVERIFIED).
- Mass (DERIVED, per-input overhead of 141 B = 389 B/pair - 248 B sigscript from the 1,556 transient/input
  ladder in `REMEASUREMENT-2026-09-15.md` s2): oracle pair 389 B + vault input about 1,040 B + payout 50 B +
  94 B fixed = about 1.6 KB, transient about 6.4k of 1M. Extra vault sharing the same oracle input: about
  1.1 KB = 4.4k transient, so about 200 vaults/tx by transient (compute per vault NOT measured).
  Fee floor ~100 x max(compute, 2 x bytes) (F8) = under 0.01 KAS.

Design 1.B: put Vault and price UTXOs in ONE app (one covenant id), liquidation is a coordinated leader entry
that `consumes { price: Follower }` and `emits { price_out: Follower }`, Follower has a `delegate read()`.
- COMPILED (`exp/inapp/app.ag`): Vault script 660 B, Follower 478 B, `liquidate` sigscript 672 B,
  `Follower::read` 490 B. No covenant-id source needed at all, so Problem 2 (oracle id) disappears.
- Pros: smaller scripts, no cross-app id binding, price identity is Rule 1 actor-template authentication
  (AG leader-delegate doc). Cons: Rule 3/5 close the input group: exactly one vault + one follower per
  liquidation tx (no K-vault batching), and the follower `use` can no longer be co-spent with anything
  (`|I(c)|=1`). The price follower must be re-emitted by the vault entry (extra checks per vault entry).
  Not executed; whether `delegate` on a different actor from the leader is accepted by the runtime resolver
  not tested.

Design 1.C (rejected): add a `read` entry with `emits none` to the oracle. It would let anyone burn a price
UTXO, and its "must be co-spent with a vault" guard re-creates the oracle<->vault template cycle noted in
`examples/enrk/a/oracle.ag` comments. Do not use.

Must still be measured: execution of the fixed liquidation tx in `argent-runtime` (compute/transient), the
`withdraw` path, and that `use` + vault co-spend passes the real script engine (the repo harness only
measured `use` ladders; see `REMEASUREMENT` s6.4, s5.1 for the harness defect).

## 2. Problem 2 (Q1c): oracle id not a constant; asset -> vault mint binding

Confirmed that a covenant id source must be a state field or entry argument (REMEASUREMENT s4; compiler
message). Consequence: nothing but lineage can guarantee the id is the right one.

### 2a. Binding vault -> oracle (and asset)
Fixable: YES, through genesis/lineage, not constants.
- Mechanism (VERIFIED): `spawns ... by id` makes consensus derive the child's id from the parent's
  authorizing outpoint and the whole ordered output group, so the parent writes the child's state and the
  child cannot lie about its parent (AG `docs/security-invariants/README.md` "Genesis spawns", Claims 1-2;
  KIP-20 "Covenant ID Derivation").
- Design 2.A (single lineage V, recommended to prototype): ALL vaults are UTXOs of one covenant id V. V is
  created once by a bootstrap that writes `oracle_id` and `asset_id` into the state. A new vault is a
  CONTINUATION (split) from an existing V UTXO ("nursery slot"), and its script must copy `oracle_id` and
  `asset_id` (`validateOutputState`). A forged vault needs a V input, so cannot exist. This also removes the
  "MinterProxy can store exactly one id" limit (ORACLE-BINDING s4): proxy.controller_id = V is a single id
  that covers the whole population. Contention moves to nursery slots (pre-split many, like price UTXOs).
  Status: design only (UNVERIFIED). Needs: bootstrap tx order (V genesis, oracle genesis, asset genesis via
  `spawns`), launch proof by hand (AG followups "Launch proofs" not shipped).
- Design 2.B (oracle spawns vaults, ORACLE-BINDING s6b): needs the oracle template to contain the vault
  template and the vault to observe the oracle template => cycle (comment in `examples/enrk/a/oracle.ag`).
  Only works if both are actors of one app (that is Design 1.B). Not recommended standalone.
- Design 2.C (factory, ORACLE-BINDING s6a): clean anchor but every vault creation contends on the factory;
  acceptable only if factory UTXO is replicated into many lanes. Fall-back option.

### 2b. Binding asset -> vault (can a forged vault mint?)
This is the real open problem and it is NOT solved by current docs.
- F14/F15/F16: KCC-20 Final has no mint model; Silverscript KCC20Minter is an example with one minter
  covenant; Argent bootstrap-by-spawns is a follow-up. So the only supported pattern is "asset stores one
  controller id and requires it co-spent".
- Hazard found (VERIFIED reasoning from F10, F11): `co_spent()` proves presence of ANY input of V, not that it
  is the vault's mint entry (Property 7: entries on the same actor are indistinguishable). Under Design 2.A
  an attacker can co-spend the proxy with ANY V UTXO in an unrelated entry (for example the price follower's
  `use` or a vault `withdraw`) and the proxy accepts an arbitrary mint. Mitigations (all UNVERIFIED, untested):
  (i) every non-mint V entry must `require(OpCovInputCount(asset_id)==0)` (asset_id must then live in every
  V actor state); (ii) route mint authority through a dedicated tiny covenant G ("mint gate", the Argent
  `Minter` shape) whose only entry observes V and checks the vault's debt delta, and make the proxy trust G;
  G is then a lane set of M singleton UTXOs (contention bounded by M); (iii) have the proxy read the V
  input state by template (cycle between apps unless handles are used).
- Burn/repay: KCC-20 has no burn; the Silverscript minter branch can decrease supply (F15) but Argent's
  example KCC20 has no burn path (read `kcc20_asset.ag`). A repay path must be designed.

What must be measured: a bootstrap + mint test in argent-runtime (does not exist; followups.md says the
Silverscript test `kcc20_covenant_minter` uses 2 txs), and a negative test for the co-spend hazard.

## 3. Problem 3: round transition not atomic (sweep 1->2)

Confirmed (VERIFIED: PriceRound.sil `OpAuthOutputCount == 2`; REMEASUREMENT s6.1). Also the 642 figure
measures only `use` consumption, not republication.

Key observation (VERIFIED reasoning): atomic transition alone does not remove stale prices. A price UTXO is
replicated by `use` (identity) and has no expiry; the script cannot express "not after" because time opcodes
give only lower bounds (lock_time, OpTxInputDaaScore; F9). Any old follower the publisher leaves unspent stays
valid forever, so an owner can `withdraw` against a stale high price. Therefore the sweep must provably consume
EVERY live follower.

Design 3.A (atomic N-way sweep with completeness): leader + follower actors.
- COMPILED (`exp/atom`, `exp/two`): one-actor version `sweep_all` with `consumes {olds: PriceRound[0..=N]}` /
  `emits {next: PriceRound[1..=N]}` compiles, but the redeem script grows about 215 B per slot (N=8: 2,061 B;
  N=128: 27,869 B) and EVERY spend carries it in its sigscript (use sigscript 27,877 B at N=128). Not scalable.
  Two-actor version (`exp/two`, N=128): Leader 99,903 B (used once per round), Follower 514 B,
  `Follower::use` sigscript 522 B, `Follower::follow` (delegate) 527 B. Range max is 512 (F12; N=640 rejected).
- DERIVED mass: per extra follower about (527+141) x 4 = 2.7k transient; Leader ~100 KB x 4 = 400k;
  N=128 round about 740k of 1M transient (fits); upper bound about 160 followers/round (Leader ~780 B/slot
  + follower ~670 B per slot = 5.8k transient/slot). Fee about 100 x 2 x 186 KB = 0.37 KAS per round.
  At one round per 10 s that is about 3,200 KAS/day; per minute about 530 KAS/day (DERIVED, tune cadence).
- Completeness: give each follower a `slot` field (0..N-1) and require the leader to check the consumed
  followers' slots are exactly 1..N-1 (indexed access `olds[i]` is documented, AG `entry-clause-ranges.md`;
  the loop form was not compiled - UNVERIFIED). `use` preserves slot, so exactly one live UTXO per slot.
- Constraints: `PriceRound` becomes a leader actor, so `use` is 1 input per tx (F11); this is harmless because
  a vault tx touches one price UTXO. The earlier "oracle must remain non-leader" note (ORACLE-BINDING s7)
  protects an N-input `use` batch that no consumer needs. Vault must observe `Follower` only (otherwise Leader
  `use` costs 400k transient). Delegates cannot use consume ranges in v1 (AG ranges doc).
- Pros: restores the atomicity claim, bounded staleness is not needed for completeness. Cons: N<=~160 not
  642; Leader is a 100 KB script (audit surface, loop expansion of generated code); requires publisher
  liveness; not executed.

Design 3.B (hierarchical / lazy re-pricing): keep the 1->2 `sweep` but treat a round as a tree; followers carry
`round` and the vault accepts only followers whose `round` equals a value in a SINGLE authoritative
head UTXO that must also be co-spent. Reintroduces global contention (head UTXO) - only viable with low
liquidation rate. UNVERIFIED.

Design 3.C (single price UTXO, N=1): no stale copy possible, price in state (variant B) or value; contention
on one UTXO but K vaults can share one read per tx and the tx re-creates it. Throughput depends on how fast
chained spends of the same outpoint are accepted across a DAG at 10 BPS: UNVERIFIED, must be tested on TN10.
Simplest to audit; recommended baseline to compare against.

## 4. Problem 4: KIP-9 100k standard mass and batch size

The audit's claim needs correction on two points (VERIFIED by RK code, F8):
1. The 100k per-dimension cap applies to compute AND transient (and storage), not compute alone.
   DERIVED with the ladder constants (A: 94/376 fixed, 759 compute, 1,556 transient per input;
   B: 839 / 1,876): A compute 131, A transient 64, B compute 119, B transient 53. So under a 100k cap the real
   N is 64 (A) / 53 (B), not 120-130 (which is compute-only).
2. In RK a41a333 the cap is not in force after Toccata: `standard_transaction_mass_cap` returns None from 30
   minutes before activation and "ever after". Toccata is active on mainnet since 2026-06-30 (F1, F2), so
   the practical ceilings are the block limits, 642 (A) / 532 (B) by transient (REMEASUREMENT s2), and tx
   inputs <=1000. Caveat: node releases after a41a333 (v2.0.1+) may differ - UNVERIFIED; check with
   `getMempoolInfo`/a testnet submission of a 300k-mass tx. KIP-9 itself never labels 100k as consensus (F7).
3. A near-block-sized tx (99.9% of transient) is a block-mate-free tx; Q4 of issue #46 (will miners include
   it?) is still unanswered. Needs TN10/TN12 test with realistic fee.
4. New data from this study: under Design 3.A the safe N is about 128-160, set by Leader script growth, not
   by the mempool cap. Under 3.A with the old 100k cap, N would be about 20 (Follower 2.7k each) - another
   reason to confirm the cap relaxation before relying on it.

## 5. Problem 5: icr_percent division by zero and overflow

Confirmed and worse than stated.
- `icr_percent = collateral_sompi * price * 100 / PRICE_SCALE / debt_units` (Vault.sil). Intermediate product
  overflows i64 (9.22e18) when collateral x price x 100 > 9.22e18. With price 1e7 (= 0.10 per unit at
  PRICE_SCALE 1e8) overflow starts at collateral about 9.2e9 sompi = about 92 KAS (DERIVED). Any realistic
  vault is outside the safe range.
- Behaviour: at engine level overflow/div0 are errors (F5), but Silverscript calls them undefined behaviour
  and permits folding them away so the spend can SUCCEED (F6, quoted). Both outcomes are bad for an immutable
  contract: fail = vault funds frozen (no withdraw, no liquidation); fold = checks bypassed. Also a
  `debt==0` vault (fully repaid) makes `withdraw` hit the division - the owner cannot exit.
- Fix within current primitives: YES.
  (a) explicit guards: `require(debt > 0)` on the liquidate path; on `withdraw` branch `if (debt == 0)` skip
  the ratio check; (b) bound inputs (`require(collateral <= C_MAX)`, `price <= P_MAX`) so the product fits;
  (c) rewrite as cross-multiplication with pre-scaled operands (for example compare
  `(collateral/ 10^k) * price * 100 >= ICR * debt * (PRICE_SCALE/ 10^k)`) and choose k so that
  C_MAX x P_MAX x 100 < 9.2e18; (d) if more range is needed, a two-word multiply (hi/lo 32-bit limbs) built
  from OpMul/OpDiv - costs more mass, not measured.
- What must be measured: property tests at extremes (collateral up to 2.9e17 sompi, price range, debt 0/1),
  both in the language semantics and in the compiled Sil with optimisation enabled (UB folding).
  `docs/design/UNDEFINED-BEHAVIOUR-EXPOSURE.md` already lists these as open; this study adds the
  92 KAS figure.

## 6. Prior art and ecosystem state

- No Kaspa L1 stablecoin, CDP or price-oracle covenant was found. Searches returned only generic Silverscript
  use cases (escrow, vesting) - SECONDARY, negative result; one social post mentions a vault + covenant token
  (UNVERIFIED lead).
- Reference token code: Silverscript KCC20 + Minter (examples), Argent KCC20 + Minter + open_icc + DEX in
  `argent-playground` (not audited; no audit report found).
- Audits: Silverscript v1.0.0 SECURITY.md "experimental" (F13); Argent "not release-ready" (F13). No
  third-party audit of either found.
- KCC-20 is Final but has no minting/burn/controller-binding (F14). This repo's
  `EXECUTION_TARGET_ASSESSMENT.md` s5 says KCC-0020 is a draft with a supply-split defect: that appears
  STALE against kccs main (status Final, created 2026-08-21); re-check before citing.
- Igra: public mainnet announced 2026-03-19 (press releases, SECONDARY). Exit limits quoted in
  `EXECUTION_TARGET_ASSESSMENT.md` s3 (Guardian multisig 48-72 h, KasExitBridge 20 exits or 200k KAS per
  ~25 h) come from Igra docs as cited there; NOT re-verified here (SECONDARY).
- KIP-21 lanes (50 lanes/block, per-lane gas) says nothing about covenant-id contention (KIP-21
  "Contention and transaction inclusion", VERIFIED(web)). So contention behaviour of many spends of one
  covenant id is UNVERIFIED and needs a testnet experiment.

## 7. Verdict

Technically: a CDP with an oracle read, vaults and a controlled mint is expressible on Kaspa L1 with current
primitives, but only after redesign of four of the five audited problems, and nothing of it has been run
end to end.
- P1 fixable now (compiled). P5 fixable now (code discipline + tests). P4 largely a non-issue after Toccata
  if the node cap relaxation holds (to be tested). P3 fixable but the scale is about 128-160 slots per atomic
  round, not 642, and needs a completeness check. P2 partly fixable: vault->oracle binding via lineage is
  sound; asset->vault mint authorisation has no shipped pattern and a presence-vs-scope hazard.
- Ecosystem: unaudited toolchain (Silverscript v1.0.0 experimental, Argent prototype), KCC-20 without mint
  model, no launch-proof tooling, no live comparable application, mempool/miner behaviour for near-full
  blocks unknown. For an immutable, unpatchable stablecoin that is a high risk today. Verdict: L1 is
  feasible as a TESTNET prototype; NOT shippable as immutable money today.
- Igra EVM: execution model is easy (Solidity, aggregate state, recovery mode, pro-rata reserves), but
  collateral is bridge-custodied and exit-throttled (per the repo's own assessment), so size must be capped
  at about 6-18M KAS; this is a bounded, disclosed trade, not a trustless one.
- Recommended next steps (smallest first): (1) argent-runtime test of the fixed liquidation co-spend
  (Design 1.A) with correct harness binding; (2) property tests for icr_percent; (3) TN10 test of a
  >100k-mass tx with realistic fee; (4) prototype Design 2.A + gate (2b ii) and the negative co-spend test;
  (5) measure Design 3.A with N=128; (6) ask Kaspa core devs the narrowed question in ORACLE-BINDING s8
  plus the "presence vs scope" question. All of these need owner validation before any change in the repo.

## 8. Not verified / limits of this study
- No tx was executed; all mass figures are DERIVED from the published ladder constants and compiled script
  sizes. Compute mass of the vault scripts and of Leader loops is unknown.
- Web pages were read through a summarising fetcher; quotes should be re-read before external citation.
- Node versions newer than rusty-kaspa a41a333 were not inspected.
- Mainnet activation confirmed from the release notes and a newsletter, not from a live node.
