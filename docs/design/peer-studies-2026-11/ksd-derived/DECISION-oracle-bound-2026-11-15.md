# Decision sheet: should ENRK's collateral oracle bound how fast its price can move?

**Date:** 2026-11-15. **Status:** decision sheet for the owner. **Nothing is decided here**: the recommendation in section 5 is mine and no number below is a proposed value. Written for the project owner (ENRK design decision; related audit item I26, open).
Script: `oracle_bound_grid.py`, output `oracle_bound_grid_output.txt` (arithmetic only, reproduce with `python3 -I -B`).

## 1. The question
The audited KAS collateral oracle (variants A and B, `AUDIT-2026-11-09.md` §13, I26) lets the publisher key set any price in one round: A even accepts 0; B refuses 0 but has no upper or rate limit. Only a signature stands between the price and every vault. Should the oracle script itself limit how far and how fast the price can move?

## 2. Facts already in the repository
- A per-sweep bound exists and was executed locally: `oracle_b.ag`, ±10.00% per sweep accepted, ±10.01% rejected, price in [P_MIN, P_MAX], `GAP` = 600 DAA (about one minute) via a clock field (`econ-v4`, P20). All its constants are test values.
- Its limit, in the report's own words: a per-sweep bound alone does not bound the hourly move; GAP and MOVE "must be sized together (owner decision)". The corrected figure is about 117 to 300 times per hour at one-minute gaps (`ECONOMICS-VERIFICATION` §2, P20); the grid below reproduces it (x304 per hour for 10% per minute).
- A compromised publisher key can rotate to itself; there is no recovery key or delay without a clock (P20 limit 3). The oracle is immutable by design: no pause, no governance.
- A tight per-round bound buys a larger refresh population N: a falling price costs storage mass proportional to N and to the depth of the fall (`L1_NATIVE_REDUCED_SPEC` §2.4, exact maximum N not established).
- A bound that is too tight makes the price lag a real crash: `econ-v3` (failure-modes table) gives about 14 minutes to reflect −25% at 2% per minute; the triggers are late by about |ln(1−d)/B| gaps.
- KAS's worst observed single day is −24.9% (`r4-market.md`, 2026-11-10); intraday data is not held.
- KSD's choice for comparison: liquidation price may fall at most 25%/h and mint price rise at most 10%/h (whitepaper, recomputed; see the review in this folder). Equivalent per-sweep moves: down 25%/h = 0.478% per sweep at one sweep a minute, 4.68% at one every 10 minutes; up 10%/h = 0.159% and 1.60%.

## 3. What a bound buys and costs
**Buys:** (a) a time window in which vault owners can add collateral or repay if the key is compromised or the feed is wrong, since no pause exists (adding collateral and repaying stay possible; KSD's 30-minute halt of priced actions has no ENRK counterpart); (b) a limit on what a bad round can do in one transaction; (c) per I26, a floor and a per-sweep limit close "price 0" and one-round jumps outright.
**Costs:** (a) liquidations and the peg index lag a real crash (the delay measured in `NOTE-asymmetric-price-limits-2026-11-15.md`: about 60 min for a 200% vault with a 25%/h limit, then ENRK's own 120-min auction); (b) a compromised key still moves the price at the allowed rate, so the bound limits speed, not direction; (c) the constants cannot change after launch.
**Not measured anywhere in the repository:** the benefit under an oracle error or manipulation scenario (no such scenario exists in W2) and intraday KAS moves.

## 4. Options
| | What | Fixes I26 | Hourly protection | Crash lag | Complexity | Notes |
|---|---|---|---|---|---|---|
| A | No bound (status quo) | No | None | None | None | Trust is the key alone |
| B | Absolute floor and ceiling only (P_MIN, P_MAX, price > 0) | Partly (price 0 and absurd values) | None | None | Low | Already in variant B and in `vault_stale`/`vault_redeem` guards |
| C | B plus per-sweep move limit with a minimum gap (P20 as executed) | Yes | Weak unless the gap is sized: 10% per minute allows ×304 per hour; 2% per 10 min allows ×1.13 per hour | Depends on constants (table below) | Medium (needs the clock field, already executed) | MOVE and GAP must be chosen together |
| D | C with different limits up and down, applied to the price used for minting and the price used for liquidation (KSD style) | Yes | Strongest | Highest | High (two price fields or derived rules in the vault; not tested on L1) | Benefit unmeasured; wait for the intraday model |

Reading the grid (`oracle_bound_grid_output.txt`), publishing at the minimum gap:
- 10% per sweep at 1-minute gaps reflects a −25% day in 3 minutes and a −50% fall in 7, but allows ×304 per hour: no real protection.
- 2% per sweep at 1-minute gaps: ×3.28 per hour, 14 and 34 minutes.
- 2% per sweep at 10-minute gaps: ×1.13 per hour, 142 and 343 minutes.
- 1% per sweep at 10-minute gaps: ×1.06 per hour, 286 and 690 minutes (nearly 12 hours to reflect −50%).
The same numbers are what a thief with the key can do: for 2% per minute, −50% in 34 minutes, which is the time vault owners would have.

## 5. My recommendation (not a decision)
1. **Do at least option B now**: price > 0, floor and ceiling, in both the oracle and every vault entry. It costs almost nothing and closes the most dangerous case of I26 (price 0).
2. **Choose C over A**, on the logic that with an immutable design and no pause, the only reaction time owners can get is built into the oracle. Do not choose the numbers by feel: pick MOVE and GAP together as one hourly rate, from two measurable criteria: (i) the crash lag the owner accepts, using the delay table of the note and an hourly crash model; (ii) the reaction time owners need if the key is stolen. These two pull in opposite directions; the grid shows both.
3. **Defer D** until an intraday model and an oracle-error scenario exist; its benefit is unmeasured and its on-chain form is untested.
4. Whatever is chosen, keep the vault-side checks (0 < price ≤ P_MAX) because the oracle bound does not protect an old vault script (P20 limit 5).

## 6. What would make the choice solid (needs owner go)
- An hourly price series for KAS, then an hourly crash stage next to W2 (new stage, options OFF = previous behaviour, equivalence check).
- An oracle-error scenario (stuck price, ×k price, stolen key) in that stage.
- A measurement of the largest N a bounded per-round move allows on testnet-10 (the spec says tighter bounds allow larger N; the exact limit is not established).

## 7. Decisions asked of the owner
1. Option B now (price > 0, floor, ceiling) in oracle and vaults: yes or no?
2. A per-time bound (C) in principle: yes, no, or only after the intraday model?
3. If yes: the criterion to choose MOVE and GAP (crash lag accepted, owner reaction time) and who sets the numbers. I will not propose values without the model.
4. Whether option D stays deferred.
