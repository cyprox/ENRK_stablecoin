//! Peg price calculation engine
//!
//! Calculates ENRK price index from four independent, uncorrelated data sources:
//! - 40% Kaspa network hashrate (proof-of-work security)
//! - 30% Global energy price index (thermodynamic cost)
//! - 20% Kaspa network fees (economic utility)
//! - 10% Global crypto adoption (market maturity)
//!
//! Target: 1 ENRK = 1 kWh of thermodynamic value
//! No dependency on fiat currency (USD, EUR, etc.)

use crate::errors::{IgraError, IgraResult};
use crate::types::{OraclePrice, PegComponents, PegPrice, PegWeights};
use log::info;

/// Peg calculation engine
pub struct PegCalculator {
    weights: PegWeights,
}

impl PegCalculator {
    /// Create new peg calculator with frozen weights
    pub fn new(weights: PegWeights) -> IgraResult<Self> {
        weights.validate().map_err(|e| IgraError::InvalidParameters(e))?;
        Ok(Self { weights })
    }

    /// Calculate current ENRK peg price (target: 1.0)
    ///
    /// Formula: Peg = 0.40×H + 0.30×E + 0.20×F + 0.10×A
    /// Where:
    ///   H = Kaspa hashrate index (normalized to 1.0 baseline)
    ///   E = Global energy price index (normalized to 1.0 baseline)
    ///   F = Kaspa fees index (normalized to 1.0 baseline)
    ///   A = Crypto adoption index (normalized to 1.0 baseline)
    ///
    /// Returns PegPrice containing:
    ///   - value: weighted index (ideally 1.0, range [0.1, 5.0])
    ///   - components: breakdown of each index
    ///   - timestamp: when peg was calculated
    pub fn calculate(
        &self,
        hashrate_index: f64,
        energy_index: f64,
        fees_index: f64,
        adoption_index: f64,
        timestamp_seconds: u64,
    ) -> IgraResult<PegPrice> {
        // Validate all index inputs
        Self::validate_index("Hashrate", hashrate_index)?;
        Self::validate_index("Energy", energy_index)?;
        Self::validate_index("Fees", fees_index)?;
        Self::validate_index("Adoption", adoption_index)?;

        // Apply frozen weights
        let hashrate_component = hashrate_index * (self.weights.hashrate as f64 / 100.0);
        let energy_component = energy_index * (self.weights.energy as f64 / 100.0);
        let fees_component = fees_index * (self.weights.fees as f64 / 100.0);
        let adoption_component = adoption_index * (self.weights.adoption as f64 / 100.0);

        // Sum to get final peg price
        let peg_value = hashrate_component + energy_component + fees_component + adoption_component;

        // Clip to reasonable range to prevent numerical explosions
        let peg_clipped = peg_value.max(0.1).min(5.0);

        info!(
            "Peg calculated: {:.4} (H:{:.2} E:{:.2} F:{:.2} A:{:.2})",
            peg_clipped, hashrate_index, energy_index, fees_index, adoption_index
        );

        Ok(PegPrice {
            value: peg_clipped,
            timestamp_seconds,
            components: PegComponents {
                hashrate_index,
                energy_index,
                fees_index,
                adoption_index,
            },
        })
    }

    /// Calculate peg deviation from ideal 1.0 value
    /// Returns percentage deviation (e.g., -5 = 5% below peg, +8 = 8% above)
    pub fn peg_deviation(peg_price: f64) -> i16 {
        let ideal = 1.0;
        let deviation = ((peg_price - ideal) / ideal) * 100.0;
        deviation as i16
    }

    /// Check if peg is within acceptable bounds
    /// Returns true if deviation <= threshold_percent
    pub fn is_peg_healthy(peg_price: f64, threshold_percent: u8) -> bool {
        let deviation = Self::peg_deviation(peg_price).abs() as u8;
        deviation <= threshold_percent
    }

    /// Validate an index is in reasonable range [0.1, 5.0]
    fn validate_index(name: &str, value: f64) -> IgraResult<()> {
        if value.is_nan() {
            return Err(IgraError::InvalidPegComponent(format!(
                "{} index is NaN",
                name
            )));
        }
        if value.is_infinite() {
            return Err(IgraError::InvalidPegComponent(format!(
                "{} index is infinite",
                name
            )));
        }
        if value < 0.1 || value > 5.0 {
            return Err(IgraError::InvalidPegComponent(format!(
                "{} index out of range: {} (expected 0.1-5.0)",
                name, value
            )));
        }
        Ok(())
    }

    /// Get the frozen weights
    pub fn weights(&self) -> &PegWeights {
        &self.weights
    }
}

/// Oracle price feed integration
/// Manages multiple oracle sources with fallback strategy
pub struct OracleManager {
    last_prices: Vec<OraclePrice>,
}

impl OracleManager {
    pub fn new() -> Self {
        Self {
            last_prices: Vec::new(),
        }
    }

    /// Record price from oracle source
    /// Fallback order: Band → Chainlink → LastPrice
    pub fn record_price(&mut self, source: &str, value: f64, timestamp_seconds: u64) -> IgraResult<()> {
        // Validate price
        if value.is_nan() || value.is_infinite() || value <= 0.0 {
            return Err(IgraError::InvalidOraclePrice(format!(
                "Invalid price from {}: {}",
                source, value
            )));
        }

        // Remove old prices from same source
        self.last_prices.retain(|p| p.source != source);

        // Add new price
        self.last_prices.push(OraclePrice {
            value,
            timestamp_seconds,
            source: source.to_string(),
        });

        info!("Oracle recorded: {} = {} at {}", source, value, timestamp_seconds);
        Ok(())
    }

    /// Get price from highest-priority available source
    /// Returns: (price, source, freshness_seconds)
    pub fn get_price(&self, now_seconds: u64, max_age_seconds: u64) -> IgraResult<(f64, String, u64)> {
        // Preference order: Band > Chainlink > LastPrice
        let preference_order = vec!["band", "chainlink", "fallback"];

        for preferred_source in preference_order {
            for price in &self.last_prices {
                if price.source == preferred_source {
                    let age = now_seconds.saturating_sub(price.timestamp_seconds);
                    if age <= max_age_seconds {
                        return Ok((price.value, price.source.clone(), age));
                    }
                }
            }
        }

        // All sources stale or missing
        if !self.last_prices.is_empty() {
            let latest = self.last_prices.iter().max_by_key(|p| p.timestamp_seconds);
            if let Some(price) = latest {
                let age = now_seconds.saturating_sub(price.timestamp_seconds);
                return Err(IgraError::OracleDowntime {
                    minutes: (age / 60) as u16,
                    threshold: (max_age_seconds / 60) as u16,
                });
            }
        }

        Err(IgraError::PegPriceUnavailable)
    }

    /// Check all oracle sources are recent enough
    pub fn all_sources_healthy(&self, now_seconds: u64, max_age_seconds: u64) -> bool {
        self.last_prices.iter().all(|p| {
            let age = now_seconds.saturating_sub(p.timestamp_seconds);
            age <= max_age_seconds
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_peg_calculator_creation() {
        let weights = PegWeights::default();
        let calc = PegCalculator::new(weights);
        assert!(calc.is_ok());
    }

    #[test]
    fn test_peg_calculation_at_target() {
        let weights = PegWeights::default();
        let calc = PegCalculator::new(weights).unwrap();

        // All indices at 1.0 = perfect peg
        let peg = calc
            .calculate(1.0, 1.0, 1.0, 1.0, 1000)
            .unwrap();

        assert!((peg.value - 1.0).abs() < 0.01);
    }

    #[test]
    fn test_peg_calculation_weighted() {
        let weights = PegWeights::default();
        let calc = PegCalculator::new(weights).unwrap();

        // Hashrate up 10%, others at 1.0
        let peg = calc
            .calculate(1.1, 1.0, 1.0, 1.0, 1000)
            .unwrap();

        // Expected: 0.4 * 1.1 + 0.3 * 1.0 + 0.2 * 1.0 + 0.1 * 1.0 = 1.04
        assert!((peg.value - 1.04).abs() < 0.01);
    }

    #[test]
    fn test_peg_calculation_crisis() {
        let weights = PegWeights::default();
        let calc = PegCalculator::new(weights).unwrap();

        // Hashrate crash to 0.5, energy stable at 1.0
        let peg = calc
            .calculate(0.5, 1.0, 1.0, 1.0, 1000)
            .unwrap();

        // Expected: 0.4 * 0.5 + 0.3 + 0.2 + 0.1 = 0.8
        assert!((peg.value - 0.8).abs() < 0.01);
    }

    #[test]
    fn test_peg_deviation_calculation() {
        assert_eq!(PegCalculator::peg_deviation(1.0), 0);    // On peg
        assert_eq!(PegCalculator::peg_deviation(1.05), 5);   // 5% above
        assert_eq!(PegCalculator::peg_deviation(0.95), -5);  // 5% below
    }

    #[test]
    fn test_peg_health_check() {
        assert!(PegCalculator::is_peg_healthy(1.0, 10));    // On peg, healthy
        assert!(PegCalculator::is_peg_healthy(1.08, 10));   // 8% above, within 10% threshold
        assert!(!PegCalculator::is_peg_healthy(1.15, 10));  // 15% above, exceeds 10% threshold
    }

    #[test]
    fn test_peg_clipping_prevents_explosion() {
        let weights = PegWeights::default();
        let calc = PegCalculator::new(weights).unwrap();

        // Maximum valid values (5.0 each)
        // Result: 0.4*5.0 + 0.3*5.0 + 0.2*5.0 + 0.1*5.0 = 5.0
        let peg = calc
            .calculate(5.0, 5.0, 5.0, 5.0, 1000)
            .unwrap();

        // Should be exactly 5.0
        assert_eq!(peg.value, 5.0);
    }

    #[test]
    fn test_oracle_manager_recording() {
        let mut oracle = OracleManager::new();

        assert!(oracle.record_price("band", 50000.0, 1000).is_ok());
        assert!(oracle.record_price("chainlink", 50100.0, 1001).is_ok());
    }

    #[test]
    fn test_oracle_manager_fallback_order() {
        let mut oracle = OracleManager::new();

        oracle.record_price("chainlink", 100.0, 1000).unwrap();
        oracle.record_price("band", 101.0, 1000).unwrap();

        // Should prefer Band over Chainlink
        let (price, source, _age) = oracle.get_price(1000, 3600).unwrap();
        assert_eq!(source, "band");
        assert_eq!(price, 101.0);
    }

    #[test]
    fn test_oracle_manager_stale_detection() {
        let mut oracle = OracleManager::new();

        oracle.record_price("band", 100.0, 1000).unwrap();

        // 7200 seconds (2 hours) later, max_age is 3600 (1 hour)
        let result = oracle.get_price(1000 + 7200, 3600);
        assert!(result.is_err());
        assert!(matches!(result, Err(IgraError::OracleDowntime { .. })));
    }

    #[test]
    fn test_oracle_manager_invalid_price() {
        let mut oracle = OracleManager::new();

        // NaN price
        let result = oracle.record_price("band", f64::NAN, 1000);
        assert!(result.is_err());

        // Negative price
        let result = oracle.record_price("band", -100.0, 1000);
        assert!(result.is_err());

        // Zero price
        let result = oracle.record_price("band", 0.0, 1000);
        assert!(result.is_err());
    }
}
