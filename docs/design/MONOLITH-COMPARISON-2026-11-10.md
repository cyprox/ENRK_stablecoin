# Monolith Market — durability review and comparison with ENRK

**Date:** 2026-11-10. **Status:** read-only study, uncommitted. Nothing here is a design
decision: every "idea for ENRK" is a proposal awaiting owner validation.

**Sources:** https://docs.monolith.market/ (16 pages + FAQ, bug bounty, risks) and the
public repository https://github.com/MonolithMarket/Monolith (branch `main`, 241 commits,
code read only, nothing executed, tests not read).

**Audit PDFs (read in full via pdftotext, 2026-11-10):** Electisec (May 2025), Sherlock
contest (Dec 8-14, 2025), and two ChainSecurity reports. The two ChainSecurity PDFs are
both marked **DRAFT**: one dated 25 March 2026 (3 versions) and one dated 14 April 2026
(4 versions, final commit `f5a6fa6a`). The "October 2025" ChainSecurity report listed in
the docs is the first version (6 Oct 2025, commit `38ce8ee7`) of that same engagement,
not a separate PDF, so I have no separate October document.

**Not read / unverified:** the three AI reviews (Sherlock AI, Nemesis, Zellic v12),
`Lens.sol`, `Metadata.sol`, test contents and CI. Only the Sherlock issue titles and the
H-1 text were read, not each issue's fix status. No TVL, volume, instance count or team
data exists in the documentation. Findings marked *(code reading, not tested)* have not
been reproduced. The deployed mainnet commit was not matched to any audited commit.

---

## 1. What Monolith is

Permissionless factory of single-collateral stablecoins on Ethereum mainnet. One
deployment = `Lender` + `Coin` (ERC-20) + `Vault` (ERC-4626 staking). Each borrower picks
a mode: **paid debt** (variable interest, not redeemable) or **free debt** (0 %,
redeemable). The ratio of free debt is the only input of the rate controller, so borrower
choice acts as an "indirect oracle" of peg pressure. No market price feed is used for the
peg.

## 2. Durability assessment

Summary: serious, audited design with no admin upgrade path, but with unbuffered loss
handling, an unproven peg mechanism and no verifiable adoption.

### Positives (from code)
- No proxy, no `delegatecall`, no pause function. Core parameters (`collateralFactor` ≤
  85 %, feed, `minDebt`, staleness threshold) have no setter.
- Operator powers are bounded and expire: risk setters (`setHalfLife`,
  `setTargetFreeDebtRatio`, `setRedeemFeeBps`, `setMaxBorrowDeltaBps`) are `beforeDeadline`
  only, deadline ≤ 1460 days. After it, only operator rotation, local reserve fee
  (≤ 10 %) and `setManager` remain.
- Interest is lazy (no keeper): accrued at the start of almost every state-changing call.

### Concerns
1. **No loss buffer.** Write-off (debt > 100× collateral value, code-confirmed) spreads the
   erased debt pro-rata over all remaining borrowers, free and paid. No reserve, no
   insurance fund, no seniority.
2. **Peg mechanism unproven.** Rate controller has no price input and no maximum rate
   (only an overflow guard at `uint88.max`). `k = ln2/halfLife`: the rate doubles every
   half-life below the target band. With a 30-day half-life, 2 % grows to about 92 %/yr
   after one year below target (own calculation from the code). The PSM buy path is
   temporary and closes at the immutability deadline.
3. **Fixed liquidation incentive.** 0 to 10 % linear between LTV = CF and CF + 5 points,
   25 % close factor, min 10,000 Coin. No auction, no grace period.
4. **Stale-oracle path (by design, confirmed by ChainSecurity).** On a stale price the
   system enters reduce-only and the price decays linearly to zero over 24 h;
   **liquidations and redemptions stay enabled at the decaying price**
   (ChainSecurity §2.2.3.3). Only a reverting or zero feed disables them. So after the
   decay a liquidator can seize collateral for a negligible Coin amount: the protocol
   accepts this as a wind-down mechanism, it is not a bug. Electisec Low-1 flagged the
   `price = 1` fallback; the team kept it ("extra precaution against division by zero").
   My earlier suspicion that this was an oversight is therefore withdrawn. ChainSecurity
   states a 25-hour stale limit; I did not reconcile this with the code's
   `stalenessThreshold` (per-instance, unbounded). `roundId`/`answeredInRound` are not
   checked *(code reading)*.
5. **Other code-level points** *(reading only)*: no `ReentrancyGuard` in `Lender`; in
   `liquidate` collateral is transferred before the Coin `transferFrom`; interest above
   `uint120.max` is silently dropped while `lastAccrue` still advances; interest accrual
   is skipped silently if the gas check fails (`INTEREST_CALCULATION_GAS_REQUIREMENT`
   40,000).
6. **Documentation vs code drift.** README says redemption is pro-rata, code targets one
   borrower per call; README says Vault fee up to 25 %, code 10 %; README says write-off
   "equally", code pro-rata by shares. A commit of 2026-05-18 "Remove free
   debt and add permanent event trigger mode" was merged then reverted on 2026-05-28, so
   the design is being explored. Open issue #62 reports a DoS in `redeem` through the
   `minDebt` check; the condition is still in the code (`Lender.sol:447`).
7. **Audit record (now read).**
   - **Electisec, 20-27 May 2025, dev branch.** 1 Critical (`lastAccrue` uninitialised, so
     the first accrual computes about 55 years of interest; fixed `395e6d9`), 1 Medium
     (write-off collateral locked in Lender; fixed `3a84b27`), 4 Low (price fallback = 1
     acknowledged and kept; `getDebtOf` stale after epoch change acknowledged; last wei of
     free debt not redeemable; no maximum rate). It rates testing "Average" and warns the
     free-debt/redemption mechanism is novel and under-tested. `Lens` was out of scope.
   - **Sherlock contest, 8-14 Dec 2025** (audited commit `b36e9ef0`, final `41eb720e`):
     1 High, 6 Medium, all marked fixed or acknowledged ("Not Fixed and Not Acknowledged":
     0). H-1: rounding in the pool-based redemption lets a user inflate the share/debt
     ratio and mint about $1 B of unbacked Coin. M-1: with a single bad-debt user anyone
     can mint unbacked tokens. M-4: accounting breaks when redeeming with a bad-debt
     position. M-5/M-6: wrong interest calculation, and accrual stuck when `wadExp`
     underflows. M-2 (inconsistent health checks) and M-3 (ERC-4626 `totalAssets`) also.
   - **ChainSecurity, 6 Oct 2025 to 14 Apr 2026, 4 versions.** 0 Critical, 5 High, 5
     Medium, 13 Low. Final state: 1 High open, 5 Low open (all "risk accepted").
     Resolved Highs: price in wrong decimals, PSM decimals mismatch, ERC-777 reentrancy
     (solved by dropping support for reentrant tokens, not by a full fix: `liquidate`
     and `adjust` order issues were noted), share deviation from redemption rescaling
     (fixed by switching to per-borrower redemption).
   - **Still open at the final version:** *Debt share price inflation via write-off*
     (High, partially corrected, risk accepted; the team only blocks new borrowing when
     total debt exceeds collateral value); unbounded interest rate (with a 24 h
     half-life and a 2 % start, debt multiplies by about 1.4e3 in 93 days and by about
     6.7e12 in 182 days under continuous compounding; the team calls such coins "dead");
     redemptions front-runnable by switching to paid status; `setRedemptionStatus` can
     create phantom debt; after the last position is written off, Coin supply can
     outlive all debt (insolvent restart). These are "risk accepted" and are real
     design limits.
   - **Gap:** the DAO contracts are in no audit scope (redeployed 2026-10-22). Both
     ChainSecurity PDFs are DRAFT.

   **Fix verification (2026-11-10, shallow clone of `main` HEAD `3511ab5`, code read,
   nothing executed, no test run).** All audited commits exist in `main` history
   (`b36e9ef0`, `41eb720e`, `f5a6fa6a`, `38ce8ee7`). Sherlock states its fixes are in PR
   #42, but that PR shows no diff and 0 commits on GitHub, and `main` was force-pushed
   on 2026-05-08, so I checked the code instead:

   | Finding | Sherlock status | State at HEAD (my reading) |
   |---|---|---|
   | H-1 rounding / unbacked borrow | fixed (PR #42) | Epoch rescaling removed: 21 `epoch` occurrences in `Lender.sol` at the audited commit, 0 at HEAD. Redemption is per borrower. Structural fix. |
   | M-1 single bad-debt user mints unbacked | fixed | `totalDebt > totalCollateralValue` forces `reduceOnly` (`Lender.sol:694-696`, PR #44 merge `41eb720e`, 16 Mar 2026). |
   | M-2 inconsistent health checks | fixed | `adjust` requires `debt <= borrowingPower` (l.292); liquidation returns 0 when `borrowingPower >= debt` (l.616). Consistent at equality. |
   | M-3 ERC-4626 `totalAssets` | **acknowledged, not fixed** | `totalAssets` unchanged (`balanceOf + pending interest`). |
   | M-4 redeem with bad-debt position | fixed | The epoch-based pooled redemption it relied on no longer exists. |
   | M-5 interest through `MIN_RATE` | fixed | Piecewise integral at `InterestModel.sol` matches `(r0 - rmin)/k` plus a flat part; commit `f211ea6` (2026-02-25). I checked the formula by reading only, no numeric test. |
   | M-6 `wadExp` underflow | fixed | `if (growthDecay == 0) growthDecay = 1;` present; commit `aa6d2fa` (2026-02-25). |
   | Issue #62 (`minDebt` check in `redeem`) | open, no maintainer reply | Condition still present (`Lender.sol:447`). Not fixed. |

   **Execution (forge 1.9.0, `main` HEAD `3511ab5`, fork test `LenderFork.t.sol` excluded
   because it needs an RPC).** 164 tests: 163 pass, 1 fails
   (`test_repay_withInterestAccrual`). The failure is a test artifact: it also fails at
   the final audited commit `f5a6fa6a` and at the mainnet deployment commit `857f8d0`,
   and it passes with `FOUNDRY_VIA_IR=false` (256 fuzz runs). With `via-ir`, the line
   `initialTimestamp = block.timestamp` is evaluated after the `vm.warp`, so the
   assertion compares the wrong value; `lastAccrue` itself is updated correctly.
   Passing tests that cover the fixes: `test_calculateInterest_wadExpUnderflow` (M-6),
   `test_writeOff_singleBadDebtBorrowerCannotMintUnbackedTokens` (M-1),
   `test_writeOff_success` / `notDeepEnoughUnderwater`, the reduce-only tests, the
   `test_redeem_*` tests (per-borrower redemption, replacing the pooled one in H-1/M-4).
   I did not rebuild the original H-1 or M-4 exploits: the code they target (epoch
   rescaling) is gone, so the fix rests on absence of that code plus the passing tests.
   **Issue #62, executed PoC** (scratch test, not in the repo): borrower with 5000
   collateral and 1500 debt, price dropped to 0.25 (collateral value 1250). Redeeming
   "everything" reverts with `Debt below minimum and larger than 0`; redeeming 400
   succeeds and leaves 1100. So #62 is real but limited to a position that is already
   undercollateralised: a redeemer can still choose a smaller amount, it is not an
   unconditional DoS.

   ChainSecurity's own statuses are those listed above (1 High and 5 Low "risk
   accepted"); I did not re-check each of the 13 Low and 5 Medium against the code.

   **Deployed code vs audited code.** Mainnet deployment commit is `857f8d0` (2026-04-24),
   10 days after the final ChainSecurity commit `f5a6fa6a` (2026-04-14). Between the two,
   `Lender.sol` and `Factory.sol` changed (diff read): events added (`InterestAccrued`,
   `ReservesPulled`), `minTotalSupply` renamed `psmVaultMinTotalSupply`,
   `timeUntilImmutability` bound `<` changed to `<=`, and **`pullLocalReserves` made
   permissionless and now mints to the operator** (was `onlyOperator`, minting to the
   caller). These look minor but are unaudited. A new `Metadata.sol` (214 lines) is also
   unaudited. I did **not** compare the deployed bytecode on Etherscan with the source.
   The later "remove free debt" work (May 2026) was reverted on `main` (`3511ab5`), so
   `main` still has free debt.
8. **Licence and traction.** LICENSE.md is a non-commercial audit licence (SPDX
   UNLICENSED), not open source; 1 GitHub star at the time of reading. Operator status
   (EOA / multisig / timelock) of Factory V2 is undocumented.

### Verdict
Cannot be qualified as durable or fragile from documentation alone. The audit history is
substantial and the early flaws (a Critical, a High that minted $1 B of unbacked Coin)
were found and fixed, which is a good sign for process but also shows the redemption and
share-accounting design was fragile before it was rewritten to per-borrower redemption.
Residual risks accepted by the team: runaway interest, bad-debt share inflation,
insolvent restart. Nothing shows peg resilience under stress or real usage. To conclude,
check on-chain history (Etherscan/DefiLlama).

## 3. Comparison with ENRK

| Topic | Monolith | ENRK (per repo state) |
|---|---|---|
| Loss absorption | Pro-rata socialization to all borrowers | Waterfall / seniority design (cascade not yet implemented per audit) |
| Peg signal | Free-debt ratio, no price | Oracle-based (price UTXO, measured on TN10) |
| Liquidation | Fixed 0–10 % incentive, 25 % chunks | 180 vaults in one tx on a single price (TN10) |
| Redemption | Single targeted borrower, free-debt only | Specified, not implemented |
| Upgrade / admin | None; operator bounded and time-limited | Not implemented; execution layer undecided |
| Execution env. | EVM, accounts | Kaspa UTXO covenants |

## 4. Ideas for ENRK — proposals only, none validated

Each item needs a feasibility check on Kaspa covenants before any decision.

1. **Targeted redemption.** Single-borrower redemption avoids a pro-rata sweep, which is
   costly in a UTXO model. Fits the unimplemented redemption item of the audit.
2. **Free vs paid debt split as a rate signal.** Gives a peg signal with no extra oracle.
   Open question: where the aggregate free-debt ratio lives in covenant state (same
   contention issue as the oracle-binding question Q1c).
3. **Exponential rate controller with a floor** (`r·exp(k·dt)`, floor 0.5 %), but with an
   explicit maximum rate, which Monolith lacks.
4. **Graceful stale-oracle degradation.** Linear price decay plus reduce-only is worth
   comparing with ENRK's own stale-price guard. Monolith deliberately keeps liquidations
   and redemptions live while the price decays to zero (point 2.4); whether ENRK wants
   that is a design decision, not a given.
5b. **Lessons from the audit record for our redemption/shares design:** avoid pool-based
   share rescaling (Sherlock H-1, ChainSecurity High); add a maximum rate; define the
   state after the last position is closed; bound debt-share inflation from write-offs.
5. **Operator powers that expire.** An immutability deadline with enumerated setters is a
   clean pattern to compare with ENRK's governance surface.
6. **Keep the loss waterfall.** It is the clearest structural difference and Monolith's
   weakest point.
7. **Do not copy:** fixed capped liquidation incentive without auction; unbounded rate;
   silent skip of accrual.
8. **Documentation hygiene.** Monolith's README/code drift illustrates the risk in our own
   unreproduced figures (kFIAT "2 %"): tie every number to a script and commit.

## 5. Next steps (need owner go)

- Read the three AI reports.
- Compare the mainnet deployed bytecode with commit `857f8d0` (Etherscan/Sourcify).
- Rebuild the original H-1 and M-4 exploits against the audited commit `b36e9ef0` to
  show they fail at HEAD (not done: only the fix tests were run).
- Read `Lens.sol` and the tests.
