//! Core data types for ENRK Igra stablecoin protocol

use serde::{Deserialize, Serialize};
use num_bigint::BigInt;
use num_traits::cast::ToPrimitive;

/// Immutable peg formula weights (frozen at deployment)
/// Sum = 100, representing:
/// - 40% Kaspa network hashrate
/// - 30% Global energy price index
/// - 20% Kaspa network fees
/// - 10% Global crypto adoption metric
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct PegWeights {
    pub hashrate: u8,     // 40
    pub energy: u8,       // 30
    pub fees: u8,         // 20
    pub adoption: u8,     // 10
}

impl PegWeights {
    pub fn validate(&self) -> Result<(), String> {
        if self.hashrate as u16 + self.energy as u16 + self.fees as u16 + self.adoption as u16
            != 100
        {
            return Err("Peg weights must sum to 100".to_string());
        }
        Ok(())
    }
}

impl Default for PegWeights {
    fn default() -> Self {
        Self {
            hashrate: 40,
            energy: 30,
            fees: 20,
            adoption: 10,
        }
    }
}

/// Collateral ratio constraints (frozen at deployment)
/// ICR: Individual Collateral Ratio (100% = 1.0x collateral per debt)
/// MCR: Minimum Collateral Ratio (below this, vault is liquidation-eligible)
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct CollateralRatios {
    pub icr_minimum: u16,  // 200 (200%)
    pub mcr_trigger: u16,  // 150 (150%)
}

impl CollateralRatios {
    pub fn validate(&self) -> Result<(), String> {
        if self.icr_minimum <= self.mcr_trigger {
            return Err("ICR must be greater than MCR".to_string());
        }
        if self.mcr_trigger < 100 {
            return Err("MCR must be at least 100%".to_string());
        }
        Ok(())
    }
}

impl Default for CollateralRatios {
    fn default() -> Self {
        Self {
            icr_minimum: 200,
            mcr_trigger: 150,
        }
    }
}

/// Liquidation auction parameters (frozen at deployment)
/// Duration: time for Dutch Auction price descent (in minutes)
/// Start/End: price percentages during auction
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct LiquidationParams {
    pub duration_minutes: u16,  // 120 minutes
    pub start_price: u8,        // 100% (full market price)
    pub end_price: u8,          // 85% (liquidation incentive discount)
}

impl LiquidationParams {
    pub fn validate(&self) -> Result<(), String> {
        if self.duration_minutes == 0 {
            return Err("Liquidation duration must be > 0".to_string());
        }
        if self.start_price <= self.end_price {
            return Err("Start price must be greater than end price".to_string());
        }
        if self.start_price > 100 {
            return Err("Start price cannot exceed 100%".to_string());
        }
        if self.end_price == 0 {
            return Err("End price must be > 0".to_string());
        }
        Ok(())
    }
}

impl Default for LiquidationParams {
    fn default() -> Self {
        Self {
            duration_minutes: 120,
            start_price: 100,
            end_price: 85,
        }
    }
}

/// Fee structure (frozen at deployment)
/// Mint/Burn/Liquidation fees
/// Distribution: % to Stability Pool vs Treasury
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct FeeStructure {
    pub mint_fee_bps: u16,         // basis points (1 = 0.01%)
    pub liquidation_fee_bps: u16,  // basis points
    pub redemption_fee_bps: u16,   // basis points
    pub stability_pool_allocation: u8,  // 80% to pool
    pub treasury_allocation: u8,        // 20% to treasury
}

impl FeeStructure {
    pub fn validate(&self) -> Result<(), String> {
        if self.stability_pool_allocation + self.treasury_allocation != 100 {
            return Err("Fee allocations must sum to 100%".to_string());
        }
        if self.mint_fee_bps > 10000 {
            return Err("Fee cannot exceed 100%".to_string());
        }
        Ok(())
    }
}

impl Default for FeeStructure {
    fn default() -> Self {
        Self {
            mint_fee_bps: 200,      // 2%
            liquidation_fee_bps: 400,  // 4%
            redemption_fee_bps: 100,   // 1%
            stability_pool_allocation: 80,
            treasury_allocation: 20,
        }
    }
}

/// Circuit breaker parameters (frozen at deployment)
/// Triggers automatic pause if peg deviates beyond threshold
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct CircuitBreakerParams {
    pub peg_deviation_threshold: u8,  // 10% max acceptable deviation
    pub oracle_downtime_threshold_minutes: u16,  // 360 (6 hours)
}

impl CircuitBreakerParams {
    pub fn validate(&self) -> Result<(), String> {
        if self.peg_deviation_threshold == 0 || self.peg_deviation_threshold > 50 {
            return Err("Peg deviation threshold must be 0 < x <= 50%".to_string());
        }
        if self.oracle_downtime_threshold_minutes == 0 {
            return Err("Oracle downtime threshold must be > 0".to_string());
        }
        Ok(())
    }
}

impl Default for CircuitBreakerParams {
    fn default() -> Self {
        Self {
            peg_deviation_threshold: 10,
            oracle_downtime_threshold_minutes: 360,
        }
    }
}

/// Current peg price from oracle feeds
/// All values normalized to 1 kWh = 1.0
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PegPrice {
    pub value: f64,           // e.g., 1.02 (2% above peg)
    pub timestamp_seconds: u64,
    pub components: PegComponents,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PegComponents {
    pub hashrate_index: f64,   // Kaspa hashrate trend
    pub energy_index: f64,     // Global energy price
    pub fees_index: f64,       // Kaspa network fees
    pub adoption_index: f64,   // Crypto adoption metric
}

/// Vault state: over-collateralized CDP holding KAS, minting ENRK
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Vault {
    pub vault_id: u64,
    pub owner: String,  // Kaspa address
    pub collateral_kas: BigInt,  // KAS held
    pub debt_enrk: BigInt,        // ENRK minted (senior tranche)
    pub debt_kfiat: BigInt,       // kFIAT minted (junior tranche)
    pub status: VaultStatus,
    pub created_at_seconds: u64,
    pub last_updated_seconds: u64,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum VaultStatus {
    Active,
    Liquidating,
    Closed,
}

impl Vault {
    /// Calculate Individual Collateral Ratio = collateral_value / total_debt
    /// Returns ratio as percentage (200 = 200%)
    pub fn calculate_icr(&self, kas_price: f64, enrk_price: f64, kfiat_price: f64) -> f64 {
        let collateral_value =
            self.collateral_kas.to_f64().unwrap_or(0.0) * kas_price;
        let debt_value = self.debt_enrk.to_f64().unwrap_or(0.0) * enrk_price
            + self.debt_kfiat.to_f64().unwrap_or(0.0) * kfiat_price;

        if debt_value == 0.0 {
            return f64::INFINITY;
        }
        (collateral_value / debt_value) * 100.0
    }

    /// Check if vault is under-collateralized (ICR < MCR)
    pub fn is_under_collateralized(&self, kas_price: f64, enrk_price: f64, kfiat_price: f64, mcr: u16) -> bool {
        self.calculate_icr(kas_price, enrk_price, kfiat_price) < mcr as f64
    }
}

/// Liquidation auction state: Dutch auction for vault collateral
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LiquidationAuction {
    pub auction_id: u64,
    pub vault_id: u64,
    pub collateral_kas: BigInt,
    pub debt_to_cover: BigInt,  // ENRK + kFIAT combined
    pub started_at_seconds: u64,
    pub duration_minutes: u16,
}

impl LiquidationAuction {
    /// Calculate current auction price as percentage
    /// Linearly descends from 100% to end_price over duration
    pub fn current_price_percent(&self, now_seconds: u64, end_price: u8) -> u8 {
        let elapsed = (now_seconds - self.started_at_seconds) / 60; // Convert to minutes
        let elapsed_percent = (elapsed as f64 / self.duration_minutes as f64) * 100.0;

        if elapsed_percent >= 100.0 {
            return end_price;
        }

        let start_price = 100u16;
        let price_range = (start_price - end_price as u16) as f64;
        let current = 100.0 - (elapsed_percent * price_range / 100.0);
        current.max(end_price as f64) as u8
    }

    /// Check if auction is expired
    pub fn is_expired(&self, now_seconds: u64) -> bool {
        ((now_seconds - self.started_at_seconds) / 60) >= self.duration_minutes as u64
    }
}

/// Stability Pool: holds ENRK to buy back during crashes
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StabilityPool {
    pub enrk_balance: BigInt,      // ENRK reserves for buyback
    pub cumulative_fees_collected: BigInt,
    pub last_buyback_seconds: u64,
}

/// Oracle price feed state
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct OraclePrice {
    pub value: f64,
    pub timestamp_seconds: u64,
    pub source: String,  // "band", "chainlink", "fallback"
}

/// Circuit breaker state: automatic pause trigger
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CircuitBreakerState {
    pub is_paused: bool,
    pub pause_triggered_at_seconds: u64,
    pub pause_reason: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_peg_weights_valid() {
        let weights = PegWeights::default();
        assert_eq!(weights.validate(), Ok(()));
    }

    #[test]
    fn test_peg_weights_invalid_sum() {
        let weights = PegWeights {
            hashrate: 50,
            energy: 30,
            fees: 20,
            adoption: 10,
        };
        assert!(weights.validate().is_err());
    }

    #[test]
    fn test_collateral_ratios_valid() {
        let ratios = CollateralRatios::default();
        assert_eq!(ratios.validate(), Ok(()));
    }

    #[test]
    fn test_collateral_ratios_invalid() {
        let ratios = CollateralRatios {
            icr_minimum: 150,
            mcr_trigger: 200,
        };
        assert!(ratios.validate().is_err());
    }

    #[test]
    fn test_liquidation_params_valid() {
        let params = LiquidationParams::default();
        assert_eq!(params.validate(), Ok(()));
    }

    #[test]
    fn test_fee_structure_valid() {
        let fees = FeeStructure::default();
        assert_eq!(fees.validate(), Ok(()));
    }

    #[test]
    fn test_circuit_breaker_valid() {
        let cb = CircuitBreakerParams::default();
        assert_eq!(cb.validate(), Ok(()));
    }

    #[test]
    fn test_vault_icr_calculation() {
        let vault = Vault {
            vault_id: 1,
            owner: "addr_test".to_string(),
            collateral_kas: BigInt::from(100),  // 100 KAS
            debt_enrk: BigInt::from(50),        // 50 ENRK
            debt_kfiat: BigInt::from(10),       // 10 kFIAT
            status: VaultStatus::Active,
            created_at_seconds: 0,
            last_updated_seconds: 0,
        };

        let kas_price = 5.0;  // $5 per KAS
        let enrk_price = 1.0; // $1 per ENRK (pegged to 1 kWh)
        let kfiat_price = 1.0;

        let icr = vault.calculate_icr(kas_price, enrk_price, kfiat_price);
        // (100 * 5.0) / (50 * 1.0 + 10 * 1.0) = 500 / 60 = 8.33 = 833%
        assert!((icr - 833.33).abs() < 1.0);
    }

    #[test]
    fn test_liquidation_auction_price_progression() {
        let auction = LiquidationAuction {
            auction_id: 1,
            vault_id: 1,
            collateral_kas: BigInt::from(100),
            debt_to_cover: BigInt::from(50),
            started_at_seconds: 1000,
            duration_minutes: 120,
        };

        // At start (1000s): should be 100%
        let price_start = auction.current_price_percent(1000, 85);
        assert_eq!(price_start, 100);

        // At 50% duration (60 minutes = 3600s): should be 92.5%
        let price_mid = auction.current_price_percent(1000 + 3600, 85);
        assert!(price_mid >= 92 && price_mid <= 93);

        // At end: should be 85%
        let price_end = auction.current_price_percent(1000 + 7200, 85);
        assert_eq!(price_end, 85);
    }

    #[test]
    fn test_liquidation_auction_expiry() {
        let auction = LiquidationAuction {
            auction_id: 1,
            vault_id: 1,
            collateral_kas: BigInt::from(100),
            debt_to_cover: BigInt::from(50),
            started_at_seconds: 1000,
            duration_minutes: 120,
        };

        // Before expiry
        assert!(!auction.is_expired(1000 + 6000)); // 100 minutes in

        // At expiry
        assert!(auction.is_expired(1000 + 7200)); // 120 minutes in
    }
}
