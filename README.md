# ENRK - Kaspa Energy Reserve Stablecoin

## Project Overview

**ENRK** (Kaspa Energy Reserve) is a decentralized stablecoin on the Kaspa network, backed by the thermodynamic value of Kaspa's proof-of-work energy.

**Key Principles:**
- No central governance (immutable by design)
- No DAO (code is law)
- Backed by real energy index (not USD/fiat)
- Self-regulating via 5 market mechanisms
- No admin keys or upgrade proxies

## Quick Links

- **Design Philosophy**: `docs/design/Immutable-By-Design.md`
- **Final Formula**: `docs/specifications/Final-Recommendation.md`
- **Technical Spec**: `docs/specifications/Frozen-Parameters.md`
- **Auto-Equilibrium**: `docs/analysis/Hedging-Mechanism.md`
- **Deployment Plan**: `docs/design/Deployment-Strategy.md`

## Project Structure

```
docs/
  design/           - Philosophy, architecture, deployment strategy
  analysis/         - Research, backtesting results, economic analysis
  specifications/   - Technical specifications, frozen parameters

contracts/igra/     - Rust smart contracts (Kaspa Igra protocol)

tests/backtesting/  - Simulation framework, historical testing

scripts/            - Deployment scripts, utilities

research/           - Economic theory, game theory analysis
```

## Timeline

- **Q1 2027** (Jan-Mar): Testnet phase, community review
- **Q1 2027** (Mar): Hardening & auditing
- **Q2 2027** (Apr-May): Mainnet beta (50-100M TVL cap)
- **Q2 2027** (Jun+): Production (unlimited TVL)

## Token Details

**Primary Token: ENRK**
- Full Name: Kaspa Energy Reserve
- Ticker: ENRK
- Supply: Unlimited (minted on demand via vaults)
- Peg: 1 ENRK ≈ 1 kWh of energy cost
- Redeemable: Always convertible to KAS at thermodynamic ratio

**Speculative Token: kFIAT**
- Full Name: Kaspa Speculative Finance Token
- Ticker: kFIAT
- Supply: Limited to 30% of total debt
- Purpose: Leverage/speculation, absorbs losses first
- No peg guarantee

## Key Features

### 1. Immutable Peg Formula
```
Peg(ENRK) = 0.40×Kaspa_Hashrate + 0.30×Global_Energy + 
            0.20×Kaspa_Fees + 0.10×Crypto_Adoption
```
Frozen at deployment. No changes possible.

### 2. Self-Regulating Mechanisms
1. **Convertibility** - Anyone can burn ENRK for KAS
2. **Miner Arbitrage** - Miners defend peg via profit incentives
3. **Stability Pool** - Auto-buyback during crashes
4. **Dutch Auction** - Progressive liquidations
5. **PoW Difficulty** - Thermodynamic floor

### 3. Immutable Parameters
- ICR: 200% (initial collateral ratio)
- MCR: 150% (maintenance ratio, liquidation trigger)
- kFIAT Cap: 30% of total debt
- Auction Duration: 120 minutes (100% → 85% price descent)
- Fee Split: 80% Stability Pool, 20% Treasury

### 4. Circuit-Breaker (Automatic)
- If peg deviates >10% in 60 minutes → Auto-pause
- If oracle down >6 hours → Fallback to previous price + alert
- No DAO override possible

## Use Cases

**1. Miners with Cheap Energy**
- Mine KAS at low cost
- Mint ENRK, arbitrage for profit
- Stabilize market naturally

**2. Hyperinflation Hedge**
- Argentina, Venezuela, Zimbabwe users
- Use ENRK as money (energy-backed, not fiat)
- Escape hyperinflation without USD dependency

**3. Energy Traders**
- Bet on inflation via energy prices
- Use kFIAT speculative token
- Leverage plays on energy market

## Development Status

✅ **Complete:**
- Economic analysis & backtesting
- Formula selection & validation
- Immutable design philosophy
- Technical specifications
- Auto-equilibrium mechanism

🚧 **In Progress:**
- Igra smart contract development (Rust)
- Oracle integration strategy
- Security auditing

📋 **Upcoming:**
- Testnet deployment
- Community review & feedback
- Mainnet launch

## Language

All documentation is in **English** (international project).

## Contact & Contribution

ENRK is a community-driven project. 

For questions or suggestions:
- Create issues in project repository
- Community Discord/forum discussions
- GitHub pull requests for improvements

---

**Last Updated**: September 2026
**Project Owner**: Community-maintained, immutable design
