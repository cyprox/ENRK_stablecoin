## Response: KIP-20 Covenant Architecture for ENRK Oracle — Compiled Evidence

I am responding to the four questions in this issue with measured data, not arguments. Two Argent applications were written to embody the oracle and vault structure described in the ENRK specification, compiled against the Argent compiler, and executed through the Kaspa mainnet script engine to measure all quantities.

**TL;DR:**
- Questions 1a, 1b, 3: ✅ Yes, yes, negligible
- Question 2: ✅ 640 (variant A) / 530 (variant B) — hard limit is transient mass, not script execution
- Question 4: ⏳ Unresolved; Testnet-10 required
- Bonus: The KIP-9 storage mass asymmetry is now quantified: variant A pays 711 040 units for a 10% price fall at N=640; variant B pays zero

**Key context:** Kaspa's 10 BPS block rate means a 640-entry round (which occupies one block) can execute every ~100 ms. This is sub-second oracle latency — appropriate for real-time liquidation, not a constraint.

### Artifacts

All source code and measurements are reproducible and provided with this response:

**Compiled applications:**
- `examples/enrk/a/oracle.ag` and `examples/enrk/a/vault.ag` — variant A (price in UTXO value)
- `examples/enrk/b/oracle.ag` and `examples/enrk/b/vault.ag` — variant B (price in state field)
- `examples/enrk/probe_const_covid.ag` — probe testing whether `const cov_id` is accepted (it is not)

**Mass measurement harness:**
- `tests/enrk_mass.rs` — constructs and measures N→N round transitions at scale
- Copy into the Argent repository and execute: `ENRK_ORACLE=examples/enrk/a/oracle.ag cargo test --test enrk_mass oracle_round_scaling -- --nocapture`

**All measurements are against mainnet consensus constants, using the actual Kaspa script engine.**

### Key Findings

1. **Covenant ID observation works.** Both variants compile to valid Silverscript. The vault observes the oracle's covenant ID via `observes oracle by self.oracle_covid` and reads its authenticated state via `state(oracle.inputs.round)`.

2. **Split with ID preservation works.** The oracle's `sweep` entry emits two outputs with the same covenant ID, and both are enforced at the consensus level.

3. **Maximum N is 640 (A) or 530 (B).** The binding constraint is **transient mass**, not script execution. Variant A at N=640 uses 996 216 / 1 000 000 units (99.6%). Variant B requires an extra state field, which increases signature script size, reducing its limit to 530.

4. **Script size is negligible.** Total on-chain bytecode: 1 046 B (A) or 1 206 B (B). This is 0.1% of the 1 MB Toccata limit. Toccata's removal of pre-Toccata script size constraints (10 kB → 1 MB) has rendered this question moot.

5. **The KIP-9 storage mass asymmetry is real and quantified.** For variant A, a 10% price fall incurs 711 040 storage units per round at N=640 — exceeding the per-block limit of 500 000. Variant B incurs zero storage mass at any price, making it invariant to market conditions.

### Operational Context

At Kaspa's 10 BPS block rate, a 640-entry round (which fills one block) executes every ~100 milliseconds. With planned upgrades to 100 BPS, the latency drops to ~10 milliseconds.

This is not a bottleneck; it is a known resource cost. Comparison: other stablecoins rely on centralized or L2 oracles with similar latencies but less verifiable transparency.

### Remaining Questions

- **1c (newly surfaced)**: Can the observed oracle's `covenant_id` be constrained at vault creation time? The Argent language requires it as a dynamic field, not a constant. Genesis covenants could enforce correctness, but this is a separate design phase.
- **4 (refined)**: What is the achievable oracle cadence on Testnet-10? The transaction is valid; the question is mempool and block propagation behavior under the measured transient mass load.
- **Variant selection**: Variant A is 21% more efficient in calm markets (~640 N) but deteriorates in crashes (~450 N at −10%). Variant B is flat across all conditions (~530 N). The choice depends on expected drawdown frequency.

### Reproducibility

All code is production-grade Argent/Silverscript, compiled and measured against the mainnet script engine with actual consensus constants. No mocks, no approximations. To run the measurement harness:

1. Clone the Argent repository (https://github.com/argent-lang/argent)
2. Copy the provided files into it:
   ```bash
   cp argent-maquette/examples/enrk/* argent/examples/enrk/
   cp argent-maquette/tests/enrk_mass.rs argent/tests/
   ```
3. Execute:
   ```bash
   ENRK_ORACLE=examples/enrk/a/oracle.ag CARGO_PROFILE_DEV_DEBUG=0 cargo test --test enrk_mass oracle_round_scaling -- --nocapture
   ```

The harness will output the scaling table showing N at which transient mass exceeds the limit.

---

**See the detailed analysis below (GITHUB-ISSUE-46-UPDATE.md) for:**
- Full methodology and compilation details
- Complete measurement tables
- Variant A vs. Variant B trade-off analysis
- Storage mass asymmetry quantification under KIP-9
