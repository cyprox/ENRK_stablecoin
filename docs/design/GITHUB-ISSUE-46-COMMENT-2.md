# Draft comment for kaspanet/kips#46 — re-measurement

**Status:** Draft. Not posted. Review before publishing.

---

## Re-measured on Argent `e76ee07` + Silverscript v1.0.0

Following the release of Silverscript v1.0.0 on September 9, I re-ran the
measurement posted here on September 6. Reporting it because two things changed
and one of them is a defect on my side.

**Toolchain.** Argent `d08e52d` → `e76ee07`; Silverscript `c7d17a1` → `3ed9733`
(v1.0.0). `rusty-kaspa` unchanged at `a41a333`, so consensus parameters and
`MassCalculator` are identical across both runs.

**Every figure reproduces to the unit.** The scaling ladder is exactly linear over
ten points:

| | fixed | per input (compute) | per input (transient) | script | sigscript |
|---|---|---|---|---|---|
| Variant A | 94 / 376 | 759 | 1 556 | 241 B | 248 B |
| Variant B | 94 / 376 | 839 | 1 876 | 320 B | 328 B |

Applying those to the seven rows I posted reproduces each one exactly (A at
N = 560/600/640/645, B at N = 520/530/540). Q1a, Q1b, Q2 and Q3 stand on a
toolchain two revisions and one language release later.

**Correction 1 — the ceilings are 642 and 532, not 640 and 530.** The published
numbers were rungs of my test ladder. Removing the fixed transaction cost and
dividing by the marginal cost per input gives the true maxima. Compute mass would
have allowed 658 and 595, so the finding is unchanged: transient mass binds.

**Correction 2 — my published reproduction steps do not reproduce.** The
committed `tests/enrk_mass.rs` binds every output to authorizing input 0, while
the generated `use` entry requires each input to authorize exactly one output.
It fails at N = 2. That check is present in the `.sil` fixtures at `d08e52d`
too, so the committed harness never produced the published ladder — the working
copy that did was not the one I committed. The fix is one line (bind output `i`
to authorizing input `i`); with it applied both variants validate the full ladder
to N = 512. Apologies to anyone who tried to run it.

**Correction 3 — a transcription error.** My summary table gave variant B's
signature script as 262 B. It is 328 B; a witness cannot be smaller than the
320 B redeem script it carries, and the same post publishes 320 B two tables
later. The mass tables were always right.

---

## Q1c: the compiler now states the constraint itself

`probe_const_covid.ag` is still rejected under v1.0.0, with a more precise
message than before:

```
argentc: entry `Probe::touch` observe `oracle` covenant id source must be
a `self.<field>` state field or entry argument of type `cov_id`
```

Thanks to @michaelsuttonil for pointing at the open-ICC `spawns` pattern and the
`self.quote_id` usage in the DEX demo. That is the lineage primitive I was
missing: consensus derives a child's covenant id from the authorizing input's
outpoint and the complete ordered output group, so a child cannot misreport its
parent, and the parent writes the child's initial state.

Working through it moved the question rather than closing it. A forged vault is
inert unless it can mint the real asset, so the binding that matters is
**asset → vault**, not vault → oracle. A `MinterProxy` stores exactly one
covenant id, so a permissionlessly created population of independent vaults needs
a common ancestor — and every mint would have to co-spend it, reintroducing
exactly the contention the 1→N oracle construction exists to avoid. The DEX
accepts that cost because pair registration is rare; vault minting is not.

Argent's own `docs/followups.md` records the KCC20 bootstrap with `spawns` and
launch proofs as unimplemented, so there is no shipped reference for this step.

**The question, restated:** given that a covenant id must be a state field or an
entry argument, what is the intended pattern for binding a large, permissionlessly
created population of independent covenants to one asset's minting authority,
without routing every mint through a single contended ancestor?

---

## Two things I got wrong in the original post, found by reading the generated code

**The round transition is not atomic.** `sweep` emits two outputs, not N — the
generated Silverscript requires `OpAuthOutputCount(activeInputIndex) == 2`.
Reaching N children from one parent takes ⌈log₂ N⌉ successive sweeps, therefore
several transactions. The stale-price-free property I claimed does not follow
from a binary split. Batching N independent sweeps into one transaction is the
obvious candidate and has the same shape as the USE ladder that does validate,
but I have not measured it and the contract does not express it.

So N = 642 is the ceiling on **consumption** — N independent USE spends batched
into one transaction — not on republication. Republication will be lower:
`sweep` carries a `checkSig` and two `validateOutputState`, and a larger witness.

**A constraint I had not noticed.** Rule 3 of Argent's leader/delegate input-group
rules requires `|I(c)| = 1` for a `consumes`-free ordinary entry on a leader
actor. `PriceRound` is not a leader actor, so N-input batching remains legal —
but if the oracle ever gains a `delegate` entry, the whole construction dies. Is
that reading right?

---

## Still open

Q4 (block inclusion under contention) still needs Testnet-10. A full round
consumes 99.93 % of one block's transient mass, so the cadence model remains one
block per round: ~100 ms at 10 BPS.

And the original ask is unchanged: is the construction what KIP-10 and KIP-20
intend, or a behaviour that happens to work and is not guaranteed? A local engine
executing my scripts is evidence, not authority.

Full record, corrections and reproduction steps:
`docs/design/REMEASUREMENT-2026-09-15.md` in the repository.
