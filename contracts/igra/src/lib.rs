//! ENRK Igra - Immutable Energy-Backed Stablecoin on Kaspa
//!
//! Smart contract implementing the ENRK protocol:
//! - Over-collateralized CDP system (like Liquity)
//! - Dual-tranche: ENRK (senior, stable) + kFIAT (junior, speculative)
//! - Five self-regulating equilibrium mechanisms (no governance)
//! - Peg backed by thermodynamic energy cost, not fiat
//! - Immutable parameters frozen at compile-time
//!
//! Architecture:
//! - types: Core data structures
//! - errors: Error handling
//! - peg: Price calculation from 4 indices
//! - vault: CDP management
//! - liquidation: Dutch Auction mechanism
//! - stability_pool: Automatic buyback
//! - circuit_breaker: Emergency safeguard
//! - kaspa_adapter: Kaspa network integration
//! - oracle_feeds: Real-time peg index feeds
//! - kaspa_tokens: ENRK/kFIAT token ledgers

pub mod circuit_breaker;
pub mod errors;
pub mod kaspa_adapter;
pub mod kaspa_tokens;
pub mod liquidation;
pub mod oracle_feeds;
pub mod peg;
pub mod stability_pool;
pub mod types;
pub mod vault;

pub use circuit_breaker::{CircuitBreaker, CircuitBreakerState};
pub use errors::{IgraError, IgraResult};
pub use kaspa_adapter::{
    KaspaAddressValidator, KaspaPegIndexCalculator, KaspaNetworkState, KaspaTransactionBuilder,
};
pub use kaspa_tokens::{TokenLayer, TokenLedger, TokenSupplyStats, TokenType};
pub use liquidation::LiquidationManager;
pub use oracle_feeds::{
    AdoptionMetricFeed, EnergyPriceFeed, KaspaNetworkFeed, OracleFeedData, OracleFeedManager,
};
pub use peg::{OracleManager, PegCalculator};
pub use stability_pool::StabilityPoolManager;
pub use types::*;
pub use vault::VaultManager;

pub const ENRK_VERSION: &str = "1.0.0";

/// Frozen protocol parameters (immutable at compile-time)
pub mod frozen_params {
    // Peg formula weights (must sum to 100)
    pub const PEG_HASHRATE_WEIGHT: u8 = 40; // 40% Kaspa hashrate
    pub const PEG_ENERGY_WEIGHT: u8 = 30; // 30% Global energy price
    pub const PEG_FEES_WEIGHT: u8 = 20; // 20% Kaspa network fees
    pub const PEG_ADOPTION_WEIGHT: u8 = 10; // 10% Crypto adoption

    // Collateral ratio constraints
    pub const ICR_MINIMUM_PERCENT: u16 = 200; // 200% minimum
    pub const MCR_TRIGGER_PERCENT: u16 = 150; // 150% liquidation threshold

    // Debt tranche cap
    pub const KFIAT_MAX_PERCENT: u8 = 30; // 30% of total debt

    // Liquidation auction parameters
    pub const LIQUIDATION_DURATION_MINUTES: u16 = 120; // 2 hours
    pub const LIQUIDATION_START_PRICE: u8 = 100; // 100% of market price
    pub const LIQUIDATION_END_PRICE: u8 = 85; // 85% (15% incentive)

    // Fee distribution
    pub const STABILITY_POOL_ALLOCATION: u8 = 80; // 80% of fees
    pub const TREASURY_ALLOCATION: u8 = 20; // 20% of fees
    pub const MINT_FEE_BPS: u16 = 200; // 2.0%
    pub const LIQUIDATION_FEE_BPS: u16 = 400; // 4.0%
    pub const REDEMPTION_FEE_BPS: u16 = 100; // 1.0%

    // Circuit breaker thresholds
    pub const PEG_DEVIATION_THRESHOLD: u8 = 10; // 10% max deviation
    pub const ORACLE_DOWNTIME_THRESHOLD_MINUTES: u16 = 360; // 6 hours

    /// Verify all parameters are valid and consistent
    pub fn validate_all() -> super::IgraResult<()> {
        use super::errors::IgraError;

        // Check peg weights sum to 100
        if (PEG_HASHRATE_WEIGHT as u16
            + PEG_ENERGY_WEIGHT as u16
            + PEG_FEES_WEIGHT as u16
            + PEG_ADOPTION_WEIGHT as u16)
            != 100
        {
            return Err(IgraError::ConfigurationInvalid(
                "Peg weights must sum to 100".to_string(),
            ));
        }

        // Check fee allocation sums to 100
        if (STABILITY_POOL_ALLOCATION as u16 + TREASURY_ALLOCATION as u16) != 100 {
            return Err(IgraError::ConfigurationInvalid(
                "Fee allocation must sum to 100".to_string(),
            ));
        }

        // Check collateral ratios
        if ICR_MINIMUM_PERCENT <= MCR_TRIGGER_PERCENT {
            return Err(IgraError::ConfigurationInvalid(
                "ICR must be > MCR".to_string(),
            ));
        }

        // Check liquidation parameters
        if LIQUIDATION_START_PRICE <= LIQUIDATION_END_PRICE {
            return Err(IgraError::ConfigurationInvalid(
                "Liquidation start price must be > end price".to_string(),
            ));
        }

        Ok(())
    }
}

/// Initialize protocol with frozen parameters
/// Validates all compile-time constants are consistent
pub fn initialize() -> IgraResult<()> {
    frozen_params::validate_all()?;
    log::info!(
        "ENRK Igra v{} initialized with frozen parameters",
        ENRK_VERSION
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_frozen_params_valid() {
        assert!(frozen_params::validate_all().is_ok());
    }

    #[test]
    fn test_peg_weights_sum() {
        let sum = frozen_params::PEG_HASHRATE_WEIGHT
            + frozen_params::PEG_ENERGY_WEIGHT
            + frozen_params::PEG_FEES_WEIGHT
            + frozen_params::PEG_ADOPTION_WEIGHT;
        assert_eq!(sum, 100);
    }

    #[test]
    fn test_fee_allocation_sum() {
        let sum =
            frozen_params::STABILITY_POOL_ALLOCATION + frozen_params::TREASURY_ALLOCATION;
        assert_eq!(sum, 100);
    }

    #[test]
    fn test_collateral_ratios() {
        assert!(frozen_params::ICR_MINIMUM_PERCENT > frozen_params::MCR_TRIGGER_PERCENT);
    }

    #[test]
    fn test_liquidation_prices() {
        assert!(
            frozen_params::LIQUIDATION_START_PRICE > frozen_params::LIQUIDATION_END_PRICE
        );
    }

    #[test]
    fn test_initialization() {
        assert!(initialize().is_ok());
    }
}
