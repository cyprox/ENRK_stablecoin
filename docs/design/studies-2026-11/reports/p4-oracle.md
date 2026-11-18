# P4 audit: oracle and covenants (read-only)
Legend: [V]=verified by me (run/read/computed), [D]=taken from doc, [U]=unverified.
Repo untouched. Build used CARGO_TARGET_DIR and TMPDIR in scratchpad, offline, in the nested clone /Users/simoes/ENRK_stablecoin/argent (e76ee07, pinned rusty-kaspa a41a333, silverscript 3ed9733).

## 0. Reproduction
- [V] argent/ builds offline. Ran `enrk_mass` for A and B with the clone's copy of the harness, which already has the per-input binding fix (argent/tests/enrk_mass.rs differs from /Users/simoes/ENRK_stablecoin/tests/enrk_mass.rs only by that fix, i.e. harness-binding-fix.patch). examples/enrk is identical in both trees.
- [V] Ladder N=1..512 executes. Per-input costs are exact: A 759 compute / 1556 transient, B 839 / 1876, fixed 94 / 376. A at N=512 transient 797,048, B 960,888. Sigscript 248 B / 328 B. N=1024 fails on compute mass. Storage table (k=1/.99/.9/.5) matches the docs to the unit, including 711,040 at N=640 (extrapolated: 64 rows -> 71,104, x10; formula gives 711,040).
- [V] `argentc build probe_const_covid.ag` gives the quoted error. Vault scripts are 805 B (A) and 886 B (B); sigscripts 815-831/882-906 (A), 896-912/963-987 (B).
- [V] Ceilings 642/532 (transient) and 658/595 (compute) are correct arithmetic, with limits 500,000/1,000,000/500,000 printed by the harness.
- NOT reproduced: any N above 512 was never executed. The committed harness has LADDER = [1,2,4,...,1024] (tests/enrk_mass.rs:33).

## 1. Findings

### BLOCKER-1 (verified by reading, not executed): vault liquidate/withdraw cannot co-spend any oracle UTXO
- argent/build/enrk_a_vault/sil/Vault.sil:46-47 (liquidate): `require(OpCovInputCount(oracle_cov_id) == 1); require(OpCovOutputCount(oracle_cov_id) == 0);` (the observes block declares no outputs).
- argent/build/enrk_a_oracle/sil/PriceRound.sil:21 `use` requires `OpAuthOutputCount(activeInputIndex) == 1` plus an output with the same value and scriptPubKey. `sweep` (:36) requires 2 outputs. Both leave at least one output carrying the oracle covenant id.
- OpCovOutputCount counts all outputs with that covenant id (rusty-kaspa a41a333 opcodes/mod.rs:1549, covenants.rs:87). So any tx satisfying the oracle input fails the vault's `== 0`, and vice versa.
- No doc mentions this. The "both variants compile and execute" claim (UPDATE.md:36-47) covers compilation only; no vault+oracle transaction was ever built.
- Recommendation: build and execute a real liquidation tx (REMEASUREMENT §9 item 4 does not mention this) before any more claims about the vault-oracle composition. Declare `outputs { round: PriceRound }` in `observes`, or restructure.

### IMPORTANT-2: "B storage mass is always 0" and the A/B trade-off rest on a shape no entry can produce
- a/oracle.ag:31 and b/oracle.ag:22: `use` forces `next.value == self.value`, so N->N value-changing rounds (the 711,040 table, UPDATE.md:148-155) are impossible. A price change goes only through `sweep` (1->2).
- b/oracle.ag:27-28 says conserved-value splitting is "the shape KIP-9 charges nothing for". KIP-9 (fetched, [V]) says only that "compounding several outputs into an equal or smaller number of outputs of equal value will never incur storage mass". A 1->2 split is the opposite case. By the formula C(sum 1/o - 1/v), splitting 1e8 into 5e7+5e7 costs 20,000x2 - 10,000 = 30,000 units per sweep (computed, not run). Deeper binary splits cost far more: 1e8/640 = 156k sompi per leaf gives C/o = 6.4M. B's "zero at any price" holds only for a hypothetical value-preserving N->N republication.
- The 711,040 and "~450 at -10%" figures also depend on the arbitrary UTXO_VALUE = 1e8 (harness :31); storage mass scales as 1/value. At 5e6 sompi it is 20x larger. ORACLE spec §2.5.2 admits "artefact ... not tested", but UPDATE.md:157-164/243 and COMMENT.md:38,50 state it without caveat.
- Internally consistent [V]: 500000/1111 = 450; 640/530 = +20.75%, 642/532 = +20.7% ("21%"). But the 21% is flat-market only; at -10% per round A (450) is below B (532), and the A-vs-B table (UPDATE.md:192-198) uses 530, not 532. Also k is "per round", and a 10% move in one 100 ms round is implausible. The A fall threshold for N=640 is about -7.3%/round.
- Recommendation: restate the trade-off as conditional on UTXO_VALUE and on the unbuilt republication shape. Measure sweep mass before choosing.

### IMPORTANT-3: operational claims contradict each other and ignore the standardness limit
- UPDATE.md:122,125, COMMENT.md:11,42 and 110: "a new round every ~100 ms ... not a bottleneck", while the same text says a round takes 99.6-99.93% of a block's transient mass. One round per block would use all block capacity.
- KIP-9 (fetched [V]): standard tx mass limit 100,000, block limit 500,000. A 642-input tx has compute mass 487,372 and transient about 999,328. If mempool standardness applies (U: Toccata may have changed it), such a tx is not relayed. Rough standard-limit N from compute alone: A ~131, B ~119 (computed). L1 spec §2.4 mentions the 100,000 limit, but Q4 and the "Ceiling on N" table (spec §2.5) ignore it. [Resolved: no 100,000 standard-mass cap after Toccata (r1-consensus section 1); a 487,182-compute transaction was accepted on testnet-10 (econ-x1b).]
- UPDATE.md:88 "Compute mass remains 3-4% under limit at both breaking points" is false [V]: A at 640 is 2.8% under, B at 530 is 11.0% under (N=540: 9.4%).
- REMEASUREMENT.md:67 and COMMENT-2.md:109: "99.93%" for both. B is 998,408/1,000,000 = 99.84% [V]; 99.93% is A only.
- 560/600/640/645 and 520/530/540 are NOT rungs of the committed LADDER (powers of 2). REMEASUREMENT.md:60-62 ("rungs of a test ladder") and UPDATE.md:71 ("Measurements from oracle_round_scaling") are inconsistent with the committed harness. Those rows reproduce by linear regression only [V]. Nothing above N=512 was executed, and "fails" at 645/540 was never observed. The patch's own claim is correctly limited to N=512.

### IMPORTANT-4: undefined behaviour in icr_percent (doc analysis confirmed)
- a/vault.ag:27 and b/vault.ag:27: `return collateral_sompi * price * 100 / PRICE_SCALE / debt_units;`. Call sites: :44 (liquidate), :59 (withdraw), both variants. [V] by reading.
- Division by zero when debt == 0, and overflow of the left-associative chain: both confirmed. Thresholds 922 KAS and 9.22 KAS are correct for price = 1e8 only (price is a free input; at 5e6 the ceiling is 20x higher). The doc states the assumption.
- Engine: OpMul uses checked_mul and OpDiv checked_div, so the script fails (rusty-kaspa mod.rs:769-789) [V]. The "not exploitable, inoperable" conclusion is right. A vault with debt==0 cannot withdraw (a/vault.ag:59 divides by debt): user funds are locked forever [V by reading]. Severity is important for the design, minor for the stub.
- Other items [V]: a/oracle.ag:46 and b/oracle.ag:40 `round + 1` (as the doc says); b/oracle.ag:36-45 `left_value < self.value` is fine. The genesis price of variant B is unchecked (doc right).
- Doc nits: UB doc says "361-line"; the file is 360 lines. §1 says "Four of the eight categories" but lists five. The sigscript malformed-signature concern (UB-EXPOSURE §3) is correctly labelled untested [U].
- Recommendation: one `require(debt > 0)`, bound operands, divide early (a design decision, not made).

### IMPORTANT-5: oracle freshness and DoS, beyond the atomicity point the docs already admit
- Sweep confirmed non-atomic [V]: PriceRound.sil:36 requires exactly 2 outputs. Additionally, a 1->2 sweep can only grow the population; there is no merge, so a steady N->N republication is not expressible. The docs' "batch N sweeps" yields 2N outputs.
- The vault never reads or checks `round` (a/vault.ag:44, 59), and old-round UTXOs stay spendable via `use` (any holder can recreate them), so stale prices stay usable. Spec §2.3 freshness depends on atomic replacement that does not exist.
- a/oracle.ag:30-33 has no vault co-spend condition (a). Anyone can re-spend oracle UTXOs for the cost of a fee, invalidating the publisher's pending sweep (outpoint conflict). The spec says (a) deters spam; the docs record the omission but not this consequence.
- a/oracle.ag:49-50: `unrestricted(left.value); unrestricted(right.value)` allows siblings with different prices in one round [V by reading].

### Q1c and "can a forged vault mint ENRK?" (ORACLE-BINDING.md)
- The reframing is logically sound: a forged vault harms only its creator unless it can mint [analysis V]. The single-covenant-id MinterProxy limit is cited from Argent docs [D, not re-read in full]. The `spawns` and genesis-id invariants are cited from Argent's docs [D].
- Gaps: it never notes that even the correct-oracle path is currently unsatisfiable (BLOCKER-1). Candidate (b), "oracle spawns vaults", is correctly flagged as an untested hypothesis. The Sutton X thread (11 Sep) is [U].
- Compiler message in §1 [V].

### Non-leader constraint (ORACLE-BINDING §7, REMEASUREMENT §6.2)
- Argent's doc defines "leader actor" as an actor named by a delegate [V], consistent with the claim. PriceRound.sil contains no |I|=1 check [V]. Note the generated comments label every entry "leader entry (1:N)", a different sense (entry kind); easily confused with the actor-level rule. Minor: clarify in the docs.

### KIP citations
- [V] KIP-9: "compounding ... never incur storage mass" quote is accurate; formula C(sum 1/o - |I|^2/sum v), C=1e12 accurate; mempool 100,000 / block 500,000 accurate. Caveat: Spec §2.4 quotes only the compounding case and applies it to a sweep that splits.
- [V] KIP-20: opcodes (OpInputCovenantId, OpAuthOutputCount, OpAuthOutputIdx) and the quote "A common pattern is a single covenant input authorizing one or many covenant outputs" are accurate. KIP-20 describes a leader/delegate pattern.
- [V, WRONG in docs] EXECUTION_TARGET_ASSESSMENT.md:35 and :12, and L1 spec :17-21 ("Both KIPs shipped with Toccata"): KIP-17 states "The following KIP 10 opcodes were already active before Toccata". KIP-10 did not ship with Toccata.
- [V, NOT FOUND] EXECUTION_TARGET:46 presents as a KIP-10 quote "There are no opcodes to read unspent UTXOs without spending them..." I could not find that sentence in KIP-10 or KIP-17 on master. It may come from a secondary source; as presented (italic quote, "KIP-10:") it is misattributed [U on origin].
- Toccata date: docs say "around June 5-20" (EXECUTION_TARGET:~44); secondary sources report mainnet activation June 30, 2026 [U, no primary source]. Docs also say "activated" while giving a range.
- KIP-16 (ZK), KIP-21 (sequencing): existence is consistent with Toccata release coverage; content not verified.
- KIP numbers in the quoted opcodes: KIP-10 opcode hex (0xb3, 0xb9, 0xbe, 0xbf) match [V].

### Other consistency checks
- 1,046 B / 1,206 B totals are consistent in all docs [V: 805+241, 886+320 = 1046, 1206]. 0.10%/0.12% of 1 MB correct. "Vault 805 B" is the compiled script; sigscripts are separate.
- 642/532 and 658/595 consistent across REMEASUREMENT, UPDATE, spec, COMMENT-2. UPDATE.md and COMMENT.md still headline 640/530, with a correction note in UPDATE only; COMMENT.md (older, "Draft/posted?") has no correction. Check which was actually posted [U]. COMMENT.md:59 uses a path `argent-maquette/` not present here.
- harness-binding-fix.patch: logic correct [V] (my run used the fixed copy; fails-at-N=2 for the old version not re-run, but PriceRound.sil:21 confirms why). The patch has bare `@@` hunk headers and will not apply with git apply as written (minor). The patch email address is the author's, not a secret.
- UPDATE.md:47 attributes "ICC (interchain covenant capability)" as the expansion of ICC; Argent docs use "inter-covenant communication" semantics [U on the expansion; minor].
- UPDATE.md:242-243 Summary says "Three of the four questions" while the table lists five rows; minor.

## 2. Not checked
Real Schnorr sweep, liquidation tx mass, Testnet-10, the stress-test numbers (102.7M KAS/1000 vaults), Argent security-invariants details beyond leader/delegate rules, the Sutton thread, KIP-16/21 content.
