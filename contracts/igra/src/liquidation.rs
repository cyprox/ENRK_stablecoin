//! Liquidation engine
//!
//! Implements Dutch Auction mechanism for liquidating under-collateralized vaults
//!
//! How it works:
//! 1. Vault falls below MCR (150% collateral ratio)
//! 2. Auction starts: collateral available at 100% of market price
//! 3. Over 120 minutes: price linearly descends to 85% (liquidation incentive)
//! 4. Anyone can bid to buy collateral and cover the vault's debt
//! 5. First successful bid ends auction, collateral transferred, debt burned
//!
//! Key properties:
//! - No centralized liquidators required
//! - Gradual price descent incentivizes participation
//! - Profitable at market price (100%), free profit (5-15%) for arbitrageurs
//! - Stability Pool can bid with accrued fees
//! - Protocol collects liquidation fees (4% default)

use crate::errors::{IgraError, IgraResult};
use crate::types::{LiquidationAuction, LiquidationParams, Vault};
use log::{info, warn};
use num_bigint::BigInt;
use num_traits::cast::ToPrimitive;
use std::collections::HashMap;

/// Liquidation manager: handles auctions for under-collateralized vaults
pub struct LiquidationManager {
    auctions: HashMap<u64, LiquidationAuction>,
    next_auction_id: u64,
    auction_params: LiquidationParams,
}

impl LiquidationManager {
    /// Create new liquidation manager with frozen parameters
    pub fn new(auction_params: LiquidationParams) -> IgraResult<Self> {
        auction_params.validate().map_err(|e| IgraError::InvalidParameters(e))?;

        info!(
            "LiquidationManager initialized: duration={}min, price_range={}%-{}%",
            auction_params.duration_minutes, auction_params.start_price, auction_params.end_price
        );

        Ok(Self {
            auctions: HashMap::new(),
            next_auction_id: 1,
            auction_params,
        })
    }

    /// Start liquidation auction for a vault
    /// Can only start if vault is under-collateralized (ICR < MCR)
    /// Returns the auction ID
    pub fn start_liquidation(
        &mut self,
        vault: &Vault,
        kas_price: f64,
        enrk_price: f64,
        kfiat_price: f64,
        mcr_trigger: u16,
    ) -> IgraResult<u64> {
        // Verify vault is actually under-collateralized
        if !vault.is_under_collateralized(kas_price, enrk_price, kfiat_price, mcr_trigger) {
            let icr = vault.calculate_icr(kas_price, enrk_price, kfiat_price);
            return Err(IgraError::VaultHealthy {
                icr: icr as u16,
                mcr: mcr_trigger,
            });
        }

        // Check vault doesn't already have active auction
        if let Some(_) = self
            .auctions
            .values()
            .find(|a| a.vault_id == vault.vault_id)
        {
            return Err(IgraError::AuctionAlreadyExists(vault.vault_id));
        }

        let auction_id = self.next_auction_id;
        self.next_auction_id += 1;

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        let auction = LiquidationAuction {
            auction_id,
            vault_id: vault.vault_id,
            collateral_kas: vault.collateral_kas.clone(),
            debt_to_cover: vault.debt_enrk.clone() + vault.debt_kfiat.clone(),
            started_at_seconds: now,
            duration_minutes: self.auction_params.duration_minutes,
        };

        self.auctions.insert(auction_id, auction.clone());

        info!(
            "Liquidation started: vault={}, auction={}, collateral={}, debt={}",
            vault.vault_id, auction_id, auction.collateral_kas, auction.debt_to_cover
        );

        Ok(auction_id)
    }

    /// Get auction by ID
    pub fn get_auction(&self, auction_id: u64) -> IgraResult<LiquidationAuction> {
        self.auctions
            .get(&auction_id)
            .cloned()
            .ok_or(IgraError::AuctionNotFound(auction_id))
    }

    /// Get current auction price as percentage of market price
    /// Returns percentage (100 = market price, 85 = 15% discount at end)
    pub fn get_auction_price(&self, auction_id: u64) -> IgraResult<u8> {
        let auction = self.get_auction(auction_id)?;

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        Ok(auction.current_price_percent(now, self.auction_params.end_price))
    }

    /// Calculate amount of KAS a bid would receive at current price
    /// bid_amount_in_stablecoins = amount of ENRK/kFIAT offered
    /// current_price_percent = 85-100 (percentage of market price)
    /// kas_price_usd = market price of 1 KAS in USD equivalent
    /// Returns KAS amount purchaser would receive
    pub fn calculate_collateral_for_bid(
        &self,
        bid_amount: &BigInt,
        current_price_percent: u8,
        kas_price: f64,
    ) -> IgraResult<BigInt> {
        if current_price_percent == 0 || current_price_percent > 100 {
            return Err(IgraError::InvalidParameters(
                "Current price must be 0 < x <= 100%".to_string(),
            ));
        }

        if kas_price <= 0.0 {
            return Err(IgraError::InvalidParameters("KAS price must be positive".to_string()));
        }

        let bid_f64 = bid_amount.to_f64().ok_or_else(|| {
            IgraError::CalculationOverflow("Bid amount too large".to_string())
        })?;

        let price_discount = current_price_percent as f64 / 100.0;
        let kas_amount = (bid_f64 * price_discount) / kas_price;

        if !kas_amount.is_finite() {
            return Err(IgraError::CalculationOverflow(
                "KAS calculation overflowed".to_string(),
            ));
        }

        Ok(BigInt::from(kas_amount as u64))
    }

    /// Submit bid to purchase collateral in auction
    /// Checks:
    /// - Auction exists and is active (not expired)
    /// - Bid covers debt at current price (with discount)
    /// - Bid doesn't exceed available collateral
    ///
    /// Returns (collateral_kas_received, fee_paid_to_protocol)
    pub fn submit_bid(
        &mut self,
        auction_id: u64,
        bid_amount: BigInt,
        kas_price: f64,
        liquidation_fee_bps: u16,
    ) -> IgraResult<(BigInt, BigInt)> {
        if bid_amount <= BigInt::from(0) {
            return Err(IgraError::InvalidParameters(
                "Bid amount must be positive".to_string(),
            ));
        }

        let auction = self.get_auction(auction_id)?;

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        // Check auction is still active
        if auction.is_expired(now) {
            return Err(IgraError::AuctionExpired);
        }

        // Get current price
        let current_price_percent = auction.current_price_percent(now, self.auction_params.end_price);

        // Check bid is sufficient
        // Bid must cover debt at current price
        // debt_in_kas = debt / (kas_price * price_percent)
        let debt_f64 = auction.debt_to_cover.to_f64().ok_or_else(|| {
            IgraError::CalculationOverflow("Debt too large".to_string())
        })?;

        let price_multiplier = (current_price_percent as f64) / 100.0;
        let required_bid = debt_f64 / (kas_price * price_multiplier);

        let bid_f64 = bid_amount.to_f64().ok_or_else(|| {
            IgraError::CalculationOverflow("Bid amount too large".to_string())
        })?;

        if bid_f64 < required_bid {
            return Err(IgraError::BidTooLow {
                bid: bid_f64 as u64,
                required: required_bid as u64,
                price: current_price_percent,
            });
        }

        // Calculate collateral to be transferred
        let collateral_kas = self.calculate_collateral_for_bid(&bid_amount, current_price_percent, kas_price)?;

        // Check doesn't exceed available collateral
        if collateral_kas > auction.collateral_kas {
            return Err(IgraError::BidExceedsCollateral);
        }

        // Calculate liquidation fee (4% default)
        let fee = Self::calculate_fee(&bid_amount, liquidation_fee_bps)?;

        // Remove auction (settled)
        self.auctions.remove(&auction_id);

        info!(
            "Bid accepted: auction={}, bid={}, collateral_received={}, fee={}",
            auction_id, bid_amount, collateral_kas, fee
        );

        Ok((collateral_kas, fee))
    }

    /// Get all active auctions
    pub fn get_active_auctions(&self) -> Vec<LiquidationAuction> {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        self.auctions
            .values()
            .filter(|a| !a.is_expired(now))
            .cloned()
            .collect()
    }

    /// Get all expired auctions (can be cleaned up)
    pub fn get_expired_auctions(&self) -> Vec<LiquidationAuction> {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        self.auctions
            .values()
            .filter(|a| a.is_expired(now))
            .cloned()
            .collect()
    }

    /// Clean up expired auction (redistribute collateral if needed)
    /// Called after 120 minutes with no bids
    pub fn finalize_expired_auction(&mut self, auction_id: u64) -> IgraResult<()> {
        let auction = self.get_auction(auction_id)?;

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        if !auction.is_expired(now) {
            return Err(IgraError::AuctionStillActive);
        }

        // In a full implementation, collateral would be redistributed to:
        // 1. Stability Pool (if has capacity)
        // 2. Otherwise, socialized loss across active vaults
        // For this skeleton, we just remove the auction

        self.auctions.remove(&auction_id);

        warn!(
            "Auction expired without bids: vault={}, collateral={}",
            auction.vault_id, auction.collateral_kas
        );

        Ok(())
    }

    /// Calculate fee from bid amount
    fn calculate_fee(bid: &BigInt, fee_bps: u16) -> IgraResult<BigInt> {
        let fee_factor = fee_bps as f64 / 10000.0;
        let bid_f64 = bid.to_f64().ok_or_else(|| {
            IgraError::CalculationOverflow("Bid too large".to_string())
        })?;
        let fee_f64 = bid_f64 * fee_factor;

        if !fee_f64.is_finite() {
            return Err(IgraError::CalculationOverflow(
                "Fee calculation overflowed".to_string(),
            ));
        }

        Ok(BigInt::from(fee_f64 as u64))
    }

    /// Get auction count
    pub fn auction_count(&self) -> usize {
        self.auctions.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::VaultStatus;

    fn create_test_manager() -> LiquidationManager {
        LiquidationManager::new(LiquidationParams::default()).unwrap()
    }

    fn create_test_vault(vault_id: u64) -> Vault {
        Vault {
            vault_id,
            owner: "addr_test".to_string(),
            collateral_kas: BigInt::from(100),
            debt_enrk: BigInt::from(50),
            debt_kfiat: BigInt::from(10),
            status: VaultStatus::Active,
            created_at_seconds: 0,
            last_updated_seconds: 0,
        }
    }

    #[test]
    fn test_liquidation_manager_creation() {
        let manager = create_test_manager();
        assert_eq!(manager.auction_count(), 0);
    }

    #[test]
    fn test_start_liquidation() {
        let mut manager = create_test_manager();
        let vault = create_test_vault(1);

        // Vault with collateral=100 KAS, debt=60 stablecoins
        // At KAS price 0.5, ICR = (100 * 0.5) / 60 = 83% (under 150% MCR)
        let auction_id = manager
            .start_liquidation(&vault, 0.5, 1.0, 1.0, 150)
            .unwrap();

        assert_eq!(auction_id, 1);
        assert_eq!(manager.auction_count(), 1);
    }

    #[test]
    fn test_start_liquidation_healthy_vault() {
        let mut manager = create_test_manager();
        let vault = Vault {
            vault_id: 1,
            owner: "addr_test".to_string(),
            collateral_kas: BigInt::from(1000),  // Very high collateral
            debt_enrk: BigInt::from(50),
            debt_kfiat: BigInt::from(0),
            status: VaultStatus::Active,
            created_at_seconds: 0,
            last_updated_seconds: 0,
        };

        let result = manager.start_liquidation(&vault, 5.0, 1.0, 1.0, 150);
        assert!(result.is_err());
        assert!(matches!(result, Err(IgraError::VaultHealthy { .. })));
    }

    #[test]
    fn test_auction_price_progression() {
        let _manager = create_test_manager();

        // Create auction manually
        let auction = LiquidationAuction {
            auction_id: 1,
            vault_id: 1,
            collateral_kas: BigInt::from(100),
            debt_to_cover: BigInt::from(50),
            started_at_seconds: 1000,
            duration_minutes: 120,
        };

        // At start: 100%
        let price_start = auction.current_price_percent(1000, 85);
        assert_eq!(price_start, 100);

        // After 60 minutes (halfway): ~92.5%
        let price_mid = auction.current_price_percent(1000 + 3600, 85);
        assert!(price_mid >= 92 && price_mid <= 93);

        // At end (120 minutes): 85%
        let price_end = auction.current_price_percent(1000 + 7200, 85);
        assert_eq!(price_end, 85);
    }

    #[test]
    fn test_calculate_collateral_for_bid() {
        let manager = create_test_manager();

        // Bid 100 units at 85% price
        // Receiving: (100 * 0.85) / 5 = 17 KAS
        let collateral = manager
            .calculate_collateral_for_bid(&BigInt::from(100), 85, 5.0)
            .unwrap();

        assert_eq!(collateral, BigInt::from(17));
    }

    #[test]
    fn test_active_auction_listing() {
        let mut manager = create_test_manager();
        let vault = create_test_vault(1);

        manager
            .start_liquidation(&vault, 0.5, 1.0, 1.0, 150)
            .unwrap();

        let active = manager.get_active_auctions();
        assert_eq!(active.len(), 1);
    }

    #[test]
    fn test_expired_auction_detection() {
        let mut manager = create_test_manager();

        // Manually create expired auction
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        let auction = LiquidationAuction {
            auction_id: 1,
            vault_id: 1,
            collateral_kas: BigInt::from(100),
            debt_to_cover: BigInt::from(50),
            started_at_seconds: now - 8000,  // Started 133 minutes ago
            duration_minutes: 120,
        };

        manager.auctions.insert(1, auction);

        let expired = manager.get_expired_auctions();
        assert_eq!(expired.len(), 1);
    }
}
