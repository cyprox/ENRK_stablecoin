# ENRK Project Manifest

## Documentation Status

### ✅ Complete (English, Ready)
- `docs/design/Immutable-By-Design.md` - Philosophy & governance elimination
- `docs/specifications/Frozen-Parameters.md` - All immutable parameters specified
- `docs/specifications/Token-Naming-ENRK.md` - Branding rationale (ENRK > ENRG)
- `docs/design/Deployment-Strategy.md` - Testnet → Mainnet → Fork path
- `docs/analysis/Auto-Equilibrium-Mechanism.md` - 5 market mechanisms (English)

### 🔄 Needs Integration (From Cloud Project)
- `docs/specifications/Final-Recommendation.md` - Alt 3.5 formula choice + backtesting
- `docs/analysis/Hedging-Mechanism.md` - How protocol defends peg

### 📋 To Translate to English (Currently French)
- `Spécification-Technique-ENRG.md` → `docs/specifications/Technical-Specification-Igra.md`
- `Backtesting-Formules-ENRG.md` → `docs/analysis/Backtesting-Results.md`
- `Analyse-Stablecoins-Échoués.md` → `docs/analysis/Failed-Stablecoins-Analysis.md`

---

## Development Roadmap

### Phase 1: Foundation (CURRENT) ✅
- [x] Economic analysis & formula selection
- [x] Backtesting & validation
- [x] Immutable design philosophy
- [x] Parameter specification
- [x] Auto-equilibrium mechanism
- [x] Token branding (ENRK)
- [x] Project structure setup
- [ ] Export all docs to local folder
- [ ] Create Igra smart contract skeleton

### Phase 2: Implementation (Q1 2027, Jan-Mar)
- [ ] Igra smart contract (Rust)
- [ ] Oracle integration (Band Protocol)
- [ ] Vault system (mint/burn/liquidation)
- [ ] Unit tests & integration tests
- [ ] Testnet deployment on Kaspa testnet
- [ ] Community review period

### Phase 3: Hardening (Q1 2027, Mar)
- [ ] Security audit (external firm)
- [ ] Academic peer review
- [ ] Bytecode verification
- [ ] Bug fixes & optimizations

### Phase 4: Beta (Q2 2027, Apr-May)
- [ ] Mainnet deployment (50-100M TVL cap)
- [ ] Monitor peg stability
- [ ] Liquidation testing
- [ ] Oracle feed quality testing
- [ ] Increase TVL cap gradually

### Phase 5: Production (Q2 2027, Jun+)
- [ ] Remove TVL cap
- [ ] Full ecosystem deployment
- [ ] Community governance (optional)
- [ ] Fork strategy documentation

---

## File Structure

```
ENRK_stablecoin/
├── README.md (✅ created)
├── PROJECT_MANIFEST.md (this file)
│
├── docs/
│   ├── design/
│   │   ├── Immutable-By-Design.md (✅)
│   │   ├── Deployment-Strategy.md (✅)
│   │   └── Architecture-Overview.md (TODO)
│   │
│   ├── specifications/
│   │   ├── Frozen-Parameters.md (✅)
│   │   ├── Token-Naming-ENRK.md (✅)
│   │   ├── Final-Recommendation.md (TODO: from cloud)
│   │   └── Technical-Specification-Igra.md (TODO: translate)
│   │
│   └── analysis/
│       ├── Auto-Equilibrium-Mechanism.md (✅)
│       ├── Hedging-Mechanism.md (TODO: from cloud)
│       ├── Backtesting-Results.md (TODO: translate)
│       └── Failed-Stablecoins-Analysis.md (TODO: translate)
│
├── contracts/igra/
│   ├── lib.rs (TODO)
│   ├── vault.rs (TODO)
│   ├── liquidation.rs (TODO)
│   ├── peg.rs (TODO)
│   └── tests/ (TODO)
│
├── tests/backtesting/
│   ├── ENRK_Backtest_Simple.py (TODO: import)
│   └── crisis_scenarios.py (TODO)
│
├── scripts/
│   ├── deploy_testnet.sh (TODO)
│   ├── deploy_mainnet.sh (TODO)
│   └── oracle_setup.sh (TODO)
│
└── research/
    ├── game_theory_analysis.md (TODO)
    ├── economic_models.md (TODO)
    └── risk_register.md (TODO)
```

---

## Key Decisions (Immutable)

### Token
- **Name**: ENRK (Kaspa Energy Reserve)
- **Speculative**: kFIAT (Kaspa Speculative Finance)
- **Supply**: Unlimited (minted on demand)
- **Peg**: 1 ENRK ≈ 1 kWh of energy

### Formula (FROZEN)
```
Peg(ENRK) = 0.40×Kaspa_Hashrate 
          + 0.30×Global_Energy 
          + 0.20×Kaspa_Fees 
          + 0.10×Crypto_Adoption
```

### Ratios (FROZEN)
- ICR: 200%
- MCR: 150%
- kFIAT Cap: 30%

### Liquidation (FROZEN)
- Dutch Auction: 120 min
- Price: 100% → 85%

### Fees (FROZEN)
- 80% → Stability Pool
- 20% → Treasury

### Oracle (HARDCODED FALLBACK)
- Primary: Band Protocol
- Fallback: Chainlink
- Emergency: Last known price + alert

---

## Next Steps (Immediate)

1. **Export docs from cloud** to local folder (preserving structure)
2. **Create Igra contract skeleton** (Rust, Kaspa)
3. **Set up testing framework** (unit tests)
4. **Define oracle integration** (Band Protocol specifics)
5. **Create deployment scripts** (testnet first)

---

## Project Principles

- ✅ **Immutable by design** (no governance after deployment)
- ✅ **Code is law** (parameters frozen in bytecode)
- ✅ **Forkable** (community can create v2 if needed)
- ✅ **No admin keys** (fully decentralized)
- ✅ **Self-regulating** (5 market mechanisms)
- ✅ **Energy-backed** (not USD/fiat dependent)
- ✅ **International** (all docs in English)

---

**Last Updated**: September 3, 2026
**Maintainer**: Community-driven
**Status**: Foundation Phase Complete → Implementation Phase Starting
