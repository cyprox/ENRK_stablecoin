# ENRK — Frozen Parameter Specification

**Date:** September 3, 2026
**Author:** cyprox

**Revision note, 2026-11-17 (dated record; values below are as frozen on 2026-09-03).** Since then: (1) execution layer decided by the owner on 2026-11-13: Kaspa L1, Igra not retained (sections 7 and 10 updated below); (2) owner decisions: a recurring stability fee, fees are never burned, ENRK has its own price oracle (rate, base and recipients not decided); (3) the stress figures quoted in sections 1 and 4 come from a simulator whose index falls with KAS (hidden cushion), see ECONOMICS-VERIFICATION-2026-11-11 sections 1 and 2; (4) open owner decisions are listed in ECONOMICS-VERIFICATION section 9.

Every parameter here is frozen at compile time and cannot be changed after
deployment. There is no governance. Changing any of them requires a fork.

This document exists because the values and their justifications had scattered
across a dozen analyses. An implementer or an auditor needs them in one place,
each with the evidence behind it.

**Legend:** ✅ decided · 🔬 recommended by evidence, awaiting confirmation ·
❓ open, blocked on the execution-layer choice

---

## 1. Peg formula

| Parameter | Value | Status |
|---|---|---|
| Hashrate weight | 40% | ✅ |
| Global energy price weight | 30% | ✅ |
| Kaspa fees weight | 20% | ✅ |
| Crypto adoption weight | 10% | ✅ |
| Peg clipping range | [0.1, 5.0] | ✅ |

Chosen as "Alternative 3.5" after backtesting. In the definitive 4,380-day simulation Alt 3.5 has volatility 25.0% and max drawdown −17.3%, while pure-Kaspa Alt 3 does not produce a finite figure (NaN); the earlier intermediate estimates were −35% against −78% (2018 bear).

**Documented cost, to be stated in any public specification:** a peg that holds
firm while collateral collapses maximises the fall in ICR. Alt 3 (pure Kaspa
indexing) leaves a 10% latent hole at −85% where Alt 3.5 leaves 17% — the hedge
costs roughly 7 points of solvency. This is the MakerDAO Black Thursday dynamic.
Not a reason to change the formula; a reason not to claim the hedge is free.

Note (2026-11-17): the 'peg holds firm' reading and the 7-point figure come from the original simulator, in which the index falls with KAS (to about 0.54 at -85%). With a flat index the same architecture loses far more (ECONOMICS-VERIFICATION section 1). The check mark records the 2026-09-03 decision; the fate of the index (fixed unit, slow-up/immediate-down bound, baseline, energy source) is open (ECONOMICS-VERIFICATION section 9, item 1).

---

## 2. Collateral ratios

| Parameter | Value | Status |
|---|---|---|
| ICR minimum (at mint) | **200%** | ✅ keep |
| MCR (liquidation trigger) | **150%** | ✅ keep |

**Why 250% was rejected.** Once the auction floor is corrected, 200% → 250% moves
ENRK p95 loss from 11.2% to 11.6% — very slightly *worse* — while costing users 25%
capital efficiency. A higher ICR makes vaults survive longer and therefore
liquidate **later, at worse prices**. Liquidating early beats holding more
collateral.

**Why raising the MCR was rejected.** MCR 200% moves the p95 latent hole from 46%
to 44% while costing +5.2% in calm markets. Wrong lever.

---

## 3. Debt tranching

| Parameter | Value | Status |
|---|---|---|
| kFIAT cap | 30% of total debt **at mint** | ✅ |
| Redeemable tranche | ENRK only | ✅ |

**The cap is a mint-time ceiling, not a permanent guarantee.** It is a ratio, so it
can be breached without minting any kFIAT — by shrinking the denominator. Burning
ENRK does exactly that, and ENRK burns are core paths: repayment, redemption, and
Stability Pool buyback. Peg defence and the cap pull against each other, and peg
defence must win.

Behaviour when breached: `mint_kfiat` refuses, `max_mintable_kfiat()` returns zero,
and `verify_invariants()` **reports** the breach rather than hiding it.

Public documentation must say "≤ 30% at mint", never "always ≤ 30%".

**Seniority, to be stated explicitly.** Only ENRK is redeemable. In a crisis ENRK
holders can exit at par while kFIAT holders cannot. Modelling shows kFIAT benefits
indirectly (redemption prevents vaults from reaching shortfall), but in a deeper
scenario ENRK drains the collateral and kFIAT faces the remainder. That is
seniority working as designed, and it must be documented as a deliberate property
rather than discovered by a holder.

---

## 4. Liquidation

| Parameter | Value | Status |
|---|---|---|
| Auction duration | 120 minutes | ✅ |
| Auction start price | 100% of market | ✅ |
| **Auction floor** | **75%** (was 85%) | ✅ **changed** |
| Liquidation fee | 4% | ✅ |

**The single most consequential parameter revision.**

Liquidator demand modelled as `4% + 18% × drawdown`. At a 95% drawdown they require
21%. An 85% floor offers 15%, so **nothing clears** past a 61% drawdown — this is
the freeze. A 75% floor offers 25%, so everything clears.

Effect: p95 latent hole **46% → 0%**.

Floors of 75%, 70% and 60% give identical results, because a Dutch auction clears
at the first acceptable price. Once the floor covers maximum demand, deeper costs
nothing and adds nothing. **The floor is a safety valve, not a price.** 75% is the
shallowest floor that always clears, and therefore the correct choice.

Honest cost: the freeze converts into realised losses — ENRK p95 5.0% and kFIAT 2%
at −85%, with redemption present.

---

## 5. Redemption — mechanism #1, currently unimplemented

| Parameter | Value | Status |
|---|---|---|
| Redemption fee | 1% | ✅ |
| Target ordering | **Lowest ICR first** (Liquity's rule) | ✅ |
| Minimum vault ICR to redeem against | **100%** | ✅ |
| Redeemable tranche | ENRK only | ✅ |

Redemption exists today only as error variants and a fee constant. **It must be
implemented.** It halves losses under stress and needs no liquidator capital, so it
functions when auctions cannot.

Its structural limit: at face value, `new ratio = (a−r)/(b−r)` improves a healthy
vault and degrades an underwater one. Below 100% ICR the collateral to honour face
value does not exist. At −95%, 26% of redemption demand finds no eligible vault.

Note (2026-11-17): in the simulator, redemption demand is an exogenous schedule; with it switched off, the candidate architecture's ENRK p95 at KAS −85% on a flat index rises from 13.8 to 20.0 (W2). 'Halves losses' is therefore model-dependent.

Lowest-ICR-first is deliberate: it pays down the worst debt and improves system
health. Those owners are dispossessed of collateral at par, involuntarily, having
done nothing wrong beyond being the least collateralised.

---

## 6. Fees and treasury

| Parameter | Value | Status |
|---|---|---|
| Mint fee | 2% | ✅ |
| Liquidation fee | 4% | ✅ |
| Redemption fee | 1% | ✅ |
| Recurring stability fee | **Yes** (owner decision 2026-11-13); rate, accrual base, denomination and recipient not decided (ECONOMICS-VERIFICATION section 9 items 3-4) | ✅ decision, ❓ parameters |
| **Fee denomination** | **KAS, taken from vault collateral** | ✅ |
| Treasury share | 20% until the cap, then **0% forever** | ✅ |
| **Treasury cap** | **2,500,000 peg units** (~$300k) | ✅ |
| Fee destination after the treasury cap | **open; fees are never burned (owner 2026-11-13) and must remunerate; recipient(s) not decided** | ❓ |

**Why fees are taken in KAS rather than minted as ENRK.** Three reasons:

1. The master invariant becomes exact: `enrk_supply == Σ debt_enrk`. No fee-minting,
   no 80/20 rounding remainder.
2. No supply inflation from fees.
3. The protocol accumulates an **exogenous** asset. This was the fundamental defect
   of the Stability Pool: its ammunition was denominated in the asset it defends,
   so its purchasing power collapsed with the crisis it existed to fix.

Cost: taking KAS lowers the vault's ICR, so the preflight check must account for it.
An implementation detail, not a design problem.

**Treasury shape:** an amount cap, not a time taper. A time-based taper is a bet on
adoption speed — too slow and it raises nothing, too fast and it raises ten times
what is needed. An amount cap is self-limiting, publicly verifiable on-chain, and
the only way to "game" it is to reach it faster, which ends the treasury sooner at
the gamer's expense.

**Rationale:** an immutable protocol has nothing to fund after launch — it ships
once and can never be updated. Costs are front-loaded. A perpetual claim with no
corresponding obligation is a rent.

**The 2.5M figure**, at roughly $0.12/kWh, covers: economic audit (30–70k),
legal review (10–30k), five years of infrastructure (15–40k), frontend (20–50k),
bug bounty (50–100k), and development compensation (80–120k) — assuming the two
code audits are ecosystem-supported. If they are not, there is a shortfall to be
found elsewhere. That is the conservative, publicly defensible choice: the number
can be justified line by line, which matters more than its generosity.

---

## 7. The insurance reserve — analysed, deferred, layer-dependent

The proposal: accumulated fee KAS forms a protocol-owned reserve covering shortfalls
that liquidation and redemption cannot.

**Sizing.** Fees yield roughly 1–3% of debt per year. Residual losses to cover are
~7.5% of total debt at the p95 −95% scenario. Three to seven years of accumulation
per tail event — reasonable for an insurance fund (SAFU, Aave's Safety Module work
this way), but it means **no protection during the years the protocol is most
fragile**, and crypto delivers a −85% roughly every four years.

**The disqualifying flaw in the simple form.** A finite, publicly visible reserve
that pays whoever arrives first creates a first-mover advantage: the rational
response to stress is to exit before it empties. That is a bank-run trigger. It is
the identical argument used to reject the gold reserve, and it survives the two
genuine improvements this version has (no custodian, no human discretion), because
the flaw comes from finiteness and visibility, not from custody or discretion.

**An additional attack surface.** A rule of the form "top up any liquidation
shortfall" converts oracle errors from "someone loses" into "the reserve pays",
which **subsidises attacks on the oracle**.

**The only sound form.** The reserve pays no individual. It counts as collateral and
is consumed **pro rata across all affected holders** in a shortfall. Everyone
receives the same fraction regardless of when they act, so there is no race.

**But pro-rata socialisation requires global aggregate state** — direct in an
account model, and precisely what Kaspa L1's UTXO model cannot express.

**Consequence (revised 2026-11-17):** the execution layer is decided: Kaspa L1, Igra not retained (owner, 2026-11-13), and the owner has ruled that fees are never burned. The earlier recommendation to burn the fee KAS on L1 is withdrawn. A pro-rata reserve needs global aggregate state, which the UTXO model cannot express directly; its L1 form is an open question (ECONOMICS-VERIFICATION P5: 'counts as collateral' has no verified L1 form).

For immutable code, adding a mechanism whose race dynamic is already known is worse
than adding nothing.

---

## 8. Circuit breaker

| Parameter | Value | Status |
|---|---|---|
| Peg deviation threshold | 10% | ✅ |
| Oracle downtime threshold | 360 minutes (6h) | ✅ |
| Override | **None possible** | ✅ |

Note (2026-11-17): ECONOMICS-VERIFICATION section 1 finds the breaker as coded harmful if it halts liquidations (unbacked debt 19.9% to 86.8% at index x2). Whether the breaker may ever act on liquidations, and on what trigger, is an open owner decision (section 9, item 2).

---

## 9. Known defects carried into the specification

**The Stability Pool cannot buy.** `attempt_buyback` computes a cost, never debits
it, and reduces the pool's own ENRK balance. It is a burn, not a buyback: no bid is
placed, no sell pressure absorbed. Its ammunition is denominated in the asset it
defends. With redemption implemented, redemption supersedes it — anyone converts
ENRK to KAS at par, a stronger floor than a pool buying at a discount. **Either fix
it or remove it, and stop claiming mechanism #3 exists.** For immutable code,
removing is safer than fixing.

**Recovery Mode buys nothing.** Modelled at −85%, it triggered on 47 of 60 days and
improved the p95 latent hole by zero points. It accelerates eligibility while the
failure is in execution. In Liquity it works because a Stability Pool absorbs
liquidations without a bidder — the two are a pair. Its unavailability on Kaspa L1
therefore costs nothing.

---

## 10. Still open

1. **Execution layer — decided by the owner, 2026-11-13: Kaspa L1; Igra not retained.** The oracle construction was measured on September 6, 2026 and re-measured on September 15 against Argent `e76ee07` and Silverscript v1.0.0, where every figure reproduced (Q1a, Q1b yes; ceilings N = 642/532 for a pure consumption round, bounded by transient mass; script size negligible). Block inclusion near the limit was executed on testnet-10 (AUDIT section 13.3b: N = 640, included in about 8 s, lightly loaded testnet, no mainnet contention test). A whole-population refresh at a changed price works on testnet-10 up to N = 46 for the contract form tested (ECONOMICS-VERIFICATION section 10.2). Core-developer confirmation of the sibling-covenant-id reading is still outstanding. See [`REMEASUREMENT-2026-09-15.md`](REMEASUREMENT-2026-09-15.md).
2. **Oracle identity binding (Q1c)** — `covenant_id` cannot be a compile-time
   constant, so the vault carries it in its own state. Reframed on September 15:
   the binding to secure is **asset → vault**, since a forged vault is inert
   unless it can mint real ENRK, and a single-id `MinterProxy` forces a common
   ancestor that every mint would contend on. See
   [`ORACLE-BINDING.md`](ORACLE-BINDING.md). **A security question on immutable
   code, and unsolved.**
2b. **Undefined behaviour in the Argent sources** — `icr_percent` divides by an
   unchecked `debt` and overflows above ~9.2 KAS of collateral, in both variants
   and both entries; the compiler accepts it without a diagnostic. On the current
   mainnet engine both fail closed, which makes affected vaults impossible to
   liquidate or withdraw from rather than exploitable. An arithmetic discipline
   must be written into this specification and into the audit scope. See
   [`UNDEFINED-BEHAVIOUR-EXPOSURE.md`](UNDEFINED-BEHAVIOUR-EXPOSURE.md).
2c. **The form of the round transition** — `sweep` as written is a 1→2 split, so
   the atomic round transition claimed in `L1_NATIVE_REDUCED_SPEC` §2.3 does not
   hold as written. Design decision, gates the next measurement.
3. **Oracle variant A or B** — A allows ~21% more N; B incurs zero storage mass
   under a falling price and locks negligible capital. Not decided.
4. **Fee destination after the treasury cap** — open. Constraint: fees are never burned (owner 2026-11-13); recipient(s) and the fee reserve's role (loss absorption versus incentives) are open owner decisions.
5. **Stability Pool: fix or remove** — open (AUDIT section 7 D proposes removal with bids payable in ENRK; not decided).

---

## Sources

[`STRESS-TEST-CRASH-RESULTS`](STRESS-TEST-CRASH-RESULTS.md), [`RECOVERY-MODE-ANALYSIS`](RECOVERY-MODE-ANALYSIS.md), [`REDEMPTION-ANALYSIS`](REDEMPTION-ANALYSIS.md), [`EXECUTION_TARGET_ASSESSMENT`](EXECUTION_TARGET_ASSESSMENT.md), [`L1_NATIVE_REDUCED_SPEC`](L1_NATIVE_REDUCED_SPEC.md), [`PHASE_4_ARCHITECTURE_PROPOSAL`](PHASE_4_ARCHITECTURE_PROPOSAL.md), [`GITHUB-ISSUE-46-UPDATE`](GITHUB-ISSUE-46-UPDATE.md).
