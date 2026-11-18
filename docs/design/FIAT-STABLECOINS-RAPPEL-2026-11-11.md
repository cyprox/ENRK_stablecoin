# USDT and USDC — how fiat-backed stablecoins work (reminder)

**Date:** 2026-11-11. **Status:** reminder note, uncommitted. No new analysis, no design
decision, no proposal for ENRK.

**Sources:** none consulted for this note. The sections on USDT and USDC are written from
general knowledge and were **not re-verified** against issuer documents, attestations or
the chain during this session. Figures are deliberately left out; the one dated event
cited (section 4) is from memory. Section 5 is read from this repository only.

---

## 1. Principle

Both tokens are claims on dollar-denominated reserves held by a private issuer
(Tether for USDT, Circle for USDC).

1. **Mint:** a client pays dollars to the issuer; the issuer creates the same number of
   tokens on-chain.
2. **Circulation:** the tokens are ordinary on-chain tokens (ERC-20 on Ethereum, and
   equivalents on Tron, Solana and others) and transfer freely.
3. **Redeem:** an eligible client returns tokens to the issuer, which burns them and
   pays out dollars.
4. **Peg:** issuance and redemption at 1 USD give arbitrageurs a reason to buy below 1
   and sell above 1. The peg rests on that redemption right and on trust in the
   reserves, not on any on-chain mechanism.

## 2. Differences between the two

| | USDT (Tether) | USDC (Circle) |
|---|---|---|
| Reserves | Mostly short-term US Treasuries, plus other assets | Mostly cash and short-term US Treasuries |
| Disclosure | Periodic attestations | Periodic attestations, US regulatory framework |
| Main usage | Exchange trading, emerging markets | DeFi, institutions |

## 3. Properties shared by both

- Centralised issuer, off-chain reserves, redemption restricted to approved clients.
- The issuer can **freeze or blacklist addresses** and can be compelled to by authorities.
- Upgradeable or administered contracts: the issuer keeps control after deployment.

## 4. Risks of the model

- **Counterparty risk:** the token is worth what the issuer's reserves and solvency are
  worth.
- **Banking risk:** USDC briefly traded well below 1 USD in March 2023 when part of its
  reserves was held at a failed bank (from memory, price not re-checked).
- **Censorship:** frozen addresses cannot move funds.
- **Regulation:** rules are changing (GENIUS Act in the US, MiCA in the EU); not
  re-checked here.

## 5. Where ENRK stands, from this repository only

Facts read in [`README.md`](../../README.md), 2026-11-11. Nothing is interpreted.

| | USDT / USDC | ENRK (as specified) |
|---|---|---|
| Unit of account | USD | 1 kWh of thermodynamic value, "no USD, no fiat" |
| Backing | Off-chain reserves held by the issuer | KAS collateral, over-collateralised (ICR minimum 200 % at mint, MCR 150 %) |
| Control | Issuer, with freeze and administration | "Governance: none", every parameter frozen at compile time |
| Loss absorption | Issuer's reserves and balance sheet | kFIAT junior tranche, capped at 30 % of debt at mint |

The README also states: design complete, implementation not started, no code deployed,
no audit performed.

---

Related studies: [`FRAX-COMPARISON-2026-11-11.md`](FRAX-COMPARISON-2026-11-11.md),
[`MONOLITH-COMPARISON-2026-11-10.md`](MONOLITH-COMPARISON-2026-11-10.md).
