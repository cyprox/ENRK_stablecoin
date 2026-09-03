# Phase 4 Architecture Proposal — Vault ↔ Token ↔ Kaspa Binding

**Status:** PROPOSAL — awaiting approval, no code written  
**Date:** September 3, 2026  
**Prerequisite:** Phases 1–3 complete (119 tests passing)

---

## 1. The core problem: double bookkeeping

After Phase 3 the protocol holds **two independent records of the same debt**:

| Record | Owner | Granularity |
|--------|-------|-------------|
| `vault.debt_enrk` / `vault.debt_kfiat` | `VaultManager` | per vault |
| ENRK / kFIAT supply | `TokenLayer` | per address |

Nothing currently forces them to agree. If they drift, the protocol is insolvent
and **no participant can detect it** — the vault layer would report healthy
collateral ratios while more tokens circulate than are backed. This is the exact
failure class that destroyed several fiat-free stablecoins: the accounting was
internally consistent inside each module and wrong across them.

Phase 4 is therefore not "plumbing". Its central job is to define, and mechanically
enforce, the relationship between these two records.

---

## 2. The master invariant

Proposed, and asserted after **every** state-changing operation:

```
enrk_supply  == Σ vault.debt_enrk  + enrk_uncovered
kfiat_supply == Σ vault.debt_kfiat + kfiat_uncovered
```

`*_uncovered` are explicit, publicly readable counters of **written-off debt**:
tokens still circulating that no vault owes any more. See §7 — they are not an
accounting convenience, they are the protocol's honesty mechanism.

In healthy operation `enrk_uncovered` must remain **zero**. A non-zero value is a
senior-tranche solvency event and should be treated as such by any integrator.

`kfiat_uncovered` is expected to become non-zero over time. That is the junior
tranche doing its job.

---

## 3. Proposed module layout

One new module, `protocol.rs`, plus one trait seam.

```
protocol.rs
├── trait KaspaExecutor          // seam: real RPC vs. mock
├── struct MockExecutor          // deterministic, for tests
├── struct EnrkProtocol          // single entry point, owns every manager
├── struct Preflight             // validate-everything-before-mutating
├── struct OperationReceipt      // uniform return value
└── struct ProtocolInvariants    // the §2 assertions
```

**Naming note:** the roadmap called this `vault_transaction_bridge.rs`. I propose
`protocol.rs` instead: this is not a bridge between two peers, it is the top-level
facade that owns all seven existing managers and is the only place where
cross-module invariants can be checked. Your call.

### 3.1 `EnrkProtocol`

```rust
pub struct EnrkProtocol<E: KaspaExecutor> {
    vaults:          VaultManager,
    tokens:          TokenLayer,
    liquidations:    LiquidationManager,
    stability_pool:  StabilityPoolManager,
    circuit_breaker: CircuitBreaker,
    oracle:          OracleFeedManager,
    peg:             PegCalculator,
    executor:        E,
    enrk_uncovered:  BigInt,
    kfiat_uncovered: BigInt,
}
```

Every public method is a complete protocol operation. No caller ever touches a
sub-manager directly — that is what makes the invariant enforceable.

### 3.2 `KaspaExecutor` — the honesty seam

`KaspaTransactionBuilder` currently returns fabricated strings like
`"tx_deposit_kaspa:al_kaspa:va"`. Phase 4 must not build logic on top of that
pretending it settles anything.

```rust
pub trait KaspaExecutor {
    fn submit_kas_transfer(&mut self, from: &str, to: &str, sompi: &BigInt)
        -> IgraResult<String>;
    fn confirm(&self, tx_id: &str) -> IgraResult<bool>;
}
```

- `MockExecutor` — deterministic ids, programmable failures, used by all tests.
- `KaspaRpcExecutor` — Phase 5, real node. Drops in without touching Phase 4 logic.

This also lets us test the failure path that matters most: **what happens when the
chain transfer fails after the ledgers were updated.** See §5.

---

## 4. Validate-all-then-apply

Rust gives us no transaction manager, and these are in-memory structures, so
partial mutation is a real risk. Example of the naive ordering going wrong:

1. `vaults.mint_enrk()` → debt increased ✔
2. `tokens.mint_enrk()` → **fails** (invalid address) ✘
3. Result: the vault owes debt for tokens that were never issued.

Proposed discipline, applied to every operation:

```
Preflight  — every check, zero mutation. Returns a validated plan.
Apply      — execute the plan. Must be infallible by construction.
Assert     — §2 invariants. A failure here is a bug, and should panic in
             debug builds rather than continue on corrupt state.
```

`Preflight` returns a concrete plan struct (amounts, splits, addresses) so `Apply`
has no decisions left to make and therefore no way to fail.

---

## 5. Operation flows

### 5.1 `mint_enrk(vault_id, amount, caller)`

```
PREFLIGHT
  1. circuit_breaker.require_active()
  2. indices = oracle.fetch_all_indices(now)        // must be fresh
  3. peg = peg_calculator.calculate(indices)
  4. circuit_breaker.check_peg_deviation(peg)
  5. vault exists && caller == vault.owner
  6. KaspaAddressValidator::is_valid_address(caller)
  7. fee        = amount * MINT_FEE_BPS / 10_000
  8. pool_share = fee * STABILITY_POOL_ALLOCATION / 100
  9. treasury   = fee - pool_share                  // remainder, see below
 10. prospective_icr with debt += amount + fee
 11. require prospective_icr >= ICR_MINIMUM (200%)

APPLY
 12. vault.debt_enrk += amount + fee
 13. tokens.mint_enrk(caller,        amount)
 14. tokens.mint_enrk(POOL_ADDR,     pool_share)
 15. tokens.mint_enrk(TREASURY_ADDR, treasury)
 16. stability_pool.deposit_fees(pool_share)

ASSERT §2
```

**Why step 9 uses subtraction, not a second percentage.** With `fee = 3`:
`3*80/100 = 2` and `3*20/100 = 0` — the two shares sum to 2, not 3, and the
invariant breaks by 1 unit on every such mint. Taking the treasury share as the
*remainder* makes the split exact by construction at any fee size.

### 5.2 Fees are **minted**, not deducted

Consequence of §2 that needs your explicit sign-off: the user receives `amount`
but owes `amount + fee`, so `fee` tokens must be issued to somebody or supply
falls short of debt.

So the fee is newly minted ENRK credited to the Stability Pool and treasury. This
is also what `stability_pool.rs` already assumes — it holds an `enrk_balance` it
spends on buybacks (equilibrium mechanism #3), and that balance has to be real
tokens, not a number.

The alternative — deducting the fee from what the user receives — would mean the
pool accrues nothing and mechanism #3 has no ammunition.

### 5.3 `burn_enrk` / repayment

Mirror of 5.1: burn from caller, reduce `vault.debt_enrk`, no fee. Permitted even
when the circuit breaker is tripped — see §6.

### 5.4 Collateral deposit / withdraw

Deposit: `executor.submit_kas_transfer(owner → vault_escrow)`, then
`vault.collateral_kas += amount`. Withdraw: preflight the resulting ICR against
MCR first, then transfer out.

**Chain-failure ordering.** For deposits, submit the transfer *first* and credit
collateral only on success — crediting first would let a failed transfer create
collateral from nothing. For withdrawals, debit collateral first and transfer
second; if the transfer fails, re-credit and return the error. Withdrawal is the
one place a rollback is genuinely needed, and it is safe because it restores a
strictly healthier state.

### 5.5 `liquidate(auction_id, bid, bidder)` — the seniority waterfall

This is the operation that gives the dual-tranche design its meaning.

```
net = bid - (bid * LIQUIDATION_FEE_BPS / 10_000)

1. SENIOR FIRST — repay ENRK debt
     enrk_repaid = min(net, vault.debt_enrk)
     burn enrk_repaid; vault.debt_enrk -= enrk_repaid
     net -= enrk_repaid

2. JUNIOR SECOND — repay kFIAT with whatever remains
     kfiat_repaid = min(net, vault.debt_kfiat)
     burn kfiat_repaid; vault.debt_kfiat -= kfiat_repaid
     net -= kfiat_repaid

3. SHORTFALL — whatever debt is still outstanding is written off,
   junior first, and recorded:
     kfiat_uncovered += vault.debt_kfiat;  vault.debt_kfiat = 0
     enrk_uncovered  += vault.debt_enrk;   vault.debt_enrk  = 0

4. SURPLUS — any remaining net returns to the vault owner
5. Transfer collateral KAS to bidder; close vault
```

Step 1 before step 2 *is* "kFIAT absorbs losses first": paying the senior claim
first is what leaves the junior claim unpaid when proceeds are short.

### 5.6 `redeem_enrk(amount, caller)`

Burn ENRK, release KAS at peg value, minus `REDEMPTION_FEE_BPS`. This is
equilibrium mechanism #1 and the strongest peg defense, which is precisely why §6
keeps it available under most conditions.

---

## 6. Circuit breaker gating

Not every operation should stop when the breaker trips. Blocking repayment would
trap users in debt they are willing to clear while liquidation risk keeps accruing
against them — punishing the people helping the protocol.

| Operation | Paused? | Reasoning |
|-----------|---------|-----------|
| `mint_enrk` / `mint_kfiat` | **blocked** | no new debt against an unreliable peg |
| `burn_enrk` / `burn_kfiat` | **allowed** | repayment always improves solvency |
| `deposit_collateral` | **allowed** | strictly improves vault health |
| `withdraw_collateral` | **blocked** | cannot price safety without a good peg |
| `liquidate` | **blocked** | liquidating at a bad peg expropriates the owner |
| `redeem_enrk` | **blocked** | redemption at a broken peg drains reserves |
| read-only queries | **allowed** | transparency must never pause |

Requires your approval — this table is a policy choice, and once deployed it is
frozen like every other parameter.

---

## 7. Open decision: the treasury address

Your founding constraint is *"à partir du moment où il y a une DAO, l'action
humaine est possible et donc l'objectif principal est biaisé."*

`TREASURY_ALLOCATION = 20` sends a fifth of all protocol fees to a treasury
address. That address is the **only** place in the entire design where value
accrues to something a human controls. No DAO, no admin key — but a wallet that
collects 20% of revenue is human action with extra steps, and it is the first
thing a critic will point at.

Three options:

| Option | Effect | Cost |
|--------|--------|------|
| **Burn the 20%** | Fee is minted then immediately burned. Deflationary, value accrues to every holder pro-rata. No controllable address exists anywhere. | No funding for audits, oracle costs, development. |
| **100% to Stability Pool** | Redirect the full fee to peg defense. Mechanism #3 gets 25% more ammunition. Still no controllable address. | Same funding gap. |
| **Keep 20% treasury** | Funds ongoing work. | Contradicts the immutability thesis; a permanent centralization vector. |

I have no strong view on which you should pick — it is a genuine trade-off between
ideological consistency and the practical need to pay for audits. But it should be
a deliberate choice made now, because it is frozen at deployment and cannot be
changed without a fork.

---

## 8. Test plan

| Area | Tests | What is actually being proven |
|------|-------|------------------------------|
| Invariant enforcement | 6 | supply == debt + uncovered after every operation type |
| Preflight rejection | 8 | a rejected operation leaves state byte-identical |
| Fee minting & split | 5 | exact split at fee = 1, 2, 3, 7, and large values |
| Liquidation waterfall | 7 | senior-first ordering; partial, exact, and surplus cases |
| Shortfall accounting | 4 | `kfiat_uncovered` rises before `enrk_uncovered` ever does |
| Circuit breaker gating | 7 | one per row of the §6 table |
| Chain-failure rollback | 4 | executor failure never leaves partial state |
| End-to-end lifecycle | 4 | create → deposit → mint → repay → close, invariants intact throughout |
| **Total** | **45** | → **164 tests** overall |

The chain-failure and preflight-rejection groups matter most. Anyone can test the
happy path; these protocols die on the rejected-halfway-through path.

---

## 9. What I need from you before writing code

1. **Module name** — `protocol.rs` (proposed) or `vault_transaction_bridge.rs`?
2. **Fees minted, not deducted** (§5.2) — confirm.
3. **Circuit breaker gating table** (§6) — approve as written, or amend rows.
4. **Treasury** (§7) — burn 20%, 100% to pool, or keep the treasury?
5. **`enrk_uncovered` / `kfiat_uncovered` as public counters** (§2, §7) — confirm
   you want write-offs published rather than absorbed silently.

Nothing gets implemented until these five are settled.
