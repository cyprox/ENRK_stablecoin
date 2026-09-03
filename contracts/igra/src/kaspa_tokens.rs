//! Kaspa token layer for ENRK and kFIAT
//!
//! Implements the dual-tranche token system as actual balances:
//! - ENRK (senior tranche): unlimited supply, redeemable at peg
//! - kFIAT (junior tranche): capped at 30% of total debt, absorbs losses first
//!
//! # The 30% kFIAT cap is a MINT-TIME ceiling, not a permanent guarantee
//!
//! The cap is a ratio, so it can be breached without minting any kFIAT at all —
//! by shrinking the denominator. Burning ENRK does exactly that, and ENRK burns
//! are core protocol paths: debt repayment, redemption at peg, and Stability Pool
//! buyback (equilibrium mechanism #3). Concretely:
//!
//!   E=700, K=300  -> 300/1000 = 30%  (at cap)
//!   burn 600 ENRK -> 300/400  = 75%  (far above cap)
//!
//! So the harder the protocol defends the peg by burning ENRK, the higher the
//! junior tranche's systemwide share climbs. Peg defense and the cap pull against
//! each other, and peg defense must win.
//!
//! This module does not paper over that. When the ratio is above the cap:
//! - `mint_kfiat` refuses, and `max_mintable_kfiat()` returns zero
//! - `verify_invariants()` REPORTS the breach as `StateInconsistency`
//!
//! The rejected alternatives, for the record: blocking ENRK repayment would break
//! the redemption arbitrage that defends the peg, and force-liquidating kFIAT to
//! restore the ratio reintroduces exactly the discretionary human action the
//! protocol's immutability principle exists to eliminate.
//!
//! A rising junior ratio is precisely the condition under which kFIAT should trade
//! at a discount. Letting the market price that is the decentralized response.
//! Documentation must therefore say "<= 30% at mint", never "always <= 30%".
//!
//! Design principles:
//! - Integer-only arithmetic (BigInt) for all supply and balance math.
//!   No f64 anywhere in this module: a rounding error in a token ledger is a
//!   solvency error, and the kFIAT cap is a hard invariant, not an estimate.
//! - The cap is enforced at the SUPPLY level, not just per-vault. A vault-level
//!   check alone can be defeated by spreading kFIAT debt across many vaults.
//! - Zero balances are pruned from the ledger so the holder map cannot be
//!   inflated indefinitely by dust-and-burn cycles.
//! - Every mutation is checked-then-applied, so a rejected operation leaves
//!   the ledger byte-for-byte unchanged.
//!
//! All amounts use 8 decimals, matching Kaspa's sompiā convention.

use crate::errors::{IgraError, IgraResult};
use crate::kaspa_adapter::KaspaAddressValidator;
use log::{info, warn};
use num_bigint::BigInt;
use num_traits::cast::ToPrimitive;
use num_traits::Zero;
use std::collections::HashMap;
use std::fmt;

/// Decimal precision for both tokens (matches Kaspa sompiā)
pub const TOKEN_DECIMALS: u8 = 8;

/// ENRK token symbol (senior tranche)
pub const ENRK_SYMBOL: &str = "ENRK";

/// kFIAT token symbol (junior tranche)
pub const KFIAT_SYMBOL: &str = "kFIAT";

/// Which tranche a balance belongs to
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum TokenType {
    /// Senior tranche: pegged, redeemable, unlimited supply
    Enrk,
    /// Junior tranche: unpegged, loss-absorbing, capped supply
    Kfiat,
}

impl TokenType {
    pub fn symbol(&self) -> &'static str {
        match self {
            TokenType::Enrk => ENRK_SYMBOL,
            TokenType::Kfiat => KFIAT_SYMBOL,
        }
    }
}

impl fmt::Display for TokenType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.symbol())
    }
}

/// Supply and holder snapshot for monitoring
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TokenSupplyStats {
    pub enrk_supply: BigInt,
    pub kfiat_supply: BigInt,
    pub total_debt: BigInt,
    /// kFIAT as a percentage of total debt (integer, floor)
    pub kfiat_ratio_percent: u8,
    pub kfiat_cap_percent: u8,
    pub enrk_holders: usize,
    pub kfiat_holders: usize,
}

/// A single-token ledger: supply plus per-address balances
#[derive(Debug, Clone)]
pub struct TokenLedger {
    token_type: TokenType,
    decimals: u8,
    total_supply: BigInt,
    balances: HashMap<String, BigInt>,
}

impl TokenLedger {
    /// Create an empty ledger for the given tranche
    pub fn new(token_type: TokenType) -> Self {
        Self {
            token_type,
            decimals: TOKEN_DECIMALS,
            total_supply: BigInt::zero(),
            balances: HashMap::new(),
        }
    }

    /// Validate an address is a well-formed Kaspa address
    fn require_valid_address(address: &str) -> IgraResult<()> {
        if !KaspaAddressValidator::is_valid_address(address) {
            return Err(IgraError::InvalidAddress(address.to_string()));
        }
        Ok(())
    }

    /// Validate an amount is strictly positive
    fn require_positive(amount: &BigInt) -> IgraResult<()> {
        if amount <= &BigInt::zero() {
            return Err(IgraError::InvalidDebtAmount);
        }
        Ok(())
    }

    /// Mint new tokens to an address, increasing total supply.
    /// Returns the recipient's new balance.
    pub fn mint(&mut self, to: &str, amount: &BigInt) -> IgraResult<BigInt> {
        Self::require_valid_address(to)?;
        Self::require_positive(amount)?;

        self.total_supply += amount;
        let entry = self.balances.entry(to.to_string()).or_insert_with(BigInt::zero);
        *entry += amount;
        let new_balance = entry.clone();

        info!(
            "{} minted: {} to {} (supply now {})",
            self.token_type, amount, to, self.total_supply
        );

        Ok(new_balance)
    }

    /// Burn tokens from an address, decreasing total supply.
    /// Returns the holder's remaining balance.
    pub fn burn(&mut self, from: &str, amount: &BigInt) -> IgraResult<BigInt> {
        Self::require_valid_address(from)?;
        Self::require_positive(amount)?;

        let available = self.balance_of(from);
        if available < *amount {
            return Err(IgraError::InsufficientBalance {
                required: amount.to_u64().unwrap_or(u64::MAX),
                available: available.to_u64().unwrap_or(0),
            });
        }

        // Supply must always cover any burnable balance. If it does not, the
        // ledger is corrupt and we refuse rather than silently underflow.
        if self.total_supply < *amount {
            return Err(IgraError::StateInconsistency(format!(
                "{} supply {} is less than burn amount {}",
                self.token_type, self.total_supply, amount
            )));
        }

        let remaining = available - amount;
        self.total_supply -= amount;

        if remaining.is_zero() {
            self.balances.remove(from);
        } else {
            self.balances.insert(from.to_string(), remaining.clone());
        }

        info!(
            "{} burned: {} from {} (supply now {})",
            self.token_type, amount, from, self.total_supply
        );

        Ok(remaining)
    }

    /// Transfer tokens between addresses. Total supply is unchanged.
    pub fn transfer(&mut self, from: &str, to: &str, amount: &BigInt) -> IgraResult<()> {
        Self::require_valid_address(from)?;
        Self::require_valid_address(to)?;
        Self::require_positive(amount)?;

        if from == to {
            return Err(IgraError::InvalidParameters(
                "Cannot transfer to the same address".to_string(),
            ));
        }

        let available = self.balance_of(from);
        if available < *amount {
            return Err(IgraError::InsufficientBalance {
                required: amount.to_u64().unwrap_or(u64::MAX),
                available: available.to_u64().unwrap_or(0),
            });
        }

        let remaining = available - amount;
        if remaining.is_zero() {
            self.balances.remove(from);
        } else {
            self.balances.insert(from.to_string(), remaining);
        }

        let credited = self.balances.entry(to.to_string()).or_insert_with(BigInt::zero);
        *credited += amount;

        info!("{} transfer: {} from {} to {}", self.token_type, amount, from, to);

        Ok(())
    }

    /// Balance of an address (zero if it holds none)
    pub fn balance_of(&self, address: &str) -> BigInt {
        self.balances.get(address).cloned().unwrap_or_else(BigInt::zero)
    }

    pub fn total_supply(&self) -> &BigInt {
        &self.total_supply
    }

    pub fn token_type(&self) -> TokenType {
        self.token_type
    }

    pub fn decimals(&self) -> u8 {
        self.decimals
    }

    /// Number of addresses holding a non-zero balance
    pub fn holder_count(&self) -> usize {
        self.balances.len()
    }

    /// Sum of all balances. Must always equal total_supply.
    pub fn sum_of_balances(&self) -> BigInt {
        self.balances.values().fold(BigInt::zero(), |acc, b| acc + b)
    }

    /// Verify the ledger's core invariant: supply == sum of balances
    pub fn verify_invariant(&self) -> IgraResult<()> {
        let sum = self.sum_of_balances();
        if sum != self.total_supply {
            return Err(IgraError::StateInconsistency(format!(
                "{} supply {} != sum of balances {}",
                self.token_type, self.total_supply, sum
            )));
        }
        Ok(())
    }
}

/// Unified token layer holding both tranches and enforcing the kFIAT cap
pub struct TokenLayer {
    enrk: TokenLedger,
    kfiat: TokenLedger,
    kfiat_cap_percent: u8,
}

impl TokenLayer {
    /// Create the token layer with a frozen kFIAT cap (protocol default: 30)
    pub fn new(kfiat_cap_percent: u8) -> IgraResult<Self> {
        if kfiat_cap_percent == 0 || kfiat_cap_percent >= 100 {
            return Err(IgraError::InvalidParameters(format!(
                "kFIAT cap must be 0 < cap < 100, got {}",
                kfiat_cap_percent
            )));
        }

        info!("TokenLayer initialized: kFIAT cap = {}%", kfiat_cap_percent);

        Ok(Self {
            enrk: TokenLedger::new(TokenType::Enrk),
            kfiat: TokenLedger::new(TokenType::Kfiat),
            kfiat_cap_percent,
        })
    }

    /// Mint ENRK. Unlimited supply: the senior tranche is always mintable
    /// against sufficient collateral, which the vault layer enforces.
    pub fn mint_enrk(&mut self, to: &str, amount: &BigInt) -> IgraResult<BigInt> {
        self.enrk.mint(to, amount)
    }

    /// Mint kFIAT, enforcing the supply-level cap.
    ///
    /// Invariant, in exact integer arithmetic:
    ///   100 * (kfiat + amount) <= cap * (enrk + kfiat + amount)
    ///
    /// Note this rejects any kFIAT mint while ENRK supply is zero: the junior
    /// tranche cannot exist without a senior tranche to be junior to.
    pub fn mint_kfiat(&mut self, to: &str, amount: &BigInt) -> IgraResult<BigInt> {
        if amount <= &BigInt::zero() {
            return Err(IgraError::InvalidDebtAmount);
        }

        let prospective_kfiat = self.kfiat.total_supply() + amount;
        let prospective_total = self.enrk.total_supply() + &prospective_kfiat;

        let lhs = BigInt::from(100u8) * &prospective_kfiat;
        let rhs = BigInt::from(self.kfiat_cap_percent) * &prospective_total;

        if lhs > rhs {
            let resulting_percent = Self::ratio_percent(&prospective_kfiat, &prospective_total);
            warn!(
                "kFIAT mint rejected: would reach {}% of debt (cap {}%)",
                resulting_percent, self.kfiat_cap_percent
            );
            return Err(IgraError::KFIATCapExceeded {
                current_kfiat: resulting_percent as u64,
                max_kfiat: self.kfiat_cap_percent as u64,
            });
        }

        self.kfiat.mint(to, amount)
    }

    /// Burn ENRK (repaying senior debt)
    pub fn burn_enrk(&mut self, from: &str, amount: &BigInt) -> IgraResult<BigInt> {
        self.enrk.burn(from, amount)
    }

    /// Burn kFIAT (repaying junior debt). Always permitted: burning kFIAT
    /// lowers the junior ratio, so it can never breach the cap.
    pub fn burn_kfiat(&mut self, from: &str, amount: &BigInt) -> IgraResult<BigInt> {
        self.kfiat.burn(from, amount)
    }

    pub fn transfer_enrk(&mut self, from: &str, to: &str, amount: &BigInt) -> IgraResult<()> {
        self.enrk.transfer(from, to, amount)
    }

    pub fn transfer_kfiat(&mut self, from: &str, to: &str, amount: &BigInt) -> IgraResult<()> {
        self.kfiat.transfer(from, to, amount)
    }

    /// Balance of an address in the given tranche
    pub fn balance_of(&self, address: &str, token_type: TokenType) -> BigInt {
        match token_type {
            TokenType::Enrk => self.enrk.balance_of(address),
            TokenType::Kfiat => self.kfiat.balance_of(address),
        }
    }

    /// Total protocol debt across both tranches
    pub fn total_debt(&self) -> BigInt {
        self.enrk.total_supply() + self.kfiat.total_supply()
    }

    /// kFIAT share of total debt as an integer percentage (floor)
    pub fn kfiat_ratio_percent(&self) -> u8 {
        Self::ratio_percent(self.kfiat.total_supply(), &self.total_debt())
    }

    /// Largest kFIAT amount that can still be minted without breaching the cap.
    ///
    /// Solving 100*(K+A) <= cap*(E+K+A) for A:
    ///   A <= (cap*(E+K) - 100*K) / (100 - cap)
    pub fn max_mintable_kfiat(&self) -> BigInt {
        let cap = BigInt::from(self.kfiat_cap_percent);
        let hundred = BigInt::from(100u8);
        let k = self.kfiat.total_supply().clone();
        let total = self.total_debt();

        let numerator = &cap * &total - &hundred * &k;
        if numerator <= BigInt::zero() {
            return BigInt::zero();
        }

        let denominator = &hundred - &cap;
        numerator / denominator
    }

    /// Whether minting `amount` of kFIAT would breach the cap
    pub fn would_exceed_kfiat_cap(&self, amount: &BigInt) -> bool {
        if amount <= &BigInt::zero() {
            return false;
        }
        let prospective_kfiat = self.kfiat.total_supply() + amount;
        let prospective_total = self.enrk.total_supply() + &prospective_kfiat;
        BigInt::from(100u8) * &prospective_kfiat
            > BigInt::from(self.kfiat_cap_percent) * &prospective_total
    }

    /// Supply and holder snapshot
    pub fn supply_stats(&self) -> TokenSupplyStats {
        TokenSupplyStats {
            enrk_supply: self.enrk.total_supply().clone(),
            kfiat_supply: self.kfiat.total_supply().clone(),
            total_debt: self.total_debt(),
            kfiat_ratio_percent: self.kfiat_ratio_percent(),
            kfiat_cap_percent: self.kfiat_cap_percent,
            enrk_holders: self.enrk.holder_count(),
            kfiat_holders: self.kfiat.holder_count(),
        }
    }

    /// Verify both ledgers and the cap invariant hold
    pub fn verify_invariants(&self) -> IgraResult<()> {
        self.enrk.verify_invariant()?;
        self.kfiat.verify_invariant()?;

        let total = self.total_debt();
        if !total.is_zero() {
            let lhs = BigInt::from(100u8) * self.kfiat.total_supply();
            let rhs = BigInt::from(self.kfiat_cap_percent) * &total;
            if lhs > rhs {
                return Err(IgraError::StateInconsistency(format!(
                    "kFIAT ratio {}% exceeds cap {}%",
                    self.kfiat_ratio_percent(),
                    self.kfiat_cap_percent
                )));
            }
        }

        Ok(())
    }

    pub fn kfiat_cap_percent(&self) -> u8 {
        self.kfiat_cap_percent
    }

    pub fn enrk_ledger(&self) -> &TokenLedger {
        &self.enrk
    }

    pub fn kfiat_ledger(&self) -> &TokenLedger {
        &self.kfiat
    }

    /// Integer percentage of `part` within `whole` (floor); zero when whole is zero
    fn ratio_percent(part: &BigInt, whole: &BigInt) -> u8 {
        if whole.is_zero() {
            return 0;
        }
        let pct = (BigInt::from(100u8) * part) / whole;
        pct.to_u8().unwrap_or(100)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const ALICE: &str = "kaspa:alice_address";
    const BOB: &str = "kaspa:bob_address";
    const TESTNET_CAROL: &str = "kaspatest:carol_address";

    fn layer() -> TokenLayer {
        TokenLayer::new(30).unwrap()
    }

    // ===== Ledger basics =====

    #[test]
    fn test_ledger_starts_empty() {
        let ledger = TokenLedger::new(TokenType::Enrk);
        assert!(ledger.total_supply().is_zero());
        assert_eq!(ledger.holder_count(), 0);
        assert_eq!(ledger.decimals(), TOKEN_DECIMALS);
        assert_eq!(ledger.token_type(), TokenType::Enrk);
    }

    #[test]
    fn test_mint_increases_supply_and_balance() {
        let mut ledger = TokenLedger::new(TokenType::Enrk);
        let balance = ledger.mint(ALICE, &BigInt::from(100)).unwrap();

        assert_eq!(balance, BigInt::from(100));
        assert_eq!(*ledger.total_supply(), BigInt::from(100));
        assert_eq!(ledger.balance_of(ALICE), BigInt::from(100));
        assert_eq!(ledger.holder_count(), 1);
        assert!(ledger.verify_invariant().is_ok());
    }

    #[test]
    fn test_mint_rejects_invalid_address_and_amount() {
        let mut ledger = TokenLedger::new(TokenType::Enrk);

        let bad_addr = ledger.mint("not_a_kaspa_address", &BigInt::from(100));
        assert!(matches!(bad_addr, Err(IgraError::InvalidAddress(_))));

        let zero = ledger.mint(ALICE, &BigInt::from(0));
        assert_eq!(zero, Err(IgraError::InvalidDebtAmount));

        let negative = ledger.mint(ALICE, &BigInt::from(-50));
        assert_eq!(negative, Err(IgraError::InvalidDebtAmount));

        // Nothing was applied
        assert!(ledger.total_supply().is_zero());
        assert_eq!(ledger.holder_count(), 0);
    }

    #[test]
    fn test_mint_accepts_testnet_address() {
        let mut ledger = TokenLedger::new(TokenType::Enrk);
        assert!(ledger.mint(TESTNET_CAROL, &BigInt::from(10)).is_ok());
        assert_eq!(ledger.balance_of(TESTNET_CAROL), BigInt::from(10));
    }

    #[test]
    fn test_burn_reduces_supply_and_prunes_zero_balance() {
        let mut ledger = TokenLedger::new(TokenType::Enrk);
        ledger.mint(ALICE, &BigInt::from(100)).unwrap();

        let remaining = ledger.burn(ALICE, &BigInt::from(40)).unwrap();
        assert_eq!(remaining, BigInt::from(60));
        assert_eq!(*ledger.total_supply(), BigInt::from(60));
        assert_eq!(ledger.holder_count(), 1);

        // Burning the rest removes the holder entry entirely
        let remaining = ledger.burn(ALICE, &BigInt::from(60)).unwrap();
        assert!(remaining.is_zero());
        assert!(ledger.total_supply().is_zero());
        assert_eq!(ledger.holder_count(), 0);
        assert!(ledger.verify_invariant().is_ok());
    }

    #[test]
    fn test_burn_rejects_insufficient_balance() {
        let mut ledger = TokenLedger::new(TokenType::Enrk);
        ledger.mint(ALICE, &BigInt::from(50)).unwrap();

        let result = ledger.burn(ALICE, &BigInt::from(80));
        assert!(matches!(
            result,
            Err(IgraError::InsufficientBalance { required: 80, available: 50 })
        ));

        // Rejected burn left the ledger untouched
        assert_eq!(*ledger.total_supply(), BigInt::from(50));
        assert_eq!(ledger.balance_of(ALICE), BigInt::from(50));
    }

    #[test]
    fn test_transfer_moves_balance_without_changing_supply() {
        let mut ledger = TokenLedger::new(TokenType::Enrk);
        ledger.mint(ALICE, &BigInt::from(100)).unwrap();

        ledger.transfer(ALICE, BOB, &BigInt::from(30)).unwrap();

        assert_eq!(ledger.balance_of(ALICE), BigInt::from(70));
        assert_eq!(ledger.balance_of(BOB), BigInt::from(30));
        assert_eq!(*ledger.total_supply(), BigInt::from(100));
        assert_eq!(ledger.holder_count(), 2);
        assert!(ledger.verify_invariant().is_ok());
    }

    #[test]
    fn test_transfer_rejects_self_and_overdraft() {
        let mut ledger = TokenLedger::new(TokenType::Enrk);
        ledger.mint(ALICE, &BigInt::from(100)).unwrap();

        let self_send = ledger.transfer(ALICE, ALICE, &BigInt::from(10));
        assert!(matches!(self_send, Err(IgraError::InvalidParameters(_))));

        let overdraft = ledger.transfer(ALICE, BOB, &BigInt::from(500));
        assert!(matches!(overdraft, Err(IgraError::InsufficientBalance { .. })));

        assert_eq!(ledger.balance_of(ALICE), BigInt::from(100));
        assert!(ledger.balance_of(BOB).is_zero());
    }

    #[test]
    fn test_transfer_full_balance_prunes_sender() {
        let mut ledger = TokenLedger::new(TokenType::Kfiat);
        ledger.mint(ALICE, &BigInt::from(25)).unwrap();

        ledger.transfer(ALICE, BOB, &BigInt::from(25)).unwrap();

        assert!(ledger.balance_of(ALICE).is_zero());
        assert_eq!(ledger.balance_of(BOB), BigInt::from(25));
        assert_eq!(ledger.holder_count(), 1);
        assert!(ledger.verify_invariant().is_ok());
    }

    // ===== TokenLayer construction =====

    #[test]
    fn test_token_layer_rejects_invalid_cap() {
        assert!(TokenLayer::new(0).is_err());
        assert!(TokenLayer::new(100).is_err());
        assert!(TokenLayer::new(30).is_ok());
    }

    #[test]
    fn test_token_type_symbols() {
        assert_eq!(TokenType::Enrk.symbol(), "ENRK");
        assert_eq!(TokenType::Kfiat.symbol(), "kFIAT");
        assert_eq!(TokenType::Kfiat.to_string(), "kFIAT");
    }

    // ===== kFIAT cap enforcement =====

    #[test]
    fn test_kfiat_cannot_be_minted_without_enrk() {
        let mut layer = layer();

        // No senior tranche exists yet: any kFIAT would be 100% of debt
        let result = layer.mint_kfiat(ALICE, &BigInt::from(1));
        assert!(matches!(result, Err(IgraError::KFIATCapExceeded { .. })));
        assert!(layer.kfiat_ledger().total_supply().is_zero());
    }

    #[test]
    fn test_kfiat_mint_within_cap() {
        let mut layer = layer();
        layer.mint_enrk(ALICE, &BigInt::from(700)).unwrap();

        // 300 kFIAT against 700 ENRK = 300/1000 = exactly 30%
        let balance = layer.mint_kfiat(ALICE, &BigInt::from(300)).unwrap();

        assert_eq!(balance, BigInt::from(300));
        assert_eq!(layer.kfiat_ratio_percent(), 30);
        assert_eq!(layer.total_debt(), BigInt::from(1000));
        assert!(layer.verify_invariants().is_ok());
    }

    #[test]
    fn test_kfiat_mint_at_cap_boundary_is_rejected_one_over() {
        let mut layer = layer();
        layer.mint_enrk(ALICE, &BigInt::from(700)).unwrap();

        // 301 would be 301/1001 = 30.07% > 30%
        let result = layer.mint_kfiat(ALICE, &BigInt::from(301));
        assert!(matches!(result, Err(IgraError::KFIATCapExceeded { .. })));

        // Ledger unchanged by the rejection
        assert!(layer.kfiat_ledger().total_supply().is_zero());
        assert_eq!(layer.kfiat_ratio_percent(), 0);
    }

    #[test]
    fn test_kfiat_cap_holds_across_many_small_mints() {
        let mut layer = layer();
        layer.mint_enrk(ALICE, &BigInt::from(700)).unwrap();

        // Drip-feed kFIAT: the cap is a supply invariant, so spreading the
        // mints out must not let total kFIAT past 30%.
        let mut minted = BigInt::zero();
        for _ in 0..100 {
            if layer.mint_kfiat(BOB, &BigInt::from(10)).is_ok() {
                minted += BigInt::from(10);
            }
        }

        assert_eq!(minted, BigInt::from(300));
        assert_eq!(*layer.kfiat_ledger().total_supply(), BigInt::from(300));
        assert!(layer.kfiat_ratio_percent() <= 30);
        assert!(layer.verify_invariants().is_ok());
    }

    #[test]
    fn test_max_mintable_kfiat() {
        let mut layer = layer();
        layer.mint_enrk(ALICE, &BigInt::from(700)).unwrap();

        // cap*(E+K) - 100*K over (100-cap) = (30*700 - 0)/70 = 300
        assert_eq!(layer.max_mintable_kfiat(), BigInt::from(300));

        layer.mint_kfiat(ALICE, &BigInt::from(300)).unwrap();

        // At the cap exactly: nothing more is mintable
        assert_eq!(layer.max_mintable_kfiat(), BigInt::zero());
        assert!(layer.would_exceed_kfiat_cap(&BigInt::from(1)));
    }

    #[test]
    fn test_minting_enrk_reopens_kfiat_headroom() {
        let mut layer = layer();
        layer.mint_enrk(ALICE, &BigInt::from(700)).unwrap();
        layer.mint_kfiat(ALICE, &BigInt::from(300)).unwrap();

        assert!(layer.would_exceed_kfiat_cap(&BigInt::from(1)));

        // More senior debt raises the denominator, so junior headroom returns
        layer.mint_enrk(BOB, &BigInt::from(700)).unwrap();

        assert_eq!(layer.max_mintable_kfiat(), BigInt::from(300));
        assert!(layer.mint_kfiat(BOB, &BigInt::from(300)).is_ok());
        assert_eq!(layer.kfiat_ratio_percent(), 30);
    }

    #[test]
    fn test_burning_kfiat_is_always_allowed_and_lowers_ratio() {
        let mut layer = layer();
        layer.mint_enrk(ALICE, &BigInt::from(700)).unwrap();
        layer.mint_kfiat(ALICE, &BigInt::from(300)).unwrap();
        assert_eq!(layer.kfiat_ratio_percent(), 30);

        layer.burn_kfiat(ALICE, &BigInt::from(200)).unwrap();

        // 100 kFIAT against 700 ENRK = 100/800 = 12%
        assert_eq!(layer.kfiat_ratio_percent(), 12);
        assert!(layer.verify_invariants().is_ok());
    }

    #[test]
    fn test_burning_enrk_can_leave_ratio_above_cap() {
        let mut layer = layer();
        layer.mint_enrk(ALICE, &BigInt::from(700)).unwrap();
        layer.mint_kfiat(BOB, &BigInt::from(300)).unwrap();

        // Repaying senior debt shrinks the denominator. This is legitimate —
        // an ENRK holder may always repay — but it pushes the junior ratio up,
        // so the cap must block new kFIAT rather than pretend nothing changed.
        layer.burn_enrk(ALICE, &BigInt::from(600)).unwrap();

        // 300/400 = 75%, well above the 30% cap
        assert_eq!(layer.kfiat_ratio_percent(), 75);
        assert_eq!(layer.max_mintable_kfiat(), BigInt::zero());
        assert!(layer.would_exceed_kfiat_cap(&BigInt::from(1)));
        assert!(layer.mint_kfiat(BOB, &BigInt::from(1)).is_err());

        // verify_invariants reports the breach rather than hiding it
        assert!(matches!(
            layer.verify_invariants(),
            Err(IgraError::StateInconsistency(_))
        ));
    }

    // ===== Cross-tranche behaviour =====

    #[test]
    fn test_tranches_have_independent_balances() {
        let mut layer = layer();
        layer.mint_enrk(ALICE, &BigInt::from(1000)).unwrap();
        layer.mint_kfiat(ALICE, &BigInt::from(100)).unwrap();

        assert_eq!(layer.balance_of(ALICE, TokenType::Enrk), BigInt::from(1000));
        assert_eq!(layer.balance_of(ALICE, TokenType::Kfiat), BigInt::from(100));

        // Burning one tranche does not touch the other
        layer.burn_kfiat(ALICE, &BigInt::from(100)).unwrap();
        assert_eq!(layer.balance_of(ALICE, TokenType::Enrk), BigInt::from(1000));
        assert!(layer.balance_of(ALICE, TokenType::Kfiat).is_zero());
    }

    #[test]
    fn test_transfers_do_not_change_supply_or_ratio() {
        let mut layer = layer();
        layer.mint_enrk(ALICE, &BigInt::from(700)).unwrap();
        layer.mint_kfiat(ALICE, &BigInt::from(300)).unwrap();

        let before = layer.supply_stats();

        layer.transfer_enrk(ALICE, BOB, &BigInt::from(350)).unwrap();
        layer.transfer_kfiat(ALICE, BOB, &BigInt::from(150)).unwrap();

        let after = layer.supply_stats();

        assert_eq!(before.enrk_supply, after.enrk_supply);
        assert_eq!(before.kfiat_supply, after.kfiat_supply);
        assert_eq!(before.kfiat_ratio_percent, after.kfiat_ratio_percent);
        assert_eq!(after.enrk_holders, 2);
        assert_eq!(after.kfiat_holders, 2);
        assert!(layer.verify_invariants().is_ok());
    }

    #[test]
    fn test_supply_stats_snapshot() {
        let mut layer = layer();
        layer.mint_enrk(ALICE, &BigInt::from(900)).unwrap();
        layer.mint_kfiat(BOB, &BigInt::from(100)).unwrap();

        let stats = layer.supply_stats();

        assert_eq!(stats.enrk_supply, BigInt::from(900));
        assert_eq!(stats.kfiat_supply, BigInt::from(100));
        assert_eq!(stats.total_debt, BigInt::from(1000));
        assert_eq!(stats.kfiat_ratio_percent, 10);
        assert_eq!(stats.kfiat_cap_percent, 30);
        assert_eq!(stats.enrk_holders, 1);
        assert_eq!(stats.kfiat_holders, 1);
    }

    #[test]
    fn test_empty_layer_stats_and_invariants() {
        let layer = layer();
        let stats = layer.supply_stats();

        assert!(stats.total_debt.is_zero());
        assert_eq!(stats.kfiat_ratio_percent, 0);
        assert_eq!(layer.max_mintable_kfiat(), BigInt::zero());
        assert!(!layer.would_exceed_kfiat_cap(&BigInt::zero()));
        assert!(layer.verify_invariants().is_ok());
    }

    #[test]
    fn test_large_amounts_use_exact_integer_math() {
        let mut layer = layer();

        // 10 million ENRK at 8 decimals, far beyond u64 sompiā precision games
        let big_enrk = BigInt::from(10_000_000u64) * BigInt::from(100_000_000u64);
        layer.mint_enrk(ALICE, &big_enrk).unwrap();

        let headroom = layer.max_mintable_kfiat();
        // 30*E/70 with E = 1e15 → 428571428571428 (floor), exact integer math
        assert_eq!(
            headroom,
            (BigInt::from(30u8) * &big_enrk) / BigInt::from(70u8)
        );

        layer.mint_kfiat(BOB, &headroom).unwrap();
        assert!(layer.kfiat_ratio_percent() <= 30);
        assert!(layer.verify_invariants().is_ok());
    }
}
