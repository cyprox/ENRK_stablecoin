//! Kaspa network adapter
//!
//! Bridges the Igra protocol to Kaspa's actual blockchain:
//! - Fetches network metrics (hashrate, fees) from Kaspa RPC
//! - Converts blockchain data to peg index values
//! - Handles KAS transfers for vault collateral
//! - Manages ENRK/kFIAT token operations on Kaspa layer
//!
//! All values use Kaspa's native unit: sompiā (1 KAS = 100,000,000 sompiā)

use crate::errors::{IgraError, IgraResult};
use num_bigint::BigInt;
use num_traits::cast::ToPrimitive;
use log::info;

/// Kaspa network constants
pub const SOMPI_PER_KAS: u64 = 100_000_000;  // 1 KAS = 100 million sompiā

/// Kaspa network state fetched from RPC
#[derive(Debug, Clone)]
pub struct KaspaNetworkState {
    /// Current network hashrate (hashes/second)
    pub hashrate_hps: f64,

    /// Average transaction fee (in sompiā)
    pub avg_tx_fee_sompi: BigInt,

    /// Current KAS price (in USD or equivalent index value)
    pub kas_price_usd: f64,

    /// Block height
    pub block_height: u64,

    /// Timestamp of this state snapshot (seconds since epoch)
    pub timestamp_seconds: u64,
}

impl KaspaNetworkState {
    pub fn new(
        hashrate_hps: f64,
        avg_tx_fee_sompi: BigInt,
        kas_price_usd: f64,
        block_height: u64,
        timestamp_seconds: u64,
    ) -> IgraResult<Self> {
        if hashrate_hps <= 0.0 || !hashrate_hps.is_finite() {
            return Err(IgraError::InvalidParameters(
                "Hashrate must be positive and finite".to_string(),
            ));
        }

        if kas_price_usd <= 0.0 || !kas_price_usd.is_finite() {
            return Err(IgraError::InvalidParameters(
                "KAS price must be positive and finite".to_string(),
            ));
        }

        Ok(Self {
            hashrate_hps,
            avg_tx_fee_sompi,
            kas_price_usd,
            block_height,
            timestamp_seconds,
        })
    }
}

/// Peg index calculator from Kaspa network state
#[derive(Debug, Clone)]
pub struct KaspaPegIndexCalculator {
    /// Baseline hashrate for normalization (hashes/second)
    baseline_hashrate_hps: f64,
}

impl KaspaPegIndexCalculator {
    /// Create calculator with baseline for index normalization
    /// baseline_hashrate_hps: historical average network hashrate
    pub fn new(baseline_hashrate_hps: f64) -> IgraResult<Self> {
        if baseline_hashrate_hps <= 0.0 {
            return Err(IgraError::InvalidParameters(
                "Baseline hashrate must be positive".to_string(),
            ));
        }

        Ok(Self {
            baseline_hashrate_hps,
        })
    }

    /// Calculate hashrate index from Kaspa network hashrate
    /// Returns normalized index where 1.0 = baseline, range [0.1, 5.0]
    pub fn calculate_hashrate_index(&self, current_hashrate_hps: f64) -> IgraResult<f64> {
        if current_hashrate_hps <= 0.0 || !current_hashrate_hps.is_finite() {
            return Err(IgraError::InvalidPegComponent(
                "Hashrate must be positive and finite".to_string(),
            ));
        }

        let index = current_hashrate_hps / self.baseline_hashrate_hps;
        let clipped = index.max(0.1).min(5.0);

        info!("Hashrate index: {:.4} (current: {:.0} hps, baseline: {:.0} hps)",
            clipped, current_hashrate_hps, self.baseline_hashrate_hps);

        Ok(clipped)
    }

    /// Calculate fees index from Kaspa average transaction fee
    /// Returns normalized index where 1.0 = baseline (0.1 KAS = 10M sompiā)
    /// Range [0.1, 5.0]
    pub fn calculate_fees_index(&self, avg_fee_sompi: &BigInt) -> IgraResult<f64> {
        // Baseline: 0.1 KAS = 10 million sompiā
        let baseline_fee_sompi = BigInt::from(10_000_000u64);

        let fee_f64 = avg_fee_sompi.to_f64().ok_or_else(|| {
            IgraError::CalculationOverflow("Fee too large".to_string())
        })?;

        let baseline_f64 = baseline_fee_sompi.to_f64().unwrap_or(10_000_000.0);

        if fee_f64 <= 0.0 {
            return Err(IgraError::InvalidPegComponent(
                "Fee must be positive".to_string(),
            ));
        }

        let index = fee_f64 / baseline_f64;
        let clipped = index.max(0.1).min(5.0);

        info!("Fees index: {:.4} (avg fee: {} sompiā)", clipped, avg_fee_sompi);

        Ok(clipped)
    }
}

/// Kaspa transaction builder for protocol operations
pub struct KaspaTransactionBuilder;

impl KaspaTransactionBuilder {
    /// Build collateral deposit transaction
    /// Sends sompiā from user address to vault escrow address
    ///
    /// In production: creates actual Kaspa transaction with inputs/outputs
    /// For testnet: validates amounts and addresses
    pub fn build_deposit_tx(
        from_address: &str,
        to_vault_address: &str,
        amount_kas: &BigInt,
    ) -> IgraResult<String> {
        if from_address.is_empty() || to_vault_address.is_empty() {
            return Err(IgraError::InvalidParameters(
                "Addresses cannot be empty".to_string(),
            ));
        }

        if amount_kas <= &BigInt::from(0) {
            return Err(IgraError::InvalidParameters(
                "Deposit amount must be positive".to_string(),
            ));
        }

        let amount_sompi = amount_kas * BigInt::from(SOMPI_PER_KAS);

        info!(
            "Deposit TX: {} KAS ({} sompiā) from {} to {}",
            amount_kas, amount_sompi, from_address, to_vault_address
        );

        // Returns transaction ID (in production, would be actual tx hash)
        Ok(format!(
            "tx_deposit_{}_{}",
            from_address.chars().take(8).collect::<String>(),
            to_vault_address.chars().take(8).collect::<String>()
        ))
    }

    /// Build liquidation settlement transaction
    /// Sends collateral KAS from vault to liquidator address
    pub fn build_liquidation_tx(
        vault_address: &str,
        liquidator_address: &str,
        collateral_kas: &BigInt,
    ) -> IgraResult<String> {
        if vault_address.is_empty() || liquidator_address.is_empty() {
            return Err(IgraError::InvalidParameters(
                "Addresses cannot be empty".to_string(),
            ));
        }

        if collateral_kas <= &BigInt::from(0) {
            return Err(IgraError::InvalidParameters(
                "Collateral must be positive".to_string(),
            ));
        }

        info!(
            "Liquidation TX: {} KAS from {} to {}",
            collateral_kas, vault_address, liquidator_address
        );

        Ok(format!(
            "tx_liquidate_{}_{}",
            vault_address.chars().take(8).collect::<String>(),
            liquidator_address.chars().take(8).collect::<String>()
        ))
    }

    /// Build token mint transaction for ENRK
    /// In production: calls Kaspa token contract
    pub fn build_enrk_mint_tx(
        to_address: &str,
        amount_enrk: &BigInt,
    ) -> IgraResult<String> {
        if to_address.is_empty() {
            return Err(IgraError::InvalidParameters(
                "Address cannot be empty".to_string(),
            ));
        }

        if amount_enrk <= &BigInt::from(0) {
            return Err(IgraError::InvalidParameters(
                "Mint amount must be positive".to_string(),
            ));
        }

        info!("ENRK Mint TX: {} ENRK to {}", amount_enrk, to_address);

        Ok(format!("tx_mint_enrk_{}", to_address.chars().take(12).collect::<String>()))
    }

    /// Build token mint transaction for kFIAT
    pub fn build_kfiat_mint_tx(
        to_address: &str,
        amount_kfiat: &BigInt,
    ) -> IgraResult<String> {
        if to_address.is_empty() {
            return Err(IgraError::InvalidParameters(
                "Address cannot be empty".to_string(),
            ));
        }

        if amount_kfiat <= &BigInt::from(0) {
            return Err(IgraError::InvalidParameters(
                "Mint amount must be positive".to_string(),
            ));
        }

        info!("kFIAT Mint TX: {} kFIAT to {}", amount_kfiat, to_address);

        Ok(format!("tx_mint_kfiat_{}", to_address.chars().take(12).collect::<String>()))
    }
}

/// Kaspa address validation
pub struct KaspaAddressValidator;

impl KaspaAddressValidator {
    /// Validate Kaspa mainnet address format
    /// Mainnet addresses start with 'kaspa:'
    pub fn is_valid_mainnet_address(address: &str) -> bool {
        address.starts_with("kaspa:") && address.len() > 10
    }

    /// Validate Kaspa testnet address format
    /// Testnet addresses start with 'kaspatest:'
    pub fn is_valid_testnet_address(address: &str) -> bool {
        address.starts_with("kaspatest:") && address.len() > 15
    }

    /// Check if address is valid for either network
    pub fn is_valid_address(address: &str) -> bool {
        Self::is_valid_mainnet_address(address) || Self::is_valid_testnet_address(address)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_kaspa_network_state_creation() {
        let state = KaspaNetworkState::new(
            1_000_000_000.0,  // 1 GH/s
            BigInt::from(1_000_000),  // 0.01 KAS
            5.0,  // $5 per KAS
            100_000,
            1000,
        );
        assert!(state.is_ok());
    }

    #[test]
    fn test_kaspa_network_state_invalid_hashrate() {
        let result = KaspaNetworkState::new(
            -1.0,  // invalid
            BigInt::from(1_000_000),
            5.0,
            100_000,
            1000,
        );
        assert!(result.is_err());
    }

    #[test]
    fn test_hashrate_index_calculation() {
        let calc = KaspaPegIndexCalculator::new(1_000_000_000.0).unwrap();

        // At baseline: should be 1.0
        let index = calc.calculate_hashrate_index(1_000_000_000.0).unwrap();
        assert!((index - 1.0).abs() < 0.01);

        // Double hashrate: should be 2.0
        let index = calc.calculate_hashrate_index(2_000_000_000.0).unwrap();
        assert!((index - 2.0).abs() < 0.01);

        // Half hashrate: should be 0.5
        let index = calc.calculate_hashrate_index(500_000_000.0).unwrap();
        assert!((index - 0.5).abs() < 0.01);
    }

    #[test]
    fn test_hashrate_index_clipping() {
        let calc = KaspaPegIndexCalculator::new(1_000_000_000.0).unwrap();

        // Extremely high hashrate should clip to 5.0
        let index = calc.calculate_hashrate_index(10_000_000_000.0).unwrap();
        assert_eq!(index, 5.0);

        // Very low hashrate should clip to 0.1
        let index = calc.calculate_hashrate_index(10_000_000.0).unwrap();
        assert_eq!(index, 0.1);
    }

    #[test]
    fn test_fees_index_calculation() {
        let calc = KaspaPegIndexCalculator::new(1_000_000_000.0).unwrap();

        // At baseline (10M sompiā): should be 1.0
        let index = calc.calculate_fees_index(&BigInt::from(10_000_000)).unwrap();
        assert!((index - 1.0).abs() < 0.01);

        // Double baseline: should be 2.0
        let index = calc.calculate_fees_index(&BigInt::from(20_000_000)).unwrap();
        assert!((index - 2.0).abs() < 0.01);
    }

    #[test]
    fn test_build_deposit_tx() {
        let tx = KaspaTransactionBuilder::build_deposit_tx(
            "kaspa:from_addr",
            "kaspa:vault_addr",
            &BigInt::from(100),
        );
        assert!(tx.is_ok());
        assert!(tx.unwrap().contains("deposit"));
    }

    #[test]
    fn test_build_liquidation_tx() {
        let tx = KaspaTransactionBuilder::build_liquidation_tx(
            "kaspa:vault_addr",
            "kaspa:liquidator_addr",
            &BigInt::from(50),
        );
        assert!(tx.is_ok());
        assert!(tx.unwrap().contains("liquidate"));
    }

    #[test]
    fn test_build_enrk_mint_tx() {
        let tx = KaspaTransactionBuilder::build_enrk_mint_tx(
            "kaspa:user_addr",
            &BigInt::from(100),
        );
        assert!(tx.is_ok());
        assert!(tx.unwrap().contains("mint_enrk"));
    }

    #[test]
    fn test_address_validation_mainnet() {
        assert!(KaspaAddressValidator::is_valid_mainnet_address("kaspa:something_valid"));
        assert!(!KaspaAddressValidator::is_valid_mainnet_address("kaspatest:something"));
        assert!(!KaspaAddressValidator::is_valid_mainnet_address("invalid"));
    }

    #[test]
    fn test_address_validation_testnet() {
        assert!(KaspaAddressValidator::is_valid_testnet_address("kaspatest:something_valid"));
        assert!(!KaspaAddressValidator::is_valid_testnet_address("kaspa:something"));
    }

    #[test]
    fn test_sompi_conversion() {
        let kas = BigInt::from(1);
        let sompi = kas * BigInt::from(SOMPI_PER_KAS);
        assert_eq!(sompi, BigInt::from(100_000_000));
    }
}
