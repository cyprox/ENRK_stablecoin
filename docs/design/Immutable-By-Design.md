# ENRK: Immutable-By-Design Philosophy

## The Core Principle

**No governance. No DAO. No admin keys. No human override possible.**

The protocol is not a system that humans manage. It is a mathematical law that
humans accept or reject at deployment.

Once deployed on mainnet, ENRK cannot be changed by anyone — including its author.

---

## Why "Immutable-By-Design" Solves the DAO Problem

### The DAO corruption paradox

```
DAO = Decentralized Autonomous Organization
But:
  • Humans vote in the DAO
  • Humans have conflicting interests
  • Whale holders vote for their profit
  • Therefore: the DAO centralises around wealthy actors

Observed:
  Terra        (LUNA governance voted through its own collapse)
  MakerDAO     (collateral policy shaped by large holders)
  Curve        (voting power captured by Yearn/Convex)
```

### The solution: remove human governance entirely

```
If no human can change the system:
  → No DAO needed
  → No corruption possible
  → No whale capture
  → No lobby groups

The only "vote" is: use it, or fork it.
```

---

## What gets frozen at deployment

All values below are compile-time constants. Their justification and the evidence
behind each figure are in [`FROZEN_PARAMETERS.md`](FROZEN_PARAMETERS.md), which is
the authoritative reference. Any discrepancy between this document and that one
should be resolved in favour of that one.

### 1. Peg formula

```
Peg(ENRK) = 0.40 × Kaspa_Hashrate_Index
          + 0.30 × Global_Energy_Index
          + 0.20 × Kaspa_Fees_Index
          + 0.10 × Crypto_Adoption_Index

Clipped to [0.1, 5.0].
Hardcoded. No contract function can change the weights.
```

**Why immutable?** Any change to the weights benefits some holders over others,
which is a corruption vector. If the weights prove sub-optimal, the community
forks to a v2 with different weights and the market chooses between them.

### 2. Collateral ratios

```
ICR (minimum to open a vault):        200%
MCR (liquidation trigger):            150%
kFIAT mint cap:                       30% of total debt, at mint
```

**Why immutable?** A higher MCR favours existing holders, a lower one favours new
borrowers. Both cannot be satisfied, so the ratio is locked at a tested value and
disagreement is resolved by forking rather than by voting.

Note that 250% ICR was tested and rejected: it moves ENRK p95 loss from 11.2% to
11.6% — slightly *worse* — while costing users 25% capital efficiency. Higher
collateral makes vaults liquidate later, at worse prices.

### 3. Liquidation auction

```
Duration:        120 minutes
Starting price:  100% of collateral market value
Floor price:     75% of collateral market value
Descent:         linear over 120 minutes
Liquidation fee: 4%
```

**The 75% floor is the single most consequential parameter in the protocol.**
Modelled liquidator demand is `4% + 18% × drawdown`; at a 95% drawdown they require
21%. An 85% floor offers 15%, so nothing clears past a 61% drawdown — the system
freezes with uncovered debt still circulating. A 75% floor offers 25%, so
everything clears. Floors of 75%, 70% and 60% give identical results, because a
Dutch auction clears at the first acceptable price. The floor is a safety valve,
not a price.

### 4. Fees

```
Mint fee:          2%
Liquidation fee:   4%
Redemption fee:    1%

Denomination:      KAS, taken from vault collateral — never minted as ENRK
Treasury share:    20% of fees until 2,500,000 peg units cumulative,
                   then 0% forever
```

**Why fees are taken in KAS rather than minted.** It keeps the master invariant
exact (`enrk_supply == Σ debt_enrk`), it adds no supply inflation, and it makes
the protocol accumulate an **exogenous** asset. That last point is the lesson of
the Stability Pool's failure: ammunition denominated in the asset you are
defending loses purchasing power exactly when you need it.

**Why the treasury is capped by amount, not by time.** A time-based taper is a bet
on adoption speed. An amount cap is self-limiting, publicly verifiable on-chain,
and the only way to "game" it is to reach it faster — which ends the treasury
sooner, at the gamer's expense. An immutable protocol has nothing to fund after
launch; a perpetual claim with no corresponding obligation is a rent.

The destination of fees after the cap is still open and follows the execution-layer
decision.

### 5. Circuit breaker

```
IF peg deviation > 10%          → auto-pause mint/burn
IF oracle feed down > 6 hours   → circuit breaker engages

No human override. No DAO vote. No multi-sig.
```

**Why immutable?** These are technical thresholds, not policy. Too aggressive
means false positives; too lenient means manipulation succeeds before the pause
triggers. Lock in a tested threshold and let a fork correct it if it proves wrong.

---

## What does NOT get frozen

```
✓ Vault opening and closing          (users decide)
✓ ENRK minting amounts               (users decide)
✓ Collateral amounts                 (users decide)
✓ Liquidation participation          (liquidators decide)
✓ Arbitrage execution                (arbitrageurs decide)
✓ Mining strategy                    (miners decide)
✓ kFIAT minting amounts              (speculators decide)
✓ Market prices                      (trading decides)
✓ PoW difficulty                     (the Kaspa network adjusts)
```

These are **economic decisions** made by participants, not **governance
decisions** made about the protocol.

---

## The oracle question

The peg requires two indices that the chain cannot produce by itself: the global
energy price and a crypto adoption measure. Hashrate and fees are native to Kaspa
and need no oracle.

**The oracle design depends on the execution layer, which is not yet decided.**
On Kaspa L1 the construction is a covenant-lineage price feed described in
[`L1_NATIVE_REDUCED_SPEC.md`](L1_NATIVE_REDUCED_SPEC.md) §2 — authenticity comes
from covenant ID lineage rather than from a signature, and round transitions are
atomic so no stale-price window exists. That construction has not been validated
by anyone who wrote the KIPs it relies on, and validating it is the current
blocker for the entire project.

What is settled, whatever the layer: the fallback behaviour is hardcoded, there is
no vote on which oracle to trust, and no multi-sig can override the circuit
breaker. If the feed degrades, the circuit breaker engages and the system pauses
rather than accepting a suspect price.

The worst case for the oracle is mispriced liquidations — bad, bounded, and
recoverable. That is a different category of risk from a custodial bridge, whose
worst case is total loss of collateral. It is the reason the L1 path is being
pursued despite being first-of-its-kind.

---

## What happens if the protocol "needs" governance?

### Scenario: the peg weights prove sub-optimal

```
→ The weights cannot be changed on mainnet. They do not need to be.

  • A v2 is developed with different weights
  • v2 deploys alongside v1
  • Users choose which to use
  • The market decides which one survives

Result: v1 stays locked for those who valued immutability,
        v2 competes on performance, no trust is required from anyone.
```

### Scenario: the oracle becomes unreliable

```
→ The fallback chain cannot be changed on mainnet. The system already handles it.

  1. The circuit breaker detects the deviation
  2. Mint and burn auto-pause
  3. The anomaly is public and verifiable on-chain
  4. Either the feed stabilises and the system resumes,
     or a v2 deploys with a different oracle strategy

Result: v1 pauses safely rather than accepting a corrupt price.
```

### Scenario: a critical bug is found in liquidation

```
→ Mainnet v1 cannot be patched.

  • Found before deployment → fixed before deployment
  • Found after deployment  → a v2 deploys with the fix,
                              v1 is deprecated by user migration

Result: no emergency governance, no admin key that an attacker
        can also use.
```

---

## The fork strategy

### This is not weakness

```
Traditional finance:
  • The system breaks → a central authority fixes it
  • Decisions are made by committee
  • Users have no choice

Immutable ENRK:
  • The system is locked → it cannot be "fixed" by governance
  • If it is wrong → the community forks
  • Users have a full choice: v1, v2, or neither
```

### How forking works

```
v1 deploys immutable, with its parameters frozen.

Later, a consensus emerges that some parameter should differ.

Decision: fork to v2
  • New code with the revised parameter
  • Audited and reviewed independently
  • Deployed alongside v1

Users migrate:
  • v1 ENRK is not automatically convertible to v2 ENRK
  • Users close v1 positions and open v2 positions,
    or stay on v1 if they prefer it

The market decides:
  • If v2 is better, v1 liquidity drains toward it
  • If v1 was right, v2 stays marginal
  • Both exist; no outcome is imposed on anyone
```

---

## The risk of immutability — stated plainly

```
1. The peg weights are genuinely bad
   → the system destabilises
   → a fork costs users a migration, but preserves decentralisation

2. The oracle sources degrade
   → the circuit breaker pauses the system
   → temporary freeze, not permanent failure

3. Collateral ratios are too strict
   → vaults are uneconomic to open
   → a fork with different ratios competes

4. A critical bug reaches mainnet
   → it cannot be patched, ever
   → this is the real cost, and no testnet fully removes it
```

**And the specific risk this project carries:** the protocol has been shown to
**freeze** rather than explode under a deep crash, and there is nobody to unfreeze
it. The 75% auction floor and the redemption mechanism are what address that, and
redemption is not yet built. An immutable protocol shipped without it would be
shipped with a known defect.

### Is this worse than DAO governance?

```
DAO governance risk:
  • Whale holders capture voting
  • The system is optimised for large holders
  • Decisions are made where users cannot see them
  • Forking is hard: it requires coordinating a majority

Immutable-by-design risk:
  • Nothing can be changed if a bug is found
  • Nothing can be optimised if a parameter is wrong
  • Users must choose between versions
  • But: no one can change it secretly, either
```

Immutability is not free. It trades the ability to repair for the impossibility of
capture. That trade is only worth making if the design is right before it ships,
which is why the analysis in this repository is adversarial toward its own
conclusions.

---

## The real governance: the deployment decision

```
BEFORE deployment:
  • Code review
  • Independent audit — code and economics
  • Adversarial scenario testing
  • "Is this right?"
  • INTENSIVE SCRUTINY

DECISION POINT:
  → deploy as-is, accepting the frozen rules
  → or do not deploy
  → or wait and demand more testing

This is the one governance moment.
After deployment: none. Just use it, or fork it.
```

An economic audit matters more here than a second code audit. The freeze found in
the stress test is a design defect in perfectly correct code — no code auditor
would have caught it. That is how stablecoins die.

---

## Philosophical core

### Law versus governance

```
Governed system:
  "We, the DAO, vote that the rule is now X."

Immutable system:
  "The rule is X. That was decided before deployment.
   This is not a vote. It is a covenant."
```

### The economic analogy

```
Governance:
  "Bitcoin's supply cap — let us vote to raise it."
  (Bitcoin refuses. The cap is law, not policy.)

Immutable ENRK:
  "ENRK's peg weights — let us vote to change them."
  (ENRK refuses. Deploy v2 instead, and let users choose.)
```

---

## Summary

Immutable-by-design answers one question: how do you stop a decentralised system
from re-centralising under whale control?

By removing the ability to control it. By making it a law rather than a governance
decision. By letting the community fork when it disagrees.

**ENRK is not managed. ENRK is not governed. ENRK is executed.**

You do not vote on thermodynamics. You accept the frozen rules, or you fork.
