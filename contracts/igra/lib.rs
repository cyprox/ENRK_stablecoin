//! ENRK Igra - Immutable Energy-Backed Stablecoin on Kaspa
//!
//! This is the core implementation of ENRK (Kaspa Energy Reserve),
//! a decentralized stablecoin backed by proof-of-work energy.
//!
//! Key principles:
//! - Immutable by design (frozen parameters)
//! - No governance after deployment (code is law)
//! - Self-regulating via market mechanisms
//! - Forkable (community can create v2 if needed)

pub mod vault;
pub mod liquidation;
pub mod peg;
pub mod stability_pool;
pub mod circuit_breaker;
pub mod errors;
pub mod types;

pub use errors::IgraError;
pub use types::*;

/// ENRK Protocol Version
pub const ENRK_VERSION: &str = "1.0.0";

/// Frozen protocol parameters (immutable)
pub mod frozen_params {
    /// Peg formula weights (sum = 100)
    pub const PEG_HASHRATE_WEIGHT: u8 = 40;      // 40%
    pub const PEG_ENERGY_WEIGHT: u8 = 30;        // 30%
    pub const PEG_FEES_WEIGHT: u8 = 20;          // 20%
    pub const PEG_ADOPTION_WEIGHT: u8 = 10;      // 10%

    /// Collateral ratios (immutable)
    pub const ICR_MINIMUM_PERCENT: u16 = 200;    // 200% initial
    pub const MCR_TRIGGER_PERCENT: u16 = 150;    // 150% maintenance
    pub const KFIAT_MAX_PERCENT: u8 = 30;        // 30% of total debt

    /// Liquidation auction (immutable)
    pub const LIQUIDATION_DURATION_MINUTES: u16 = 120;
    pub const LIQUIDATION_START_PRICE: u8 = 100; // 100%
    pub const LIQUIDATION_END_PRICE: u8 = 85;    // 85%

    /// Fee distribution (immutable)
    pub const STABILITY_POOL_ALLOCATION: u8 = 80; // 80% to pool
    pub const TREASURY_ALLOCATION: u8 = 20;       // 20% to treasury

    /// Circuit breaker thresholds (immutable)
    pub const PEG_DEVIATION_THRESHOLD: u8 = 10;   // 10% max deviation
    pub const ORACLE_DOWNTIME_THRESHOLD_MINUTES: u16 = 360; // 6 hours
}

/// Initialize ENRK protocol
/// This function should be called once at deployment
pub fn initialize() -> Result<(), IgraError> {
    log::info!("Initializing ENRK Igra v{}", ENRK_VERSION);
    
    // Verify frozen parameters are immutable (compile-time constants)
    assert_eq!(
        frozen_params::PEG_HASHRATE_WEIGHT
            + frozen_params::PEG_ENERGY_WEIGHT
            + frozen_params::PEG_FEES_WEIGHT
            + frozen_params::PEG_ADOPTION_WEIGHT,
        100,
        "Peg weights must sum to 100"
    );

    log::info!("ENRK protocol initialized successfully");
    log::info!("Frozen parameters verified immutable");
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_peg_weights_sum() {
        let sum = frozen_params::PEG_HASHRATE_WEIGHT
            + frozen_params::PEG_ENERGY_WEIGHT
            + frozen_params::PEG_FEES_WEIGHT
            + frozen_params::PEG_ADOPTION_WEIGHT;
        assert_eq!(sum, 100);
    }

    #[test]
    fn test_initialization() {
        let result = initialize();
        assert!(result.is_ok());
    }

    #[test]
    fn test_frozen_params_immutable() {
        // These are compile-time constants, cannot be modified
        assert_eq!(frozen_params::ICR_MINIMUM_PERCENT, 200);
        assert_eq!(frozen_params::MCR_TRIGGER_PERCENT, 150);
        assert_eq!(frozen_params::KFIAT_MAX_PERCENT, 30);
    }
}
