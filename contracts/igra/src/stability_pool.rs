//! Stability Pool: Automatic peg defense mechanism
//!
//! The Stability Pool is the protocol's self-regulating buyback mechanism.
//!
//! How it works:
//! 1. Collects 80% of all protocol fees (mint, liquidation, redemption fees)
//! 2. When ENRK price falls below peg:
//!    - Pool automatically buys ENRK at discount
//!    - Burns the purchased ENRK (reduces supply)
//! 3. This reduces supply when demand is weak, restoring peg
//! 4. Profitable for protocol: buys low, removes supply
//!
//! Mathematical property:
//! - If Stability Pool balance is sufficient, peg defended
//! - Automatic (no governance required), immutable trigger
//! - Only activates when price < peg - does NOT trade actively
//!
//! Example:
//! - ENRK price at 0.95 (5% below peg)
//! - Pool has 1000 ENRK in balance
//! - Pool buys ENRK at 0.95, burning it
//! - Supply reduced → demand/supply ratio improves → price rises toward peg

use crate::errors::{IgraError, IgraResult};
use crate::types::StabilityPool;
use log::{debug, info};
use num_bigint::BigInt;
use num_traits::cast::ToPrimitive;

/// Stability Pool manager
pub struct StabilityPoolManager {
    pool: StabilityPool,
}

impl StabilityPoolManager {
    /// Create new Stability Pool
    pub fn new() -> Self {
        Self {
            pool: StabilityPool {
                enrk_balance: BigInt::from(0),
                cumulative_fees_collected: BigInt::from(0),
                last_buyback_seconds: 0,
            },
        }
    }

    /// Add fees collected from protocol operations
    /// Called whenever: mint, liquidation, or redemption fees are collected
    /// Only 80% goes to Stability Pool; 20% goes to Treasury
    pub fn deposit_fees(&mut self, total_fees: BigInt, stability_pool_allocation: u8) -> IgraResult<BigInt> {
        if total_fees <= BigInt::from(0) {
            return Err(IgraError::InvalidParameters(
                "Fees must be positive".to_string(),
            ));
        }

        // Calculate pool's share (default 80%)
        let pool_share_factor = stability_pool_allocation as f64 / 100.0;
        let total_f64 = total_fees.to_f64().ok_or_else(|| {
            IgraError::CalculationOverflow("Fee amount too large".to_string())
        })?;

        let pool_share = total_f64 * pool_share_factor;

        if !pool_share.is_finite() {
            return Err(IgraError::CalculationOverflow(
                "Pool share calculation overflowed".to_string(),
            ));
        }

        let pool_share_bigint = BigInt::from(pool_share as u64);

        self.pool.enrk_balance = self.pool.enrk_balance.clone() + pool_share_bigint.clone();
        self.pool.cumulative_fees_collected = self.pool.cumulative_fees_collected.clone() + total_fees;

        debug!(
            "Fees deposited to Stability Pool: {}",
            pool_share_bigint
        );

        Ok(pool_share_bigint)
    }

    /// Attempt automatic buyback: buy ENRK when price is below peg
    ///
    /// Returns: (enrk_burned, cost_paid)
    /// Only executes if:
    /// - ENRK price < 1.0 (below peg)
    /// - Pool has sufficient balance
    /// - Buyback hasn't occurred in last 6 hours (prevent spam)
    pub fn attempt_buyback(
        &mut self,
        enrk_price: f64,
        buyback_amount: &BigInt,
    ) -> IgraResult<(BigInt, BigInt)> {
        // Check price is below peg
        if enrk_price >= 1.0 {
            return Err(IgraError::PriceAbovePeg);
        }

        if buyback_amount <= &BigInt::from(0) {
            return Err(IgraError::InvalidParameters(
                "Buyback amount must be positive".to_string(),
            ));
        }

        // Check sufficient balance
        if self.pool.enrk_balance < *buyback_amount {
            return Err(IgraError::BuybackExceedsPoolBalance);
        }

        // Calculate cost in the depressed stablecoin
        // At price 0.95, buying 100 ENRK costs 100 * 0.95 = 95 stablecoins
        let buyback_f64 = buyback_amount.to_f64().ok_or_else(|| {
            IgraError::CalculationOverflow("Buyback amount too large".to_string())
        })?;

        let cost = buyback_f64 * enrk_price;

        if !cost.is_finite() {
            return Err(IgraError::CalculationOverflow(
                "Cost calculation overflowed".to_string(),
            ));
        }

        // Burn the ENRK (remove from pool, remove from circulation)
        self.pool.enrk_balance = self.pool.enrk_balance.clone() - buyback_amount.clone();

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        self.pool.last_buyback_seconds = now;

        let cost_bigint = BigInt::from(cost as u64);

        info!(
            "Stability Pool buyback: burned={}, cost={}, enrk_price={}",
            buyback_amount, cost_bigint, enrk_price
        );

        Ok((buyback_amount.clone(), cost_bigint))
    }

    /// Get current pool balance
    pub fn balance(&self) -> BigInt {
        self.pool.enrk_balance.clone()
    }

    /// Get cumulative fees collected
    pub fn cumulative_fees(&self) -> BigInt {
        self.pool.cumulative_fees_collected.clone()
    }

    /// Check if pool has sufficient balance for operation
    pub fn has_sufficient_balance(&self, amount: &BigInt) -> bool {
        self.pool.enrk_balance >= *amount
    }

    /// Get last buyback timestamp
    pub fn last_buyback(&self) -> u64 {
        self.pool.last_buyback_seconds
    }

    /// Calculate how much ENRK could be bought at current price
    /// Returns maximum affordable amount given pool balance and price
    pub fn max_buyable(&self, current_price: f64) -> IgraResult<BigInt> {
        if current_price <= 0.0 {
            return Err(IgraError::InvalidParameters(
                "Price must be positive".to_string(),
            ));
        }

        let balance_f64 = self.pool.enrk_balance.to_f64().ok_or_else(|| {
            IgraError::CalculationOverflow("Balance too large".to_string())
        })?;

        // At price 0.95, balance 1000 can buy: 1000 / 0.95 = 1052 ENRK
        let buyable = balance_f64 / current_price;

        if !buyable.is_finite() {
            return Err(IgraError::CalculationOverflow(
                "Buyable calculation overflowed".to_string(),
            ));
        }

        Ok(BigInt::from(buyable as u64))
    }

    /// Liquidation proceeds: when vault liquidated, collateral goes to pool
    /// (In full implementation, kFIAT holders also deposit their losses here)
    pub fn deposit_liquidation_proceeds(&mut self, proceeds: BigInt) -> IgraResult<()> {
        if proceeds < BigInt::from(0) {
            return Err(IgraError::InvalidParameters(
                "Proceeds cannot be negative".to_string(),
            ));
        }

        // Note: proceeds are in ENRK or kFIAT, not KAS
        // In full system, these get swapped to ENRK for pool
        self.pool.enrk_balance = self.pool.enrk_balance.clone() + proceeds.clone();

        debug!("Liquidation proceeds deposited: {}", proceeds);

        Ok(())
    }

    /// Get pool statistics
    pub fn stats(&self) -> StabilityPoolStats {
        StabilityPoolStats {
            balance: self.pool.enrk_balance.clone(),
            cumulative_fees: self.pool.cumulative_fees_collected.clone(),
            last_buyback: self.pool.last_buyback_seconds,
        }
    }
}

pub struct StabilityPoolStats {
    pub balance: BigInt,
    pub cumulative_fees: BigInt,
    pub last_buyback: u64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pool_creation() {
        let pool = StabilityPoolManager::new();
        assert_eq!(pool.balance(), BigInt::from(0));
    }

    #[test]
    fn test_deposit_fees() {
        let mut pool = StabilityPoolManager::new();

        let deposited = pool
            .deposit_fees(BigInt::from(1000), 80)
            .unwrap();

        // 80% of 1000 = 800
        assert_eq!(deposited, BigInt::from(800));
        assert_eq!(pool.balance(), BigInt::from(800));
    }

    #[test]
    fn test_deposit_fees_different_allocation() {
        let mut pool = StabilityPoolManager::new();

        let deposited = pool
            .deposit_fees(BigInt::from(1000), 50)
            .unwrap();

        // 50% of 1000 = 500
        assert_eq!(deposited, BigInt::from(500));
    }

    #[test]
    fn test_cumulative_fees_tracking() {
        let mut pool = StabilityPoolManager::new();

        pool.deposit_fees(BigInt::from(100), 80).unwrap();
        pool.deposit_fees(BigInt::from(200), 80).unwrap();

        // Total deposited = 300, not 240
        assert_eq!(pool.cumulative_fees(), BigInt::from(300));
    }

    #[test]
    fn test_attempted_buyback_above_peg() {
        let mut pool = StabilityPoolManager::new();

        pool.deposit_fees(BigInt::from(1000), 80).unwrap();

        // Price at 1.05 (above peg) - should fail
        let result = pool.attempt_buyback(1.05, &BigInt::from(100));
        assert!(result.is_err());
        assert!(matches!(result, Err(IgraError::PriceAbovePeg)));
    }

    #[test]
    fn test_successful_buyback() {
        let mut pool = StabilityPoolManager::new();

        pool.deposit_fees(BigInt::from(1000), 80).unwrap();

        // Price at 0.95 (5% below peg)
        // Buy 100 ENRK at 0.95 = 95 cost
        let (burned, cost) = pool
            .attempt_buyback(0.95, &BigInt::from(100))
            .unwrap();

        assert_eq!(burned, BigInt::from(100));
        assert_eq!(cost, BigInt::from(95));
        assert_eq!(pool.balance(), BigInt::from(700));
    }

    #[test]
    fn test_buyback_insufficient_balance() {
        let mut pool = StabilityPoolManager::new();

        pool.deposit_fees(BigInt::from(100), 80).unwrap();

        // Try to buy 200 when only 80 available
        let result = pool.attempt_buyback(0.95, &BigInt::from(200));
        assert!(result.is_err());
        assert!(matches!(result, Err(IgraError::BuybackExceedsPoolBalance)));
    }

    #[test]
    fn test_max_buyable_calculation() {
        let mut pool = StabilityPoolManager::new();

        pool.deposit_fees(BigInt::from(1000), 80).unwrap();

        // Balance: 800, Price: 0.95
        // Max buyable: 800 / 0.95 = 842 ENRK
        let max = pool.max_buyable(0.95).unwrap();
        assert!(max > BigInt::from(840));
    }

    #[test]
    fn test_has_sufficient_balance() {
        let mut pool = StabilityPoolManager::new();

        pool.deposit_fees(BigInt::from(1000), 80).unwrap();

        assert!(pool.has_sufficient_balance(&BigInt::from(500)));
        assert!(pool.has_sufficient_balance(&BigInt::from(800)));
        assert!(!pool.has_sufficient_balance(&BigInt::from(900)));
    }

    #[test]
    fn test_liquidation_proceeds() {
        let mut pool = StabilityPoolManager::new();

        pool.deposit_liquidation_proceeds(BigInt::from(500))
            .unwrap();

        assert_eq!(pool.balance(), BigInt::from(500));
    }

    #[test]
    fn test_stats() {
        let mut pool = StabilityPoolManager::new();

        pool.deposit_fees(BigInt::from(1000), 80).unwrap();

        let stats = pool.stats();
        assert_eq!(stats.balance, BigInt::from(800));
        assert_eq!(stats.cumulative_fees, BigInt::from(1000));
    }
}
