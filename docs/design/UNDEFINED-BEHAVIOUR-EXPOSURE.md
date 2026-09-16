# Undefined Behaviour Exposure

**Date:** September 15, 2026
**Scope:** `examples/enrk/a/{oracle,vault}.ag`,
`examples/enrk/b/{oracle,vault}.ag`, `examples/enrk/probe_const_covid.ag`,
audited line by line against Silverscript's `UNDEFINED-BEHAVIOUR.md` at
tag `v1.0.0` (`3ed9733`).

---

## Why this document exists

Silverscript v1.0.0 ships a 361-line specification of **undefined behaviour**,
with C-style semantics. Three properties of it matter to a protocol that can
never be patched:

1. The compiler is **not required to reject** a contract containing undefined
   behaviour.
2. The compiler **may remove, replace or fold** a statement or expression that
   would encounter it.
3. If the contract nevertheless terminates, its result is `true` and **the spend
   succeeds**.

The document states explicitly that a contract must never rely on undefined
behaviour as an implicit check that rejects a transaction.

ENRK's entire thesis is that the code must be right before it ships, because it
can never be corrected afterwards. A language with undefined behaviour makes
arithmetic discipline a specification-level obligation rather than a coding
habit. This document records where we stand today.

---

## 1. What does not apply

Four of the eight categories are absent from our sources entirely: arrays and
fixed-byte values, indexing and slicing, bitwise operations and concatenation,
casts, and loops. There is no `split`, no `slice`, no cast, no loop in any of the
five files. On those axes the code is clean.

Everything below concerns **integer expressions**, plus one open question on
cryptographic expressions and one on generated code.

---

## 2. Two reachable undefined behaviours, in one function

Identical in `a/vault.ag` and `b/vault.ag`, reached by **both** entries
(`liquidate` and `withdraw`):

```
fn icr_percent(int collateral_sompi, int price, int debt_units) -> int {
    return collateral_sompi * price * 100 / PRICE_SCALE / debt_units;
}
```

### 2.1 Division by a zero divisor

`debt_units` is `self.debt`, a state field. **It is checked nowhere.** A vault
with `debt == 0` is not exotic — it is the state of a fully repaid vault, and in
the real protocol it is reachable.

`UNDEFINED-BEHAVIOUR.md` gives this exact case as its canonical example, together
with the `require(b != 0)` that is missing here.

### 2.2 Arithmetic overflow

Multiplication is left-associative, so `(collateral × price) × 100`, and **each
intermediate** must be representable in eight signed-magnitude bytes: a magnitude
of at most 9 223 372 036 854 775 807.

With `price` at `PRICE_SCALE = 1e8`:

| Intermediate | Ceiling on collateral |
|---|---|
| `collateral × price` | 9.22 × 10¹⁰ sompi ≈ **922 KAS** |
| `× 100` | 9.22 × 10⁸ sompi ≈ **9.2 KAS** |

Every vault above roughly ten KAS is in undefined territory. On the stress-test
population — about 102 700 000 KAS over 1 000 vaults — that is 100 % of vaults,
three to four orders of magnitude over the ceiling.

There is no bound anywhere on `self.value`, on `price`, or on `debt`.

### 2.3 The compiler accepts this

Verified in two independent ways on September 15, 2026:

- **By reading the compiler.** In
  `silverscript-lang/src/compiler/compile/expression.rs`, `BinaryOp::Mul` and
  `BinaryOp::Div` lower to a bare `OpMul` and `OpDiv`. No range guard is emitted.
  The only `ArithmeticOverflow` diagnostics in the compiler concern compile-time
  type sizes and array dimensions, never run-time values. The one static check
  v1.0.0 adds is a for-loop iteration budget of 10 000 per function.
- **By running it.** `argentc build` on both vault variants succeeds with no
  error and no warning.

This was the expected answer — the operands are run-time values, so nothing is
decidable at compile time — but it is now established rather than assumed.

### 2.4 What the mainnet engine does today, and why it does not rescue us

In `rusty-kaspa` at the pinned revision `a41a333`,
`crypto/txscript/src/opcodes/mod.rs`:

- `OpMul` uses `checked_mul` and returns `NumberTooBig` on overflow.
- `OpDiv` uses `checked_div` and returns `InvalidState` on a zero divisor.

**The script fails. It does not silently succeed.** The severity therefore
changes category, but not magnitude:

- **Not exploitable.** Nobody obtains a free liquidation or an unbounded
  withdrawal.
- **Inoperable.** Any vault above ~9.2 KAS, and any vault at `debt == 0`, can be
  **neither liquidated nor withdrawn from**. Ever.

That is the freeze found in the crash stress test, reached by a completely
different route — arithmetic rather than auction economics — and hitting 100 % of
vaults rather than 57 % of debt at p95. With no governance, there is nobody to
unfreeze it.

Two reasons not to rest on the engine's behaviour:

1. `UNDEFINED-BEHAVIOUR.md` does not promise it. It promises that the compiler
   may fold the expression. Here there is nothing to fold, which is why the
   engine decides — but the document forbids relying on undefined behaviour as an
   implicit check.
2. Engine behaviour is a consensus detail. `checked_mul` today; something else
   after a hardfork. Our code would be frozen and unpatchable.

### 2.5 The shape of a correction, and its cost

Dividing early keeps every intermediate in range — for instance
`collateral × 100 / PRICE_SCALE × price / debt` — at the price of moving where
precision is lost. For a liquidation threshold, precision loss is a design
decision, not an implementation detail. **It is not decided here.**

---

## 3. One open question that would be severe if answered badly

`UNDEFINED-BEHAVIOUR.md` states that a **malformed** signature or public key is
undefined behaviour, as distinct from a well-formed but incorrect signature,
which simply evaluates to `false`. Its worked example derives the undefined
behaviour from an explicit `sig(...)` cast.

Our three `checkSig` calls take typed `sig` parameters, not casts. Whether the
generated preamble validates the encoding of a spender-supplied `sig` parameter
is **not stated anywhere we could find**.

If it does not, the stake is maximal: the oracle's SWEEP branch is guarded by a
single `checkSig(publisher_sig, publisher)`. Undefined behaviour is not
guaranteed to fail, and a contract that terminates returns `true`. That would be
round republication without the publisher's signature — an oracle whose price
anyone sets.

This is **not asserted**. It is asserted only that nothing in the documentation
excludes it, and that it is testable in minutes: feed a malformed signature to
`sweep` and observe whether the script rejects. It has not been done.

---

## 4. Generated code is in scope and is not ours

Our `.ag` sources are not what executes. Argent emits Silverscript that indexes
inputs and outputs, reads state through templates and computes offsets, and
**every undefined-behaviour rule applies to that code exactly as it applies to
ours**. `UNDEFINED-BEHAVIOUR.md` devotes an entire section to transaction and
state expressions: valid indices, non-negative template lengths, offsets that do
not overflow.

One instance is concrete. `argentc inspect` reports, on both vault entries of
both variants:

```
generated arguments: gen__oracle_feed__price_round_prefix_len: int
                     gen__oracle_feed__price_round_suffix_len: int
```

These template lengths are supplied by the spender and feed
`readInputStateWithTemplate`, whose contract is that supplied lengths must match
the layout of the selected input. The authenticity of the price inside the vault
therefore depends on two integers provided by whoever spends.

This is a question for audit, not an established defect. It is also the clearest
available evidence that an ENRK audit must cover **two layers**: our source, and
Argent's lowering. Argent says of itself that it will require its own audit and
hardening after Silverscript's.

---

## 5. Minor findings

**`round + 1`**, in both `sweep` entries. Unbounded addition on a state field,
therefore undefined behaviour in principle if `round` approaches 2⁶³. At one
round per 100 ms that is on the order of 10¹⁰ years. Worth listing in an audit,
not worth correcting.

**Integer state-field width.** Writing an integer into a state field is
undefined behaviour if it does not fit the declared width. `round + 1` and
`next_price` are written into `PriceRoundState`. The width Argent allocates to an
`int` state field has not been verified.

**Variant B: the genesis price is unconstrained.** `sweep` requires
`next_price > 0`, but no entry validates the initial state, and `use` checks
nothing. A round-1 price of zero yields an ICR of zero and makes every
liquidation valid. This is a logic hole rather than undefined behaviour, and it
exists only in variant B.

**Variant B's `sweep` is the one correct piece.** `require(left_value > 0)`
followed by `require(left_value < self.value)` bounds the subtraction on both
sides. It is the only place in the corpus where arithmetic discipline is actually
applied — which shows the reflex existed in places and not in others, the usual
pattern.

**Variant A's `use` still lacks condition (a).** The clause tying the spender to
a real vault is documented as absent in the file's own comment. Not undefined
behaviour, but still open, and worth re-reading in the light of the open-ICC
patterns.

---

## 6. What this implies for the project

Two certain and reachable undefined behaviours, in the same function, identical
across both variants and both entries. One possible and potentially fatal one,
testable. Two minor ones. One entire category outside our control.

The rate matters more than the list. These defects are in the only Argent code
this project has written — a measurement stub of a hundred or so lines, written
carefully. For immutable code, arithmetic discipline must become **a written rule
of the project and a line of the audit scope**, not a reflex that is present
sometimes:

- every divisor proved non-zero before the division
- every operand bounded before every multiplication, addition and subtraction
- the accepted input range of every entry stated explicitly
- no reliance on engine-level checked arithmetic as an implicit guard

None of this is currently recorded anywhere in the specification.

---

## Sources

- `kaspanet/silverscript` `UNDEFINED-BEHAVIOUR.md` at tag `v1.0.0` (`3ed9733`)
- `silverscript-lang/src/compiler/compile/expression.rs`,
  `silverscript-lang/src/compiler/static_check.rs`, same revision
- `kaspanet/rusty-kaspa` `crypto/txscript/src/opcodes/mod.rs` at `a41a333`
- `argentc inspect` output, September 15, 2026 — see
  [`REMEASUREMENT-2026-09-15.md`](REMEASUREMENT-2026-09-15.md) §8
