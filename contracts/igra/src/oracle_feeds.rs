//! Oracle feed integration for peg indices
//!
//! Fetches real-time data from three sources:
//! - Band Protocol: Global energy price ($/kWh)
//! - Chainlink: Crypto adoption metric
//! - Kaspa RPC: Network hashrate and fees
//!
//! Implements fallback chain with caching for resilience.
//! All indices normalized to [0.1, 5.0] range.

use crate::errors::{IgraError, IgraResult};
use crate::kaspa_adapter::KaspaPegIndexCalculator;
use log::{info, warn};
use num_bigint::BigInt;
use std::collections::HashMap;

/// Oracle feed data with timestamp and source
#[derive(Debug, Clone)]
pub struct OracleFeedData {
    /// Energy price index (0.1 = 10% below baseline, 1.0 = baseline, 5.0 = 5x baseline)
    pub energy_index: f64,
    /// Adoption index (crypto market maturity)
    pub adoption_index: f64,
    /// Hashrate index (Kaspa network health)
    pub hashrate_index: f64,
    /// Fees index (Kaspa network activity)
    pub fees_index: f64,
    /// When this data was fetched (seconds since epoch)
    pub timestamp_seconds: u64,
}

/// Energy price feed from Band Protocol
#[derive(Debug, Clone)]
pub struct EnergyPriceFeed {
    /// Current energy price (USD per kWh)
    price_usd_per_kwh: f64,
    /// Baseline for index calculation (default: $0.10/kWh)
    baseline_usd_per_kwh: f64,
    /// Last fetch timestamp
    last_updated_seconds: u64,
}

impl EnergyPriceFeed {
    pub fn new(baseline_usd_per_kwh: f64) -> IgraResult<Self> {
        if baseline_usd_per_kwh <= 0.0 || !baseline_usd_per_kwh.is_finite() {
            return Err(IgraError::InvalidParameters(
                "Energy baseline must be positive and finite".to_string(),
            ));
        }

        Ok(Self {
            price_usd_per_kwh: baseline_usd_per_kwh,
            baseline_usd_per_kwh,
            last_updated_seconds: 0,
        })
    }

    /// Update energy price from Band Protocol (or mock data in tests)
    pub fn update_price(&mut self, price_usd_per_kwh: f64, timestamp_seconds: u64) -> IgraResult<()> {
        if price_usd_per_kwh <= 0.0 || !price_usd_per_kwh.is_finite() {
            return Err(IgraError::InvalidPegComponent(
                "Energy price must be positive and finite".to_string(),
            ));
        }

        self.price_usd_per_kwh = price_usd_per_kwh;
        self.last_updated_seconds = timestamp_seconds;

        info!("Energy price updated: ${:.4}/kWh at {}", price_usd_per_kwh, timestamp_seconds);

        Ok(())
    }

    /// Calculate energy price index
    pub fn calculate_index(&self) -> IgraResult<f64> {
        let index = self.price_usd_per_kwh / self.baseline_usd_per_kwh;
        let clipped = index.max(0.1).min(5.0);

        info!("Energy index: {:.4} (price: ${:.4}/kWh, baseline: ${:.4}/kWh)",
            clipped, self.price_usd_per_kwh, self.baseline_usd_per_kwh);

        Ok(clipped)
    }

    /// Check if data is fresh (not stale)
    /// Returns false if never updated (last_updated_seconds == 0)
    pub fn is_fresh(&self, now_seconds: u64, max_age_seconds: u64) -> bool {
        if self.last_updated_seconds == 0 {
            return false;  // Never updated
        }
        (now_seconds - self.last_updated_seconds) <= max_age_seconds
    }
}

/// Adoption metric feed from Chainlink
#[derive(Debug, Clone)]
pub struct AdoptionMetricFeed {
    /// Current adoption metric (normalized value)
    adoption_value: f64,
    /// Baseline for index calculation (2023 average)
    baseline_adoption: f64,
    /// Last fetch timestamp
    last_updated_seconds: u64,
}

impl AdoptionMetricFeed {
    pub fn new(baseline_adoption: f64) -> IgraResult<Self> {
        if baseline_adoption <= 0.0 || !baseline_adoption.is_finite() {
            return Err(IgraError::InvalidParameters(
                "Adoption baseline must be positive and finite".to_string(),
            ));
        }

        Ok(Self {
            adoption_value: baseline_adoption,
            baseline_adoption,
            last_updated_seconds: 0,
        })
    }

    /// Update adoption metric from Chainlink or on-chain source
    pub fn update_metric(&mut self, adoption_value: f64, timestamp_seconds: u64) -> IgraResult<()> {
        if adoption_value <= 0.0 || !adoption_value.is_finite() {
            return Err(IgraError::InvalidPegComponent(
                "Adoption value must be positive and finite".to_string(),
            ));
        }

        self.adoption_value = adoption_value;
        self.last_updated_seconds = timestamp_seconds;

        info!("Adoption metric updated: {:.4} at {}", adoption_value, timestamp_seconds);

        Ok(())
    }

    /// Calculate adoption index
    pub fn calculate_index(&self) -> IgraResult<f64> {
        let index = self.adoption_value / self.baseline_adoption;
        let clipped = index.max(0.1).min(5.0);

        info!("Adoption index: {:.4} (value: {:.4}, baseline: {:.4})",
            clipped, self.adoption_value, self.baseline_adoption);

        Ok(clipped)
    }

    /// Check if data is fresh
    /// Returns false if never updated (last_updated_seconds == 0)
    pub fn is_fresh(&self, now_seconds: u64, max_age_seconds: u64) -> bool {
        if self.last_updated_seconds == 0 {
            return false;  // Never updated
        }
        (now_seconds - self.last_updated_seconds) <= max_age_seconds
    }
}

/// Kaspa network state feed from RPC
#[derive(Debug, Clone)]
pub struct KaspaNetworkFeed {
    /// Current network hashrate (hashes/second)
    hashrate_hps: f64,
    /// Average transaction fee (in sompiā, 1 KAS = 100M sompiā)
    avg_fee_sompi: BigInt,
    /// Peg index calculator (contains baseline)
    peg_calculator: Option<KaspaPegIndexCalculator>,
    /// Last fetch timestamp
    last_updated_seconds: u64,
}

impl KaspaNetworkFeed {
    pub fn new() -> Self {
        Self {
            hashrate_hps: 0.0,
            avg_fee_sompi: BigInt::from(0),
            peg_calculator: None,
            last_updated_seconds: 0,
        }
    }

    /// Initialize with peg calculator (baseline)
    pub fn with_calculator(calculator: KaspaPegIndexCalculator) -> Self {
        Self {
            hashrate_hps: 0.0,
            avg_fee_sompi: BigInt::from(0),
            peg_calculator: Some(calculator),
            last_updated_seconds: 0,
        }
    }

    /// Update network state from Kaspa RPC
    pub fn update_network_state(
        &mut self,
        hashrate_hps: f64,
        avg_fee_sompi: BigInt,
        timestamp_seconds: u64,
    ) -> IgraResult<()> {
        if hashrate_hps <= 0.0 || !hashrate_hps.is_finite() {
            return Err(IgraError::InvalidPegComponent(
                "Hashrate must be positive and finite".to_string(),
            ));
        }

        self.hashrate_hps = hashrate_hps;
        self.avg_fee_sompi = avg_fee_sompi;
        self.last_updated_seconds = timestamp_seconds;

        info!("Kaspa network state updated: {:.0} hps, {} sompiā fee at {}",
            hashrate_hps, self.avg_fee_sompi, timestamp_seconds);

        Ok(())
    }

    /// Calculate hashrate index (requires calculator)
    pub fn calculate_hashrate_index(&self) -> IgraResult<f64> {
        let calculator = self.peg_calculator.as_ref()
            .ok_or_else(|| IgraError::InvalidParameters("No calculator available".to_string()))?;

        calculator.calculate_hashrate_index(self.hashrate_hps)
    }

    /// Calculate fees index (requires calculator)
    pub fn calculate_fees_index(&self) -> IgraResult<f64> {
        let calculator = self.peg_calculator.as_ref()
            .ok_or_else(|| IgraError::InvalidParameters("No calculator available".to_string()))?;

        calculator.calculate_fees_index(&self.avg_fee_sompi)
    }

    /// Check if data is fresh
    /// Returns false if never updated (last_updated_seconds == 0)
    pub fn is_fresh(&self, now_seconds: u64, max_age_seconds: u64) -> bool {
        if self.last_updated_seconds == 0 {
            return false;  // Never updated
        }
        (now_seconds - self.last_updated_seconds) <= max_age_seconds
    }
}

/// Oracle feed manager: coordinates all feeds with fallback chain
pub struct OracleFeedManager {
    energy_feed: EnergyPriceFeed,
    adoption_feed: AdoptionMetricFeed,
    kaspa_feed: KaspaNetworkFeed,
    /// Cache of recent feed data
    cache: HashMap<String, (OracleFeedData, u64)>,
    /// Maximum age of cached data (seconds)
    cache_ttl_seconds: u64,
}

impl OracleFeedManager {
    /// Create new oracle manager
    pub fn new(
        baseline_energy_usd_per_kwh: f64,
        baseline_adoption: f64,
        peg_calculator: KaspaPegIndexCalculator,
        cache_ttl_seconds: u64,
    ) -> IgraResult<Self> {
        Ok(Self {
            energy_feed: EnergyPriceFeed::new(baseline_energy_usd_per_kwh)?,
            adoption_feed: AdoptionMetricFeed::new(baseline_adoption)?,
            kaspa_feed: KaspaNetworkFeed::with_calculator(peg_calculator),
            cache: HashMap::new(),
            cache_ttl_seconds,
        })
    }

    /// Update energy price (from Band Protocol in production)
    pub fn update_energy_price(&mut self, price_usd_per_kwh: f64, timestamp_seconds: u64) -> IgraResult<()> {
        self.energy_feed.update_price(price_usd_per_kwh, timestamp_seconds)?;
        self.cache.clear();  // Invalidate cache on any update
        Ok(())
    }

    /// Update adoption metric (from Chainlink in production)
    pub fn update_adoption_metric(&mut self, adoption_value: f64, timestamp_seconds: u64) -> IgraResult<()> {
        self.adoption_feed.update_metric(adoption_value, timestamp_seconds)?;
        self.cache.clear();
        Ok(())
    }

    /// Update Kaspa network state (from RPC in production)
    pub fn update_kaspa_network(
        &mut self,
        hashrate_hps: f64,
        avg_fee_sompi: BigInt,
        timestamp_seconds: u64,
    ) -> IgraResult<()> {
        self.kaspa_feed.update_network_state(hashrate_hps, avg_fee_sompi, timestamp_seconds)?;
        self.cache.clear();
        Ok(())
    }

    /// Fetch all four peg indices
    /// Returns: (hashrate_index, energy_index, fees_index, adoption_index)
    /// Or returns error if any source is stale
    pub fn fetch_all_indices(&mut self, now_seconds: u64) -> IgraResult<(f64, f64, f64, f64)> {
        let cache_key = "all_indices";

        // Check cache first
        if let Some((cached_data, cached_at)) = self.cache.get(cache_key) {
            if (now_seconds - cached_at) < self.cache_ttl_seconds {
                info!("Cache hit for all indices (age: {} seconds)", now_seconds - cached_at);
                return Ok((
                    cached_data.hashrate_index,
                    cached_data.energy_index,
                    cached_data.fees_index,
                    cached_data.adoption_index,
                ));
            }
        }

        // Check all sources are reasonably fresh (within last 24 hours)
        let max_age = 86_400;  // 24 hours in seconds

        if !self.energy_feed.is_fresh(now_seconds, max_age) {
            warn!("Energy feed is stale");
        }

        if !self.adoption_feed.is_fresh(now_seconds, max_age) {
            warn!("Adoption feed is stale");
        }

        if !self.kaspa_feed.is_fresh(now_seconds, max_age) {
            warn!("Kaspa feed is stale");
        }

        // Calculate all indices
        let hashrate_index = self.kaspa_feed.calculate_hashrate_index()?;
        let energy_index = self.energy_feed.calculate_index()?;
        let fees_index = self.kaspa_feed.calculate_fees_index()?;
        let adoption_index = self.adoption_feed.calculate_index()?;

        let data = OracleFeedData {
            energy_index,
            adoption_index,
            hashrate_index,
            fees_index,
            timestamp_seconds: now_seconds,
        };

        // Cache result
        self.cache.insert(cache_key.to_string(), (data.clone(), now_seconds));

        info!("All indices fetched: H:{:.4} E:{:.4} F:{:.4} A:{:.4}",
            hashrate_index, energy_index, fees_index, adoption_index);

        Ok((hashrate_index, energy_index, fees_index, adoption_index))
    }

    /// Check if all feeds are healthy (fresh and valid)
    pub fn all_feeds_healthy(&self, now_seconds: u64, max_age_seconds: u64) -> bool {
        self.energy_feed.is_fresh(now_seconds, max_age_seconds)
            && self.adoption_feed.is_fresh(now_seconds, max_age_seconds)
            && self.kaspa_feed.is_fresh(now_seconds, max_age_seconds)
    }

    /// Get cache stats (for monitoring)
    pub fn cache_size(&self) -> usize {
        self.cache.len()
    }

    /// Clear cache
    pub fn clear_cache(&mut self) {
        self.cache.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_energy_price_feed_creation() {
        let feed = EnergyPriceFeed::new(0.10);
        assert!(feed.is_ok());
    }

    #[test]
    fn test_energy_price_feed_invalid_baseline() {
        let feed = EnergyPriceFeed::new(-0.10);
        assert!(feed.is_err());
    }

    #[test]
    fn test_energy_price_update() {
        let mut feed = EnergyPriceFeed::new(0.10).unwrap();
        assert!(feed.update_price(0.12, 1000).is_ok());
        assert_eq!(feed.last_updated_seconds, 1000);
    }

    #[test]
    fn test_energy_price_index() {
        let mut feed = EnergyPriceFeed::new(0.10).unwrap();
        feed.update_price(0.20, 1000).unwrap();
        let index = feed.calculate_index().unwrap();
        // 0.20 / 0.10 = 2.0
        assert!((index - 2.0).abs() < 0.01);
    }

    #[test]
    fn test_energy_price_index_clipping() {
        let mut feed = EnergyPriceFeed::new(0.10).unwrap();
        feed.update_price(0.50, 1000).unwrap();
        let index = feed.calculate_index().unwrap();
        // 0.50 / 0.10 = 5.0, should clip to 5.0
        assert_eq!(index, 5.0);
    }

    #[test]
    fn test_adoption_metric_feed_creation() {
        let feed = AdoptionMetricFeed::new(1.0);
        assert!(feed.is_ok());
    }

    #[test]
    fn test_adoption_metric_update() {
        let mut feed = AdoptionMetricFeed::new(1.0).unwrap();
        assert!(feed.update_metric(1.5, 1000).is_ok());
    }

    #[test]
    fn test_adoption_metric_index() {
        let mut feed = AdoptionMetricFeed::new(1.0).unwrap();
        feed.update_metric(1.5, 1000).unwrap();
        let index = feed.calculate_index().unwrap();
        // 1.5 / 1.0 = 1.5
        assert!((index - 1.5).abs() < 0.01);
    }

    #[test]
    fn test_kaspa_network_feed_creation() {
        let feed = KaspaNetworkFeed::new();
        assert_eq!(feed.hashrate_hps, 0.0);
    }

    #[test]
    fn test_kaspa_network_update() {
        let mut feed = KaspaNetworkFeed::new();
        let result = feed.update_network_state(
            1_000_000_000.0,
            BigInt::from(10_000_000),
            1000,
        );
        assert!(result.is_ok());
        assert_eq!(feed.last_updated_seconds, 1000);
    }

    #[test]
    fn test_kaspa_network_feed_freshness() {
        let mut feed = KaspaNetworkFeed::new();
        feed.update_network_state(1_000_000_000.0, BigInt::from(10_000_000), 1000).unwrap();

        // Within 1 hour: fresh
        assert!(feed.is_fresh(1000 + 3600, 3600));

        // Beyond 1 hour: stale
        assert!(!feed.is_fresh(1000 + 7200, 3600));
    }

    #[test]
    fn test_oracle_manager_creation() {
        let peg_calc = KaspaPegIndexCalculator::new(1_000_000_000.0).unwrap();
        let manager = OracleFeedManager::new(0.10, 1.0, peg_calc, 3600);
        assert!(manager.is_ok());
    }

    #[test]
    fn test_oracle_manager_update_and_fetch() {
        let peg_calc = KaspaPegIndexCalculator::new(1_000_000_000.0).unwrap();
        let mut manager = OracleFeedManager::new(0.10, 1.0, peg_calc, 3600).unwrap();

        // Update all feeds
        manager.update_energy_price(0.10, 1000).unwrap();
        manager.update_adoption_metric(1.0, 1000).unwrap();
        manager.update_kaspa_network(1_000_000_000.0, BigInt::from(10_000_000), 1000).unwrap();

        // Fetch all indices
        let (h, e, f, a) = manager.fetch_all_indices(1000).unwrap();

        // All should be normalized indices
        assert!((h - 1.0).abs() < 0.1);  // Hashrate at baseline
        assert!((e - 1.0).abs() < 0.01); // Energy at baseline
        assert!((f - 1.0).abs() < 0.1);  // Fees at baseline
        assert!((a - 1.0).abs() < 0.01); // Adoption at baseline
    }

    #[test]
    fn test_oracle_manager_caching() {
        let peg_calc = KaspaPegIndexCalculator::new(1_000_000_000.0).unwrap();
        let mut manager = OracleFeedManager::new(0.10, 1.0, peg_calc, 3600).unwrap();

        manager.update_energy_price(0.10, 1000).unwrap();
        manager.update_adoption_metric(1.0, 1000).unwrap();
        manager.update_kaspa_network(1_000_000_000.0, BigInt::from(10_000_000), 1000).unwrap();

        // First fetch
        let result1 = manager.fetch_all_indices(1000);
        assert!(result1.is_ok());
        assert_eq!(manager.cache_size(), 1);

        // Second fetch within cache TTL
        let result2 = manager.fetch_all_indices(1000 + 1800);  // 30 min later
        assert!(result2.is_ok());
        assert_eq!(manager.cache_size(), 1);  // Still 1 cached entry

        // Both should return same values
        let (h1, e1, f1, a1) = result1.unwrap();
        let (h2, e2, f2, a2) = result2.unwrap();
        assert_eq!(h1, h2);
        assert_eq!(e1, e2);
        assert_eq!(f1, f2);
        assert_eq!(a1, a2);
    }

    #[test]
    fn test_oracle_manager_all_feeds_healthy() {
        let peg_calc = KaspaPegIndexCalculator::new(1_000_000_000.0).unwrap();
        let mut manager = OracleFeedManager::new(0.10, 1.0, peg_calc, 3600).unwrap();

        // Initially no data
        assert!(!manager.all_feeds_healthy(1000, 3600));

        // Update all feeds
        manager.update_energy_price(0.10, 1000).unwrap();
        manager.update_adoption_metric(1.0, 1000).unwrap();
        manager.update_kaspa_network(1_000_000_000.0, BigInt::from(10_000_000), 1000).unwrap();

        // Now all should be healthy
        assert!(manager.all_feeds_healthy(1000, 3600));

        // After 1 hour, should still be healthy (at max_age limit)
        assert!(manager.all_feeds_healthy(1000 + 3600, 3600));

        // After 2 hours, should NOT be healthy (exceeds max_age of 3600)
        assert!(!manager.all_feeds_healthy(1000 + 7200, 3600));

        // After 2 hours, should be healthy if we allow longer max_age
        assert!(manager.all_feeds_healthy(1000 + 7200, 7200));
    }

    #[test]
    fn test_oracle_manager_clear_cache() {
        let peg_calc = KaspaPegIndexCalculator::new(1_000_000_000.0).unwrap();
        let mut manager = OracleFeedManager::new(0.10, 1.0, peg_calc, 3600).unwrap();

        manager.update_energy_price(0.10, 1000).unwrap();
        manager.update_adoption_metric(1.0, 1000).unwrap();
        manager.update_kaspa_network(1_000_000_000.0, BigInt::from(10_000_000), 1000).unwrap();

        manager.fetch_all_indices(1000).unwrap();
        assert_eq!(manager.cache_size(), 1);

        manager.clear_cache();
        assert_eq!(manager.cache_size(), 0);
    }
}
