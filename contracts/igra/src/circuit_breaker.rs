//! Circuit Breaker: Emergency protocol safeguard
//!
//! Immutable safety mechanism that automatically pauses the protocol if:
//! 1. Peg deviates >10% from target (1.0 kWh)
//! 2. Oracle feeds go down for >6 hours
//!
//! Key properties:
//! - NO governance override possible
//! - NO admin keys can unlock it
//! - Pause persists until manual resolution (community fork if needed)
//! - Prevents cascading failures during extreme conditions
//!
//! Design philosophy:
//! - Better to pause and defend integrity than keep running and lose trust
//! - Immutability means this protection cannot be disabled by corrupt governance
//! - Aligns incentives: oracle operators know they must be reliable or protocol pauses

use crate::errors::{IgraError, IgraResult};
use crate::types::CircuitBreakerParams;
use log::{error, info};

/// Circuit breaker state machine
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CircuitBreakerState {
    Active,   // Normal operation
    Paused,   // Emergency pause triggered
}

/// Circuit breaker manager
pub struct CircuitBreaker {
    state: CircuitBreakerState,
    params: CircuitBreakerParams,
    pause_reason: String,
    pause_triggered_at: u64,
    last_peg_check: u64,
    last_oracle_health_check: u64,
}

impl CircuitBreaker {
    /// Create new circuit breaker with frozen parameters
    pub fn new(params: CircuitBreakerParams) -> IgraResult<Self> {
        params.validate().map_err(|e| IgraError::InvalidParameters(e))?;

        info!(
            "CircuitBreaker initialized: peg_threshold={}%, oracle_downtime_threshold={}min",
            params.peg_deviation_threshold, params.oracle_downtime_threshold_minutes
        );

        Ok(Self {
            state: CircuitBreakerState::Active,
            params,
            pause_reason: String::new(),
            pause_triggered_at: 0,
            last_peg_check: 0,
            last_oracle_health_check: 0,
        })
    }

    /// Get current state
    pub fn is_active(&self) -> bool {
        self.state == CircuitBreakerState::Active
    }

    /// Get pause details
    pub fn pause_details(&self) -> (bool, String, u64) {
        (
            self.state == CircuitBreakerState::Paused,
            self.pause_reason.clone(),
            self.pause_triggered_at,
        )
    }

    /// Check peg deviation and trigger pause if necessary
    /// Returns Err if breach detected and pause triggered
    ///
    /// Peg deviation = ((current_price - 1.0) / 1.0) * 100%
    /// Triggers if |deviation| > threshold (default 10%)
    pub fn check_peg_deviation(&mut self, current_peg_price: f64) -> IgraResult<()> {
        let deviation = ((current_peg_price - 1.0) / 1.0) * 100.0;
        let abs_deviation = deviation.abs() as u8;

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        self.last_peg_check = now;

        // Check if breach
        if abs_deviation > self.params.peg_deviation_threshold {
            self.trigger_pause(
                format!(
                    "Peg deviation {}% exceeds threshold {}%",
                    abs_deviation, self.params.peg_deviation_threshold
                ),
                now,
            );

            return Err(IgraError::CircuitBreakerTriggered {
                deviation: abs_deviation,
                threshold: self.params.peg_deviation_threshold,
            });
        }

        Ok(())
    }

    /// Check oracle health and trigger pause if down too long
    /// last_oracle_update_seconds = when last oracle price was received
    ///
    /// Triggers if (now - last_update) > threshold (default 6 hours)
    pub fn check_oracle_health(&mut self, last_oracle_update_seconds: u64) -> IgraResult<()> {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        self.last_oracle_health_check = now;

        let downtime_minutes = ((now - last_oracle_update_seconds) / 60) as u16;

        // Check if exceeded threshold
        if downtime_minutes > self.params.oracle_downtime_threshold_minutes {
            self.trigger_pause(
                format!(
                    "Oracle offline for {} minutes (threshold: {})",
                    downtime_minutes, self.params.oracle_downtime_threshold_minutes
                ),
                now,
            );

            return Err(IgraError::OracleDowntime {
                minutes: downtime_minutes,
                threshold: self.params.oracle_downtime_threshold_minutes,
            });
        }

        Ok(())
    }

    /// Manually check if protocol should be paused before operation
    /// This is called before any state-changing operation
    pub fn require_active(&self) -> IgraResult<()> {
        if self.state == CircuitBreakerState::Paused {
            return Err(IgraError::ProtocolPaused {
                reason: self.pause_reason.clone(),
                triggered_at_seconds: self.pause_triggered_at,
            });
        }
        Ok(())
    }

    /// INTERNAL: Trigger pause (no override possible)
    fn trigger_pause(&mut self, reason: String, timestamp: u64) {
        self.state = CircuitBreakerState::Paused;
        self.pause_reason = reason.clone();
        self.pause_triggered_at = timestamp;

        error!(
            "CIRCUIT BREAKER TRIGGERED: {} at {}",
            reason, timestamp
        );
    }

    /// Get params
    pub fn params(&self) -> &CircuitBreakerParams {
        &self.params
    }

    /// Get diagnostics (for debugging/monitoring)
    pub fn diagnostics(&self) -> CircuitBreakerDiagnostics {
        CircuitBreakerDiagnostics {
            is_active: self.is_active(),
            pause_reason: self.pause_reason.clone(),
            pause_triggered_at: self.pause_triggered_at,
            last_peg_check: self.last_peg_check,
            last_oracle_health_check: self.last_oracle_health_check,
            peg_threshold: self.params.peg_deviation_threshold,
            oracle_downtime_threshold: self.params.oracle_downtime_threshold_minutes,
        }
    }
}

#[derive(Debug, Clone)]
pub struct CircuitBreakerDiagnostics {
    pub is_active: bool,
    pub pause_reason: String,
    pub pause_triggered_at: u64,
    pub last_peg_check: u64,
    pub last_oracle_health_check: u64,
    pub peg_threshold: u8,
    pub oracle_downtime_threshold: u16,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_circuit_breaker_creation() {
        let cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();
        assert!(cb.is_active());
    }

    #[test]
    fn test_peg_deviation_within_threshold() {
        let mut cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();

        // Price at 1.05 (5% above peg, within 10% threshold)
        let result = cb.check_peg_deviation(1.05);
        assert!(result.is_ok());
        assert!(cb.is_active());
    }

    #[test]
    fn test_peg_deviation_exceeds_threshold() {
        let mut cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();

        // Price at 1.15 (15% above peg, exceeds 10% threshold)
        let result = cb.check_peg_deviation(1.15);
        assert!(result.is_err());
        assert!(!cb.is_active());
    }

    #[test]
    fn test_peg_deviation_negative() {
        let mut cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();

        // Price at 0.85 (15% below peg)
        let result = cb.check_peg_deviation(0.85);
        assert!(result.is_err());
        assert!(!cb.is_active());
    }

    #[test]
    fn test_peg_deviation_at_boundary() {
        let mut cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();

        // Price at exactly 1.10 (10% above, at threshold)
        let result = cb.check_peg_deviation(1.10);
        assert!(result.is_ok());  // At threshold is OK, exceeding is not
        assert!(cb.is_active());
    }

    #[test]
    fn test_oracle_health_recent_update() {
        let mut cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        // Oracle updated 1 hour ago (threshold is 6 hours)
        let last_update = now - 3600;

        let result = cb.check_oracle_health(last_update);
        assert!(result.is_ok());
        assert!(cb.is_active());
    }

    #[test]
    fn test_oracle_health_stale() {
        let mut cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        // Oracle went down 7 hours ago (threshold is 6 hours)
        let last_update = now - (7 * 3600);

        let result = cb.check_oracle_health(last_update);
        assert!(result.is_err());
        assert!(!cb.is_active());
    }

    #[test]
    fn test_oracle_health_boundary() {
        let mut cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        // Oracle updated exactly 6 hours ago
        let last_update = now - (6 * 3600);

        let result = cb.check_oracle_health(last_update);
        assert!(result.is_ok());
        assert!(cb.is_active());
    }

    #[test]
    fn test_require_active_when_paused() {
        let mut cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();

        // Trigger pause
        cb.check_peg_deviation(1.20).ok();

        let result = cb.require_active();
        assert!(result.is_err());
        assert!(matches!(result, Err(IgraError::ProtocolPaused { .. })));
    }

    #[test]
    fn test_require_active_when_normal() {
        let cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();

        let result = cb.require_active();
        assert!(result.is_ok());
    }

    #[test]
    fn test_pause_details() {
        let mut cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();

        cb.check_peg_deviation(1.20).ok();

        let (paused, reason, _triggered) = cb.pause_details();
        assert!(paused);
        assert!(reason.contains("Peg deviation"));
    }

    #[test]
    fn test_diagnostics() {
        let mut cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();

        cb.check_peg_deviation(1.05).ok();

        let diag = cb.diagnostics();
        assert!(diag.is_active);
        assert_eq!(diag.peg_threshold, 10);
    }

    #[test]
    fn test_multiple_checks() {
        let mut cb = CircuitBreaker::new(CircuitBreakerParams::default()).unwrap();

        // Check 1: Peg is OK
        cb.check_peg_deviation(1.05).ok();
        assert!(cb.is_active());

        // Check 2: Still OK
        cb.check_peg_deviation(1.08).ok();
        assert!(cb.is_active());

        // Check 3: Exceeds threshold
        cb.check_peg_deviation(1.15).ok();
        assert!(!cb.is_active());
    }
}
