# ENRK — Frozen Parameter Specification

**Date:** September 3, 2026
**Author:** cyprox

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

Chosen as "Alternative 3.5" after backtesting. The 30% uncorrelated energy hedge
cut peg drawdown from −78% to −17.3%.

**Documented cost, to be stated in any public specification:** a peg that holds
firm while collateral collapses maximises the fall in ICR. Alt 3 (pure Kaspa
indexing) leaves a 10% latent hole at −85% where Alt 3.5 leaves 17% — the hedge
costs roughly 7 points of solvency. This is the MakerDAO Black Thursday dynamic.
Not a reason to change the formula; a reason not to claim the hedge is free.

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
| **Fee denomination** | **KAS, taken from vault collateral** | ✅ |
| Treasury share | 20% until the cap, then **0% forever** | ✅ |
| **Treasury cap** | **2,500,000 peg units** (~$300k) | ✅ |
| Fee destination after the treasury cap | **see §7** | ❓ |

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

**Consequence:** this is the first concrete argument in Igra's favour to emerge in
some time, and it belongs in the layer decision. On Kaspa L1, burning the fee KAS is
the honest answer — minimal, no attack surface, no race, benefiting all KAS holders
pro rata including every vault owner. On Igra, the pro-rata reserve becomes possible
and deserves its own analysis.

For immutable code, adding a mechanism whose race dynamic is already known is worse
than adding nothing.

---

## 8. Circuit breaker

| Parameter | Value | Status |
|---|---|---|
| Peg deviation threshold | 10% | ✅ |
| Oracle downtime threshold | 360 minutes (6h) | ✅ |
| Override | **None possible** | ✅ |

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

1. **Execution layer** — Kaspa L1 covenants vs Igra EVM. Blocked on core-developer
   validation of the covenant oracle construction.
2. **Fee destination after the treasury cap** (§7) — burn on L1, pro-rata reserve on
   Igra. Follows the layer decision.
3. **Stability Pool: fix or remove** — follows from (2).

---

## Sources

`Stress-Test-Crash-Results`, `Recovery-Mode-Analysis`, `Redemption-Analysis`,
`Execution-Target-Assessment`, `L1-Native-Reduced-Spec`,
`Phase-4-Architecture-Proposal`.
