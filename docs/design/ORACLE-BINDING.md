# The Oracle Binding Problem (Q1c), Reframed

**Date:** September 15, 2026
**Status:** Open. This document records what is known, what changed, and why the
question as previously written was the wrong one. It proposes no decision. Layer decided 2026-11-13 (Kaspa L1), so this question is now on the critical path. Sending the section 8 question to Kaspa core developers is an outward step that needs a separate owner go.

---

## 1. Where the question came from

The measurement of September 6 established, by the compiler refusing to build
`probe_const_covid.ag`, that a covenant id **cannot be a compile-time constant**.
Confirmed again on September 15 under Silverscript v1.0.0, with the compiler now
naming the admissible sources precisely:

```
argentc: entry `Probe::touch` observe `oracle` covenant id source must be
a `self.<field>` state field or entry argument of type `cov_id`
```

The consequence recorded at the time: each vault carries the oracle identity in
its own state, fixed at vault creation, and *nothing specifies what guarantees a
vault is created against the correct oracle*.

---

## 2. What Michael Sutton pointed at

On September 11, 2026, in a thread on X about parallel and replicated state
designs, Sutton was told that the open point in this construction was binding a
vault to the oracle's covenant id, since it cannot be a compile-time constant.

He replied that he could not read the material in full at that moment, and
pointed at the Argent design docs; then, more specifically, at the DEX demo app
in `argent-lang/argent-playground` and at **the `self.quote_id` usage pattern**,
noting that the design principles for this "open ICC" pattern are documented in
the Argent repository.

**This is not a confirmation of our reading of the KIPs.** He said explicitly
that he had not read it in full, and the four questions of issue #46 remain
without a core-developer answer. Issue #46 still contains only this project's own
two comments. What it is, is a targeted pointer at the canonical pattern for
exactly this problem, which is more useful than the confirmation that was asked
for.

---

## 3. The mechanism the pointer leads to

In the DEX demo, `DexPairState` carries `core_id`, `quote_id` and `base_id`, all
dynamic `cov_id` fields — precisely the Q1c constraint. But the child never
writes them itself. The `DexCore` writes them, through:

```
spawns new_pair by pair_id {
    outputs { pair: self.pair_type }
}
...
core_id: self.cov_id,
quote_id: quote_id,
```

`spawns … by …` is not syntactic sugar. Per Argent's
`docs/security-invariants/README.md`, **consensus derives a genesis covenant id
from the outpoint of the authorizing input and the complete output group carrying
that id, ordered by global index.** The generated script reconstructs that
preimage and requires the computed id to equal the one on the first selected
output. Under collision resistance the witness sequence is therefore exactly the
complete group: no output can be omitted, added, reordered or duplicated. A
second invariant forbids one genesis group from satisfying two `spawns` clauses.

Three properties follow:

1. A child covenant **cannot lie about its parent**, because it does not compute
   its own identity — consensus does, from the parent's outpoint.
2. The parent writes the child's state at creation, so fields such as an oracle
   id are not self-asserted.
3. `actor_type<...>` handles additionally bind the **implementation** of an
   observed foreign covenant, not merely its id.

This is the structural replacement for the impossible compile-time constant: the
anchor moves one level up, to a genesis whose lineage is a consensus fact.

---

## 4. Why the question as written is the wrong one

This repository asks: *what guarantees a vault is bound to the correct oracle?*

A vault built from the correct template but carrying a bogus `oracle_covid`
harms only its creator. Each vault is an independent UTXO touching no shared
state, and Argent's security document is explicit that undeclared genesis groups
are permitted — they simply receive no authority.

The question that matters is: **can a forged vault mint real ENRK?** If it can,
everything collapses; if it cannot, it is inert.

That is the closed-ICC `MinterProxy` shape in `examples/icc/`: the asset side
stores the controller's covenant id and requires `controller_id.co_spent()`.

And that is where the hard problem sits. **A `MinterProxy` can store exactly one
covenant id.** With N independent vaults each holding its own, the asset cannot
know them all. A common ancestor is therefore required — and every mint would
have to co-spend it, which reintroduces precisely the global contention the 1→N
oracle construction exists to avoid.

`dex.ag` accepts that cost deliberately, and says so in its own comment: the
`DexCore` is touched only for pair registration and reserve migration, never for
an ordinary swap. Pair registration is rare. **Vault creation and minting are
not.**

---

## 5. What Argent does not yet provide

Both from `docs/followups.md` in `argent-lang/argent`:

- **"KCC20 bootstrap with `spawns`"** — the Minter/KCC20 example implements
  minting but *not* the bootstrap sequence. The document states in as many words
  that it does not show how the controller receives the asset's covenant id. That
  is exactly the step ENRK needs. There is no shipped reference for it.
- **"Launch proofs"** — the proof package (outpoint, computed id, initial states,
  redeem-script preimages) is a follow-up, not existing tooling. Sutton's public
  position that every deployed L1 covenant should ship with a launch proof
  derived from its covenant-id preimage is therefore an intention, not an
  available artifact. Today an auditor assembles that evidence by hand.

---

## 6. Two candidate architectures, neither chosen

**(a) A single factory.** A `VaultFactory` with a known genesis, which `spawns`
each vault and writes `oracle_covid` into it. One clean anchor, one thing to
audit. Cost: every vault opening, and probably every mint, contends on the
factory.

**(b) The oracle spawns the vaults.** The vault's covenant id would then derive
from the outpoint of an oracle-lineage child, making the vault↔oracle binding a
consensus property rather than a state field to be trusted. Since a round already
consumes and emits N UTXOs, vault creation could ride along at no additional
contention.

(b) is more elegant and is an untested hypothesis originating in this analysis,
not a recommendation. It couples two life cycles of very different duration —
an oracle round lasts milliseconds, a vault lasts years.

In both cases **the minting path remains the unsolved part**, and it should be
solved before the vault-creation path.

---

## 7. A related constraint, recorded here so it is not lost

The oracle actor must remain **non-leader**. Argent `e76ee07` formalises
leader/delegate input-group rules; rule 3 requires `|I(c)| = 1` — one input per
covenant id per transaction — for a `consumes`-free ordinary entry **on a leader
actor**. `PriceRound` is not one today, which is why N-input batching is legal.
If it ever acquires a `delegate` entry, the 1→N construction dies.

See [`REMEASUREMENT-2026-09-15.md`](REMEASUREMENT-2026-09-15.md) §6.2.

---

## 8. What to ask, and of whom

The question for Kaspa core developers is now narrower and better formed than the
one on issue #46:

> Given that a covenant id must be a state field or an entry argument, what is
> the intended pattern for binding a large, permissionlessly created population
> of independent covenants to one asset's minting authority, without routing
> every mint through a single contended ancestor?

That is a different question from "is our reading of KIP-10 and KIP-20 correct",
and both remain open.

---

## Sources

- `argent-lang/argent` `docs/security-invariants/README.md`,
  `docs/icc-semantics.md`, `docs/argent-design.md`, `docs/followups.md`,
  `examples/icc/`, `examples/open_icc/`, at `e76ee07`
- `argent-lang/argent-playground` `ag/dex/dex.ag` at `9402c7a`
- `argentc build examples/enrk/probe_const_covid.ag`, September 15, 2026
- Michael Sutton, X thread of September 11, 2026
