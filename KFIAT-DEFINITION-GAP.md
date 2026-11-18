# kFIAT — The Undefined Parameter, and What the Code Assumes Instead

**Date:** September 16, 2026
**Status:** Findings. **No decision taken.** The denomination of kFIAT is open and
is the gating question.
**Scope:** Read-only audit of every kFIAT touch point in the repository at
`33c4248`. No file was modified.

> **Why this document exists.** The junior tranche is named in every entry
> document, has 145 references in `kaspa_tokens.rs`, and carries a frozen 30% cap
> — but the quantity that prices it, `kfiat_price`, is declared in eight function
> signatures and produced by nothing. This document records what is actually
> defined, what is assumed silently and inconsistently, and what must be decided
> before any implementation.

**Update 2026-11-17.** The audit of 2026-11-09 confirms sections 4, 6.1 and 6.2 (audit B3, I8, I9). The economics verification (2026-11-11) found that the two denomination forms are identical on every aggregate, so the difference is global state on UTXO and where the excess goes (ECON P3: needs a decision), and that the published stress figures inherit a hidden index cushion (`docs/design/ECONOMICS-VERIFICATION-2026-11-11.md` §1.1). The denomination remains undecided. The code has not changed since `33c4248`.

---

## 1. The chronology, established from git

The premise that specification preceded code does not hold for this module.

| Date | Commit | Content |
|---|---|---|
| Sept 3 | `9a4d909`, `6931302`, `4b39b92` | All Rust — `types.rs`, `kaspa_tokens.rs`, 119 tests |
| Sept 5 | `50799b3` | `FROZEN_PARAMETERS.md`, `PHASE_4_ARCHITECTURE_PROPOSAL.md` |

The code precedes the frozen specification by two days. `FROZEN_PARAMETERS.md`
says so in its own introduction: it exists because values and justifications had
scattered across a dozen analyses.

`types.rs` has **one commit in its entire history**, `4b39b92` of September 3, and
has not been touched since. That is the mechanical explanation for three stale
values it still carries — see §7.

---

## 2. What kFIAT has, and it is substantial

**A ledger.** `kaspa_tokens.rs` (827 lines) holds two separate `TokenLedger`
instances under one `TokenLayer`. Integer-only BigInt arithmetic, no `f64`
anywhere in the module. Zero balances are pruned. Every mutation is
checked-then-applied, so a rejected operation leaves the ledger byte-for-byte
unchanged.

**A supply-level cap**, not a per-vault one, in exact integer arithmetic:

```
100 * (K + A) <= cap * (E + K + A)
```

`max_mintable_kfiat()` solves the inequality for `A`. `would_exceed_kfiat_cap()`
tests it without mutating. `verify_invariants()` **reports** a breach as
`StateInconsistency` rather than concealing it. The module documents the
denominator-shrinking path explicitly (E=700/K=300, burn 600 ENRK, ratio reaches
75%) and records the rejected alternatives.

**A seniority ordering**, identical in `PHASE_4` §5.5 and
`stress_test_crash.py` l.423-440: fee, then ENRK at par, then kFIAT on the
remainder, then write-off junior first.

**A master invariant**, `PHASE_4` §2:
`kfiat_supply == Σ vault.debt_kfiat + kfiat_uncovered`, with the note that
`kfiat_uncovered` becoming non-zero is the junior tranche doing its job.

**No redemption** — `CannotRedeemKFIAT`. Mint blocked under the circuit breaker,
burn always allowed.

---

## 3. What kFIAT does not have: a denomination

`kfiat_price: f64` is declared in eight signatures:

| File | Line | Function |
|---|---|---|
| `types.rs` | 216 | `calculate_icr` |
| `types.rs` | 229 | `is_under_collateralized` |
| `vault.rs` | 176 | `mint_kfiat` |
| `vault.rs` | 292 | `burn_kfiat` |
| `vault.rs` | 364 | `withdraw_collateral` |
| `vault.rs` | 413 | `close_vault` — already `_kfiat_price`, unused |
| `vault.rs` | 439 | `get_liquidation_candidates` |
| `liquidation.rs` | 58 | `start_liquidation` |

**One line consumes it** — `types.rs:220`:

```rust
let debt_value = self.debt_enrk.to_f64().unwrap_or(0.0) * enrk_price
    + self.debt_kfiat.to_f64().unwrap_or(0.0) * kfiat_price;
```

The other seven declarations only transport the value to that line.

**Nothing produces it.** `oracle_feeds.rs` (557 lines) produces four indices and
the peg. No function in any module returns a kFIAT price. In the documentation,
`grep -rn "kfiat.*price" docs/` matches only the November audit and the study
reports, which describe the gap and do not define the price.

**Nothing tests it.** The 119 tests never call `VaultManager::mint_kfiat`,
`burn_kfiat`, `withdraw_collateral`, `close_vault` or
`get_liquidation_candidates`. The kFIAT tests in `kaspa_tokens.rs`
(l.619-823) exercise `TokenLayer`, which handles no price at all. The only
call sites passing a value are `liquidation.rs` 359, 380, 431 and
`types.rs:361`, all at `1.0`.

The value has no source, no specification, no definition and no coverage. It
exists only as a parameter.

---

## 4. Two ICRs for the same vault

`vault.rs:142` (`mint_enrk`) and `vault.rs:266` (`burn_enrk`) pass the **literal
`1.0`**, while `mint_kfiat`, `burn_kfiat`, `withdraw_collateral` and
`get_liquidation_candidates` pass a caller-supplied value.

On a vault carrying junior debt, the ICR computed by `mint_enrk` and the ICR
computed by `mint_kfiat` differ for any caller value other than 1.0. Two truths
for the same quantity, in the same file.

---

## 5. Three artefacts, three answers

| Artefact | What it assumes |
|---|---|
| `stress_test_crash.py` l.120-125, l.156-157 | Fixed face in peg units — **at par** |
| `types.rs` `calculate_icr` | A separate caller-supplied price — **marked to market** |
| `kaspa_tokens.rs` l.70 and header | *"unpegged"*, "let the market price the discount" — **marked to market** |

The stress test is decisive because the published figures rest on it:

```python
def icr(self, kas_price: float, peg: float) -> float:
    debt_value = self.total_debt_units() * peg
```

Total debt — ENRK and kFIAT combined — multiplied by a single `peg`. There is no
`kfiat_price` anywhere in `tests/backtesting/`. Vault construction (l.156-157)
splits one `total_debt_units` into two fractions of the same unit.

**Every published kFIAT figure assumes par**: ENRK p95 5.0% with redemption (the
quoted "kFIAT 2%" is not reproduced: audit I1 gives mean about 10%, p95 about 39% at
-85%, floor 75%, redemption on; "kFIAT 14% without" was not re-checked), the latent hole 46% → 0%, the rejection of
Recovery Mode, the rejection of a 250% ICR.

---

## 6. Two further gaps, independent of the decision

### 6.1 The seniority waterfall is not implemented

`submit_bid` (`liquidation.rs` 171-240) checks expiry, computes the current
price, verifies the bid covers the debt, computes collateral and fee, removes
the auction and returns `(collateral_kas, fee)`.

No ENRK burn, no kFIAT burn, no shortfall recorded, no `enrk_uncovered` /
`kfiat_uncovered`, no vault closure, no surplus to the owner. `PHASE_4` §5.5 is
a proposal, per its title. The waterfall exists in Python in the stress test and
as pseudocode in that proposal — nowhere else.

`submit_bid` also takes **no token type** and no bidder identity. The bid is a
bare `BigInt`, and l.128 documents it as *"amount of ENRK/kFIAT offered"*, so
settlement treats the two tranches as interchangeable at par as a means of
payment. `auction.debt_to_cover` (l.91) sums them directly.

### 6.2 A dimensional inconsistency in settlement

```rust
// l.207 — [stablecoin] / [$/KAS] -> a KAS quantity
let required_bid = debt_f64 / (kas_price * price_multiplier);
if bid_f64 < required_bid { ... }

// l.152 — bid treated as a value
let kas_amount = (bid_f64 * price_discount) / kas_price;
```

`bid_amount` is compared against a KAS quantity in the first and divided by
`kas_price` as a stablecoin value in the second. It cannot be both. This is a
defect of the settlement path, not of kFIAT, and it is recorded nowhere.

---

## 7. Stale values in `types.rs`

Untouched since September 3, therefore predating the frozen specification:

| Field | Value in code | Frozen value |
|---|---|---|
| `LiquidationParams::end_price` | 85 | **75** |
| `FeeStructure::stability_pool_allocation` / `treasury_allocation` | 80 / 20 | Fees taken in KAS; treasury 20% until cap, then 0% |
| `OraclePrice::source` | `"band"`, `"chainlink"` | Covenant-lineage oracle |
| `lib.rs:68` `LIQUIDATION_END_PRICE` | 85 | **75** |

These are the same assertions for which seven documents were deleted in the
September 5 hygiene pass. The pass did not cover the code. Whether to correct
these values is an open owner decision.

---

## 8. The decision, and what each branch costs

**The question:** is kFIAT debt at fixed face in peg units, non-redeemable — or a
residual claim marked to market?

**Branch 1 — fixed face.** Removes eight parameter declarations and the
`* kfiat_price` term; `types.rs:220` becomes a single multiplication of total
debt by the peg. Nine call sites adjusted, one test constant. No test to rewrite,
since none exercises the surface. `PHASE_4` §5.5 holds as written. The choice
does not change the published figures, which still carry the index cushion found
in the economics verification (§1.1). `kaspa_tokens.rs` must be corrected, since it asserts the
opposite.

**Branch 2 — residual claim.** Requires creating the producer that does not
exist, which on L1 means a second oracle flow with its own covenant construction
while Q1c is unresolved for the first. Requires correcting the reflexive
inversion: `kfiat_price` sits in the denominator of `calculate_icr`, so a
collapsing kFIAT **raises** a vault's ICR and delays its liquidation precisely
when it should accelerate. Requires rewriting the cap formula, which would sum
heterogeneous units. Requires re-running the stress test, invalidating every
published figure.

**A conceptual objection to branch 2, recorded rather than decided.** If kFIAT is
already marked to market, the loss is already in the price; writing off a
shortfall on top counts it twice. "kFIAT absorbs losses first" has content only
against a fixed face that goes unhonoured. Branch 2 empties the waterfall of its
function.

The costs are not symmetric: branch 1 deletes code, branch 2 adds code and
invalidates measurements. **This is not a reason to decide it here.**

Note (2026-11-17): the economics verification found the two forms identical on
aggregates (ECON P3), and the audit lists a third form, fixed face plus an
on-chain write-down index (audit, option A2). None is decided.

---

## 9. Open items this document adds

1. **kFIAT denomination** — fixed face in peg units, or residual claim at market.
   Gates §3, §4, §5 and the form of the cap. **Undecided.**
2. **The seniority waterfall is unimplemented** — `submit_bid` settles nothing.
   Joins redemption on the list of specified-but-unbuilt mechanisms.
3. **The dimensional inconsistency in `submit_bid`** — independent of (1).
4. **`types.rs` carries three superseded values** — the September 5 hygiene pass
   covered documents only.

---

## 10. Operational note for the next session

Copies of documents attached to other tools can be older than the repository. A
session that works from such copies works from a superseded state. This is hygiene
rule 3 of `PROJECT-STATE.md` in its exact form: before asserting the state of a
file, read the file.

---

## Sources

All line numbers refer to `cyprox/ENRK_stablecoin` at `33c4248`, branch `master`.

- `contracts/igra/src/types.rs`, `vault.rs`, `liquidation.rs`,
  `kaspa_tokens.rs`, `oracle_feeds.rs`, `errors.rs`, `lib.rs`
- `tests/backtesting/stress_test_crash.py`
- `docs/design/PHASE_4_ARCHITECTURE_PROPOSAL.md` §2, §5.5
- `docs/design/FROZEN_PARAMETERS.md` §3, §10
- `docs/design/REDEMPTION-ANALYSIS.md`
- `git log` for the chronology in §1
