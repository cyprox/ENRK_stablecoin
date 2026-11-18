# Re-measurement and Toolchain Audit — September 15, 2026

**Status:** Complete. Every figure below was produced on this date, on the
toolchain revisions named in §1, and can be reproduced with §8.

**Why this document exists.** The oracle measurement of September 6 was made on
Argent `d08e52d`. Argent has since moved to `e76ee07` and, with it, from
Silverscript `c7d17a1` to the released **Silverscript v1.0.0**. This document
re-establishes every published figure against the current toolchain, corrects
what was wrong, and records what the exercise found that nobody was looking for.

**The short version.** The September measurement was correct. All seven published
rows reproduce to the unit. What does not survive is the *reproducibility* of the
published procedure, three transcribed figures in `L1_NATIVE_REDUCED_SPEC` §2.5,
and one claim in §2.3 that the generated code contradicts.

---

## 1. What was measured, and on what

| | |
|---|---|
| Argent | `e76ee07` (September 14, 2026) — was `d08e52d` (September 2) |
| Silverscript | `3ed9733` = **v1.0.0**, tagged September 9 — was `c7d17a1` (v1-rc1) |
| rusty-kaspa | `a41a333` — **unchanged**, so consensus parameters and `MassCalculator` are identical across both measurements |
| Host | macOS, Rust toolchain per `rust-version = 1.94.0` |

Because the consensus side did not move, any difference between the two
measurements is attributable to the compiler alone.

---

## 2. The September figures reproduce exactly

Ten points of the scaling ladder (N = 1 … 512) give a perfectly linear cost. The
regression is exact — not approximate — on every point:

| | fixed cost | per input (compute) | per input (transient) | script | sigscript |
|---|---|---|---|---|---|
| **Variant A** | 94 / 376 | **759** | **1 556** | 241 B | 248 B |
| **Variant B** | 94 / 376 | **839** | **1 876** | 320 B | 328 B |

Applying these to the seven rows published in `GITHUB-ISSUE-46-UPDATE.md`
reproduces each one to the unit:

```
A N= 560  compute 425134 [OK]   transient  871736 [OK]
A N= 600  compute 455494 [OK]   transient  933976 [OK]
A N= 640  compute 485854 [OK]   transient  996216 [OK]
A N= 645                        transient 1003996 [OK]
B N= 520  compute 436374 [OK]   transient  975896 [OK]
B N= 530  compute 444764 [OK]   transient  994656 [OK]
B N= 540                        transient 1013416 [OK]
```

**Conclusion: the September 6 measurement was genuine and accurate.** Q2 and Q3
stand, on a toolchain two revisions and one language release later.

### 2.1 The true ceilings are 642 and 532

The published 640 and 530 are rungs of a test ladder, not maxima. Removing the
fixed transaction cost and dividing by the marginal cost per input gives:

| | ceiling | binding constraint | block transient consumed |
|---|---|---|---|
| Variant A | **642** | transient mass | 99.93 % |
| Variant B | **532** | transient mass | 99.84 % |

Compute mass would have allowed 658 and 595 respectively, so the September
finding holds: **transient mass binds, compute mass does not.**

The published figures are therefore correct and mildly conservative. Nothing
downstream needs revising on their account, but the method should be stated as
what it is: a marginal cost measured over ten points, not a division of a single
observation.

---

## 3. Script sizes are unchanged, to the byte

| | September 6 | September 15 |
|---|---|---|
| Vault A | 805 B | **805 B** |
| Oracle A | 241 B | **241 B** |
| Total A | 1 046 B | **1 046 B** |
| Vault B | 886 B | **886 B** |
| Oracle B | 320 B | **320 B** |
| Total B | 1 206 B | **1 206 B** |

Q3 is confirmed without drift: 0.1 % of the 1 MB limit.

---

## 4. Q1c holds, and the compiler now states it precisely

`probe_const_covid.ag` is still rejected under Silverscript v1.0.0:

```
argentc: entry `Probe::touch` observe `oracle` covenant id source must be
a `self.<field>` state field or entry argument of type `cov_id`
```

This is the authoritative formulation of Q1c and should replace every paraphrase
of it in this repository. The compiler names the two admissible sources: a state
field, or an entry argument of type `cov_id`. Neither is a compile-time constant.

---

## 5. Three defects found in this repository

### 5.1 The published harness cannot reproduce the published result

`tests/enrk_mass.rs`, as committed on September 6, binds **every** output to
authorizing input 0:

```rust
for _ in 0..n {
    context = context.actor_output("PriceRound", state.clone(),
        CovenantBinding::new(0, covenant_id), UTXO_VALUE);
}
```

`CovenantBinding::new`'s first argument is the authorizing input index
(`consensus/core/src/tx.rs`: `pub authorizing_input: u16`). The generated
`PriceRound::use` requires `OpAuthOutputCount(this.activeInputIndex) == 1`. With
all N outputs attributed to input 0, that count is N, and the transaction fails
at N = 2 with *"input 0 script failed: script ran, but verification failed"*.

This check is not new — it is present verbatim in the `.sil` fixtures committed
at `d08e52d`. The committed harness could therefore never have produced the
published ladder, on either revision. The working copy that produced it was not
the copy that was committed.

**Consequence.** The reproduction steps published on issue #46 do not reproduce.
Anyone following them gets a failure at N = 2. On a dossier whose central claim
is that it measured rather than argued, this is the worst possible defect.

**The fix** (one line, pending owner approval — see §9):

```rust
for index in 0..n {
    context = context.actor_output("PriceRound", state.clone(),
        CovenantBinding::new(index as u16, covenant_id), UTXO_VALUE);
}
```

`crates/argent-runtime/src/resolve.rs` shows outputs bound to distinct
authorizing inputs in a single transaction, so this is an intended usage.

### 5.2 Three transcription errors in `L1_NATIVE_REDUCED_SPEC` §2.5

The tables in `GITHUB-ISSUE-46-UPDATE.md` are right. The summary table copied
into the specification is not, in its variant B column:

| Figure | §2.5 says | Measured | Note |
|---|---|---|---|
| Compute mass per input, B | ~849 | **839** | the published tables already imply 839 |
| Transient mass per input, B | ~1 866 | **1 876** | the published tables already imply 1 876 |
| Signature script, B | 262 B | **328 B** | **internally impossible**: the witness carries the redeem script, which is 320 B |

The third is demonstrable without any measurement: a 262-byte signature script
cannot contain a 320-byte script, and the same document publishes 320 B two
tables later. Variant A's column is correct throughout.

### 5.3 `GITHUB-ISSUE-46-UPDATE.md` contradicts itself on cadence

§"Key Finding" states Kaspa runs at 10 blocks per second and that a full round
therefore publishes every ~100 ms. §"Remaining Open Questions" states "~10
seconds per block", giving one round per 10 seconds — a factor of 100 apart, in
the same document, on the number that determines whether the oracle is usable
for real-time liquidation. The 10 BPS figure is the correct one.

The same section renders the KIP-9 storage mass formula in terms of harmonic
means, which does not match the formula used elsewhere in this repository
(`C·(Σ(1/o) − |I|²/Σ(v))⁺`). The numbers in the storage table are unaffected;
the rendered formula should be corrected to the canonical one.

---

## 6. What the generated code revealed

### 6.1 The sweep is a 1→2 split, not 1→N

`argentc inspect` on the oracle reports, for both variants:

```
PriceRound::sweep [leader]
  outputs: left -> PriceRound, right -> PriceRound
```

and the generated Silverscript requires `OpAuthOutputCount(this.activeInputIndex)
== 2`. The round transition as written is **binary**.

§2.3 of `L1_NATIVE_REDUCED_SPEC` claims that "round R's UTXOs are consumed and
round R+1's are created atomically", and that this is what removes the
stale-price window. Reaching N children from one parent by binary splitting takes
⌈log₂ N⌉ ≈ 10 successive sweeps, therefore several transactions, therefore not
atomically.

**The atomicity claim does not hold for the construction as written.** It is not
necessarily unreachable — batching N independent sweeps into one transaction is
the obvious candidate, and is the same shape the `use` ladder validated — but it
has never been measured, and the contract as written does not express it.

**What N = 642 actually measures** is therefore the ceiling on *consumption*: N
independent USE spends batched into one transaction. The ceiling on
*republication* is unknown and will be lower, because `sweep` carries a
`checkSig` and two `validateOutputState` where `use` carries two equality
comparisons, and its signature script is larger (314 B for A, 396–412 B for B,
against 248 / 328 for `use`).

This was not measured in this session because measuring a binary sweep would
produce an exact number for a shape that cannot carry the claimed property. The
form of the split should be decided first. See §9.

### 6.2 A new structural constraint: the oracle must remain non-leader

Argent `e76ee07` formalises leader/delegate input-group rules
(`docs/security-invariants/leader-delegate-input-groups.md`). Rule 3 states that
an ordinary entry without a `consumes` clause, **on a leader actor**, requires
`|I(c)| = 1` — one input per covenant id per transaction.

`PriceRound` is not a leader actor today, so the rule does not apply and the
N-input batching that the whole construction depends on remains legal. Rules 5
and 6 are likewise not emitted for our entries: rule 5 requires
`entry.kind == Leader && !entry.consumes.is_empty()`, rule 6 requires the actor
to declare a `delegate` entry. Verified both by reading the emitter and by
inspecting the generated `PriceRound.sil`, which contains neither check.

**But this is now a design constraint to hold deliberately.** If `PriceRound`
ever acquires a `delegate` entry — for instance to implement a Stability Pool by
the KIP-20 delegation pattern discussed in §6.2 of the specification — then every
`consumes`-free ordinary entry on it falls under `|I(c)| = 1`, and the 1→N
construction dies. The oracle must remain non-leader. Nothing currently records
this.

### 6.3 The vault reads the oracle's state through a spender-supplied template

`argentc inspect` on both vaults reports, on both entries:

```
generated arguments: gen__oracle_feed__price_round_prefix_len: int
                     gen__oracle_feed__price_round_suffix_len: int
```

These are template lengths, supplied in the spender's signature script, feeding
Silverscript's `readInputStateWithTemplate` path. `UNDEFINED-BEHAVIOUR.md`
specifies that supplied template lengths must match the layout of the selected
input, and that a mismatch is undefined behaviour.

The authenticity of the price, inside the vault, therefore depends on two
integers provided by whoever spends — in generated code we did not write. This is
a question for audit, not an established defect, and it is concrete evidence that
an ENRK audit must cover two layers: our Argent source, and Argent's lowering.

### 6.4 Vault signature scripts are large, and the liquidation path is unmeasured

| Entry | Variant A | Variant B |
|---|---|---|
| `Vault::liquidate` | 815–831 B | 896–912 B |
| `Vault::withdraw` | 882–906 B | 963–987 B |
| `PriceRound::use` | 248 B | 328 B |

Transient mass tracks transaction size. A liquidation transaction is a vault
input of ~820 B plus an oracle input of 248 B, and **its mass has never been
measured**. N = 642 is the ceiling on a pure oracle round; the cost of the path
that actually matters is unknown.

---

## 7. Toolchain findings

### 7.1 Silverscript v1.0.0 is released, and is not audited

`v1.0.0` was tagged on September 9, 2026. The release notes describe an extensive
review, testing and standardisation process, and thank four ecosystem
contributors. The word *audit* does not appear — not in the release notes, and
not in any `.md` file in the repository. `SECURITY.md`, at the tagged commit,
still describes the language as experimental and not at its first stable release.
No audit report was found anywhere.

**The risk recorded in `PROJECT-STATE.md` therefore changes shape rather than
going away.** What improved is real: a tagged release with an explicit SemVer
commitment, rather than a moving `master`. What has not changed is that nobody
has audited a Silverscript covenant system for immutable deployment. Argent
states of itself that it requires its own audit and hardening after
Silverscript's.

### 7.2 The only unexplained difference between the two revisions

Variant A reproduces bit for bit. Variant B's marginal costs measured today
(839 compute, 1 876 transient, 328 B witness) are the values the September tables
already imply, so they are not a drift either. After correcting §5.2, **no
unexplained difference between `d08e52d` and `e76ee07` remains** for either
variant.

---

## 8. Reproduction

From a clean checkout, with `ENRK_stablecoin` as the working directory:

```bash
git clone https://github.com/argent-lang/argent && cd argent
git checkout e76ee07
mkdir -p examples/enrk
cp -r ../examples/enrk/* examples/enrk/
cp    ../tests/enrk_mass.rs tests/

# scaling ladder, both variants
ENRK_ORACLE=examples/enrk/a/oracle.ag cargo test --test enrk_mass oracle_round_scaling -- --nocapture
ENRK_ORACLE=examples/enrk/b/oracle.ag cargo test --test enrk_mass oracle_round_scaling -- --nocapture

# script sizes: build first, then inspect the build directory
cargo run --bin argentc -- build examples/enrk/a/oracle.ag --out build/enrk_a_oracle
cargo run --bin argentc -- build examples/enrk/b/oracle.ag --out build/enrk_b_oracle
cargo run --bin argentc -- build examples/enrk/a/vault.ag  --out build/enrk_a_vault
cargo run --bin argentc -- build examples/enrk/b/vault.ag  --out build/enrk_b_vault
cargo run --bin argentc -- inspect build/enrk_a_oracle
cargo run --bin argentc -- inspect build/enrk_b_oracle
cargo run --bin argentc -- inspect build/enrk_a_vault
cargo run --bin argentc -- inspect build/enrk_b_vault

# Q1c probe: must fail to compile
cargo run --bin argentc -- build examples/enrk/probe_const_covid.ag --out build/enrk_probe

# the generated Silverscript, which is what actually executes
cat build/enrk_a_oracle/sil/PriceRound.sil
```

Note that `argentc inspect` takes a **build directory or an `artifact.json`**, not
a `.ag` source file. The command published in `GITHUB-ISSUE-46-UPDATE.md` is
correct on this point; earlier drafts elsewhere were not.

**The scaling ladder requires the §5.1 fix.** Without it, both variants fail at
N = 2.

---

## 9. What is open, in the order it should be taken

1. **Apply the §5.1 harness fix and commit it**, so that the published
   reproduction steps work. Until then, issue #46 points at a procedure that
   fails.
2. **Decide the form of the round transition** (§6.1). Binary sweep with no
   atomicity, or N sweeps batched into one transaction. This is a design decision
   and it gates the next measurement.
3. **Measure the chosen sweep form.** This requires real Schnorr signatures in
   the harness: `argent-runtime` computes sighashes for verification but exposes
   no signing helper, so the test must sign with `secp256k1` itself. Roughly
   thirty lines in a new test, touching no contract.
4. **Measure the liquidation transaction** (§6.4). Vault input plus oracle input,
   full mass accounting. This is the path the protocol actually runs.
5. **Q1c / the binding problem**, reframed — see
   `docs/design/ORACLE-BINDING.md`. The question is not only "is the vault bound to the right
   oracle" but "does the ENRK asset accept a mint from this vault".
6. **Variant A or B.** Unchanged and still open. The measurement confirms the
   trade-off: A allows ~21 % more N and costs storage mass on a falling price; B
   is invariant.
7. **Q4 — block inclusion under contention.** Testnet-10, unchanged.

---

## 10. Undefined behaviour

A line-by-line audit of both variants against Silverscript's
`UNDEFINED-BEHAVIOUR.md` was carried out in the same session and is recorded
separately in
[`UNDEFINED-BEHAVIOUR-EXPOSURE.md`](UNDEFINED-BEHAVIOUR-EXPOSURE.md). Its
headline: `icr_percent` contains two reachable undefined behaviours, both vault
variants, both entries, and the compiler accepts it without a diagnostic.

---

**Author:** cyprox
**Licence:** GPL-3.0

Update 2026-11-17: the liquidation path and the sweep were measured on testnet-10 (AUDIT sections 6 P1 and 13.3b); whole-population refresh executed (ECONOMICS-VERIFICATION section 10.2).

Status 2026-11-17 of the items in section 9: 1 open (repo defect, owner go); 2 open; 3 done in part (sweep batches); 4 done; 5 open (ORACLE-BINDING); 6 open; 7 done on testnet-10 (mainnet untested).
