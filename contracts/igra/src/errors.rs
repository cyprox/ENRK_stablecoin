//! Error types for ENRK Igra protocol

use thiserror::Error;

/// All possible errors in the ENRK Igra stablecoin protocol
/// Immutable design means these error conditions cannot be overridden
#[derive(Error, Debug, Clone, PartialEq, Eq)]
pub enum IgraError {
    // ===== Vault Errors =====
    #[error("Vault not found: {0}")]
    VaultNotFound(u64),

    #[error("Vault already exists: {0}")]
    VaultAlreadyExists(u64),

    #[error("Insufficient collateral. Required ICR: {required_icr}%, current: {current_icr}%")]
    InsufficientCollateral { required_icr: u16, current_icr: u16 },

    #[error("Vault is not under-collateralized (ICR: {icr}% > MCR: {mcr}%)")]
    VaultNotUnderCollateralized { icr: u16, mcr: u16 },

    #[error("Cannot mint more than kFIAT cap. Current: {current_kfiat}%, Max: {max_kfiat}%")]
    KFIATCapExceeded {
        current_kfiat: u64,
        max_kfiat: u64,
    },

    #[error("Vault has zero debt")]
    VaultZeroDebt,

    #[error("Invalid collateral amount")]
    InvalidCollateralAmount,

    #[error("Invalid debt amount")]
    InvalidDebtAmount,

    #[error("Cannot withdraw collateral: would leave vault under MCR")]
    InsufficientRemainingCollateral,

    #[error("Vault status is {status}, cannot perform operation")]
    InvalidVaultStatus { status: String },

    // ===== Liquidation Errors =====
    #[error("Auction not found: {0}")]
    AuctionNotFound(u64),

    #[error("Auction already exists for vault: {0}")]
    AuctionAlreadyExists(u64),

    #[error("Auction has expired")]
    AuctionExpired,

    #[error("Auction is still active (not expired)")]
    AuctionStillActive,

    #[error("Bid amount {bid} is less than required {required} at current price {price}%")]
    BidTooLow { bid: u64, required: u64, price: u8 },

    #[error("Bid exceeds available collateral")]
    BidExceedsCollateral,

    #[error("No bidders for auction")]
    NoBiddersForAuction,

    #[error("Cannot liquidate: vault is healthy (ICR: {icr}% >= MCR: {mcr}%)")]
    VaultHealthy { icr: u16, mcr: u16 },

    // ===== Peg & Oracle Errors =====
    #[error("Peg price not available")]
    PegPriceUnavailable,

    #[error("Oracle feed offline for {minutes} minutes (threshold: {threshold})")]
    OracleDowntime { minutes: u16, threshold: u16 },

    #[error("Oracle price deviation exceeds {deviation}% threshold")]
    OraclePriceDeviation { deviation: u8 },

    #[error("Invalid oracle price: {0}")]
    InvalidOraclePrice(String),

    #[error("Cannot calculate peg: {0}")]
    PegCalculationFailed(String),

    #[error("Peg index component invalid: {0}")]
    InvalidPegComponent(String),

    // ===== Circuit Breaker Errors =====
    #[error("Protocol is paused: {reason}. Pause triggered at: {triggered_at_seconds}")]
    ProtocolPaused {
        reason: String,
        triggered_at_seconds: u64,
    },

    #[error("Peg deviation {deviation}% exceeds circuit breaker threshold {threshold}%")]
    CircuitBreakerTriggered { deviation: u8, threshold: u8 },

    // ===== Redemption Errors =====
    #[error("Insufficient ENRK for redemption")]
    InsufficientENRK,

    #[error("Redemption would break systemically sound vaults")]
    RedemptionWouldLiquidateHealthy,

    #[error("Redemption amount exceeds {max}")]
    RedemptionAmountTooLarge { max: u64 },

    #[error("Cannot redeem kFIAT: only ENRK can be redeemed")]
    CannotRedeemKFIAT,

    // ===== Fee & Stability Pool Errors =====
    #[error("Fee calculation failed: {0}")]
    FeeCalculationFailed(String),

    #[error("Stability pool balance insufficient")]
    StabilityPoolEmpty,

    #[error("Cannot trigger buyback: ENRK price still above peg")]
    PriceAbovePeg,

    #[error("Buyback would exceed stability pool balance")]
    BuybackExceedsPoolBalance,

    // ===== Permission & Access Errors =====
    #[error("Unauthorized: {0}")]
    Unauthorized(String),

    #[error("Invalid address: {0}")]
    InvalidAddress(String),

    #[error("Only vault owner can perform this action")]
    OnlyVaultOwner,

    // ===== Parameter Validation Errors =====
    #[error("Invalid parameters: {0}")]
    InvalidParameters(String),

    #[error("Parameter immutable: cannot modify {parameter} after deployment")]
    ParameterImmutable { parameter: String },

    #[error("Configuration validation failed: {0}")]
    ConfigurationInvalid(String),

    // ===== Transaction & State Errors =====
    #[error("Transaction failed: {0}")]
    TransactionFailed(String),

    #[error("State inconsistency detected: {0}")]
    StateInconsistency(String),

    #[error("Insufficient balance: required {required}, available {available}")]
    InsufficientBalance { required: u64, available: u64 },

    #[error("Overflow in calculation: {0}")]
    CalculationOverflow(String),

    #[error("Division by zero in {operation}")]
    DivisionByZero { operation: String },

    // ===== Generic Errors =====
    #[error("Operation failed: {0}")]
    OperationFailed(String),

    #[error("Unknown error: {0}")]
    Unknown(String),
}

/// Result type for Igra operations
pub type IgraResult<T> = Result<T, IgraError>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vault_not_found_error() {
        let err = IgraError::VaultNotFound(123);
        assert_eq!(err.to_string(), "Vault not found: 123");
    }

    #[test]
    fn test_insufficient_collateral_error() {
        let err = IgraError::InsufficientCollateral {
            required_icr: 200,
            current_icr: 150,
        };
        let msg = err.to_string();
        assert!(msg.contains("200"));
        assert!(msg.contains("150"));
    }

    #[test]
    fn test_circuit_breaker_triggered_error() {
        let err = IgraError::CircuitBreakerTriggered {
            deviation: 15,
            threshold: 10,
        };
        let msg = err.to_string();
        assert!(msg.contains("15"));
        assert!(msg.contains("10"));
    }

    #[test]
    fn test_protocol_paused_error() {
        let err = IgraError::ProtocolPaused {
            reason: "Peg deviation > 10%".to_string(),
            triggered_at_seconds: 1000,
        };
        let msg = err.to_string();
        assert!(msg.contains("Peg deviation"));
        assert!(msg.contains("1000"));
    }

    #[test]
    fn test_error_equality() {
        let err1 = IgraError::VaultNotFound(1);
        let err2 = IgraError::VaultNotFound(1);
        let err3 = IgraError::VaultNotFound(2);

        assert_eq!(err1, err2);
        assert_ne!(err1, err3);
    }
}
