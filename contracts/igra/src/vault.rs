//! Vault management system
//!
//! Implements over-collateralized CDP (Collateralized Debt Position) model
//! adapted from Liquity protocol, with dual-tranche architecture:
//! - ENRK: Senior tranche, stable, pegged to 1 kWh, unlimited supply
//! - kFIAT: Junior tranche, speculative, capped at 30% of total debt
//!
//! Key guarantees:
//! - All vaults must maintain ICR ≥ 200% (Individual Collateral Ratio)
//! - Vaults with ICR < 150% become liquidation-eligible
//! - ENRK is redeemable for KAS at peg rate (cost-of-production floor)
//! - kFIAT has no redemption guarantee (bears liquidation losses first)

use crate::errors::{IgraError, IgraResult};
use crate::types::{CollateralRatios, FeeStructure, Vault, VaultStatus};
use log::{debug, info, warn};
use num_bigint::BigInt;
use num_traits::cast::ToPrimitive;
use std::collections::HashMap;

/// Vault manager: handles creation, collateral management, minting/burning
pub struct VaultManager {
    vaults: HashMap<u64, Vault>,
    next_vault_id: u64,
    collateral_ratios: CollateralRatios,
    fees: FeeStructure,
    kfiat_cap_percent: u8,  // 30% of total debt
}

impl VaultManager {
    /// Create new vault manager with frozen parameters
    pub fn new(
        collateral_ratios: CollateralRatios,
        fees: FeeStructure,
        kfiat_cap_percent: u8,
    ) -> IgraResult<Self> {
        collateral_ratios.validate().map_err(|e| IgraError::InvalidParameters(e))?;
        fees.validate().map_err(|e| IgraError::InvalidParameters(e))?;

        if kfiat_cap_percent == 0 || kfiat_cap_percent > 50 {
            return Err(IgraError::InvalidParameters(
                "kFIAT cap must be 0 < x <= 50%".to_string(),
            ));
        }

        info!(
            "VaultManager initialized: ICR={}%, MCR={}%, kFIAT_cap={}%",
            collateral_ratios.icr_minimum, collateral_ratios.mcr_trigger, kfiat_cap_percent
        );

        Ok(Self {
            vaults: HashMap::new(),
            next_vault_id: 1,
            collateral_ratios,
            fees,
            kfiat_cap_percent,
        })
    }

    /// Create new vault for owner with initial collateral
    /// Generates unique vault_id, initializes with KAS collateral
    pub fn create_vault(&mut self, owner: &str, initial_collateral_kas: BigInt) -> IgraResult<u64> {
        if owner.is_empty() {
            return Err(IgraError::InvalidAddress("Owner address empty".to_string()));
        }

        if initial_collateral_kas <= BigInt::from(0) {
            return Err(IgraError::InvalidCollateralAmount);
        }

        let vault_id = self.next_vault_id;
        self.next_vault_id += 1;

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        let vault = Vault {
            vault_id,
            owner: owner.to_string(),
            collateral_kas: initial_collateral_kas.clone(),
            debt_enrk: BigInt::from(0),
            debt_kfiat: BigInt::from(0),
            status: VaultStatus::Active,
            created_at_seconds: now,
            last_updated_seconds: now,
        };

        self.vaults.insert(vault_id, vault);

        info!(
            "Vault created: id={}, owner={}, collateral={}",
            vault_id, owner, initial_collateral_kas
        );

        Ok(vault_id)
    }

    /// Get vault by ID (read-only)
    pub fn get_vault(&self, vault_id: u64) -> IgraResult<Vault> {
        self.vaults
            .get(&vault_id)
            .cloned()
            .ok_or(IgraError::VaultNotFound(vault_id))
    }

    /// Mint ENRK against vault collateral
    /// Checks:
    /// - Vault exists and is active
    /// - Resulting ICR ≥ ICR_minimum after mint
    /// - Debt > 0
    ///
    /// Applies mint fee (default 2% to ENRK amount)
    pub fn mint_enrk(
        &mut self,
        vault_id: u64,
        amount_enrk: BigInt,
        kas_price: f64,
        enrk_price: f64,
    ) -> IgraResult<BigInt> {
        if amount_enrk <= BigInt::from(0) {
            return Err(IgraError::InvalidDebtAmount);
        }

        let mut vault = self.get_vault(vault_id)?;

        if vault.status != VaultStatus::Active {
            return Err(IgraError::InvalidVaultStatus {
                status: format!("{:?}", vault.status),
            });
        }

        // Calculate mint fee (in ENRK)
        let fee_amount = Self::calculate_fee(&amount_enrk, self.fees.mint_fee_bps)?;
        let total_enrk_debt = amount_enrk.clone() + fee_amount.clone();

        // Update vault debt
        vault.debt_enrk = vault.debt_enrk.clone() + total_enrk_debt.clone();

        // Check new ICR is acceptable
        let icr = vault.calculate_icr(kas_price, enrk_price, 1.0);
        if (icr as u16) < self.collateral_ratios.icr_minimum {
            return Err(IgraError::InsufficientCollateral {
                required_icr: self.collateral_ratios.icr_minimum,
                current_icr: icr as u16,
            });
        }

        vault.last_updated_seconds = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        self.vaults.insert(vault_id, vault.clone());

        info!(
            "ENRK minted: vault={}, amount={}, fee={}, new_debt={}",
            vault_id, amount_enrk, fee_amount, vault.debt_enrk
        );

        Ok(fee_amount)
    }

    /// Mint kFIAT against vault collateral
    /// Checks:
    /// - Vault exists and is active
    /// - Resulting ICR ≥ ICR_minimum after mint
    /// - Total kFIAT across all vaults ≤ 30% of total ENRK + kFIAT debt
    pub fn mint_kfiat(
        &mut self,
        vault_id: u64,
        amount_kfiat: BigInt,
        kas_price: f64,
        enrk_price: f64,
        kfiat_price: f64,
    ) -> IgraResult<BigInt> {
        if amount_kfiat <= BigInt::from(0) {
            return Err(IgraError::InvalidDebtAmount);
        }

        let mut vault = self.get_vault(vault_id)?;

        if vault.status != VaultStatus::Active {
            return Err(IgraError::InvalidVaultStatus {
                status: format!("{:?}", vault.status),
            });
        }

        // Calculate mint fee
        let fee_amount = Self::calculate_fee(&amount_kfiat, self.fees.mint_fee_bps)?;
        let total_kfiat_debt = amount_kfiat.clone() + fee_amount.clone();

        // Check kFIAT cap: total kFIAT ≤ 30% of (ENRK + kFIAT)
        let total_existing_debt_enrk =
            self.vaults.values().map(|v| v.debt_enrk.clone()).sum::<BigInt>();
        let total_existing_debt_kfiat =
            self.vaults.values().map(|v| v.debt_kfiat.clone()).sum::<BigInt>();

        let new_total_kfiat = total_existing_debt_kfiat.clone() + total_kfiat_debt.clone();
        let new_total_debt = total_existing_debt_enrk.clone() + new_total_kfiat.clone();

        if new_total_debt > BigInt::from(0) {
            let kfiat_ratio = (new_total_kfiat.to_f64().unwrap_or(0.0)
                / new_total_debt.to_f64().unwrap_or(1.0))
                * 100.0;

            if kfiat_ratio > self.kfiat_cap_percent as f64 {
                return Err(IgraError::KFIATCapExceeded {
                    current_kfiat: kfiat_ratio as u64,
                    max_kfiat: self.kfiat_cap_percent as u64,
                });
            }
        }

        // Update vault
        vault.debt_kfiat = vault.debt_kfiat.clone() + total_kfiat_debt.clone();

        // Check ICR still healthy
        let icr = vault.calculate_icr(kas_price, enrk_price, kfiat_price);
        if (icr as u16) < self.collateral_ratios.icr_minimum {
            return Err(IgraError::InsufficientCollateral {
                required_icr: self.collateral_ratios.icr_minimum,
                current_icr: icr as u16,
            });
        }

        vault.last_updated_seconds = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        self.vaults.insert(vault_id, vault.clone());

        info!(
            "kFIAT minted: vault={}, amount={}, fee={}, new_debt={}",
            vault_id, amount_kfiat, fee_amount, vault.debt_kfiat
        );

        Ok(fee_amount)
    }

    /// Burn ENRK debt from vault
    /// Reduces debt and proportionally releases collateral
    pub fn burn_enrk(
        &mut self,
        vault_id: u64,
        amount_to_burn: BigInt,
        kas_price: f64,
        enrk_price: f64,
    ) -> IgraResult<()> {
        if amount_to_burn <= BigInt::from(0) {
            return Err(IgraError::InvalidDebtAmount);
        }

        let mut vault = self.get_vault(vault_id)?;

        if vault.debt_enrk < amount_to_burn {
            return Err(IgraError::InsufficientENRK);
        }

        vault.debt_enrk = vault.debt_enrk.clone() - amount_to_burn.clone();

        // After burn, check ICR is still adequate
        if vault.debt_enrk > BigInt::from(0) {
            let icr = vault.calculate_icr(kas_price, enrk_price, 1.0);
            if (icr as u16) < self.collateral_ratios.icr_minimum {
                warn!("After ENRK burn, vault ICR dropped below minimum");
                return Err(IgraError::InsufficientRemainingCollateral);
            }
        }

        vault.last_updated_seconds = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        self.vaults.insert(vault_id, vault);

        info!("ENRK burned: vault={}, amount={}", vault_id, amount_to_burn);

        Ok(())
    }

    /// Burn kFIAT debt from vault
    pub fn burn_kfiat(
        &mut self,
        vault_id: u64,
        amount_to_burn: BigInt,
        kas_price: f64,
        enrk_price: f64,
        kfiat_price: f64,
    ) -> IgraResult<()> {
        if amount_to_burn <= BigInt::from(0) {
            return Err(IgraError::InvalidDebtAmount);
        }

        let mut vault = self.get_vault(vault_id)?;

        if vault.debt_kfiat < amount_to_burn {
            return Err(IgraError::InsufficientBalance {
                required: amount_to_burn.to_u64().unwrap_or(u64::MAX),
                available: vault.debt_kfiat.to_u64().unwrap_or(0),
            });
        }

        vault.debt_kfiat = vault.debt_kfiat.clone() - amount_to_burn.clone();

        // After burn, check ICR is still adequate
        if vault.debt_enrk.clone() + vault.debt_kfiat.clone() > BigInt::from(0) {
            let icr = vault.calculate_icr(kas_price, enrk_price, kfiat_price);
            if (icr as u16) < self.collateral_ratios.icr_minimum {
                return Err(IgraError::InsufficientRemainingCollateral);
            }
        }

        vault.last_updated_seconds = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        self.vaults.insert(vault_id, vault);

        info!("kFIAT burned: vault={}, amount={}", vault_id, amount_to_burn);

        Ok(())
    }

    /// Deposit additional KAS collateral into vault
    pub fn deposit_collateral(&mut self, vault_id: u64, additional_kas: BigInt) -> IgraResult<()> {
        if additional_kas <= BigInt::from(0) {
            return Err(IgraError::InvalidCollateralAmount);
        }

        let mut vault = self.get_vault(vault_id)?;

        if vault.status != VaultStatus::Active {
            return Err(IgraError::InvalidVaultStatus {
                status: format!("{:?}", vault.status),
            });
        }

        vault.collateral_kas = vault.collateral_kas.clone() + additional_kas.clone();
        vault.last_updated_seconds = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        self.vaults.insert(vault_id, vault);

        debug!("Collateral deposited: vault={}, amount={}", vault_id, additional_kas);

        Ok(())
    }

    /// Withdraw KAS collateral from vault
    /// Checks remaining collateral maintains ICR ≥ MCR
    pub fn withdraw_collateral(
        &mut self,
        vault_id: u64,
        amount_kas: BigInt,
        kas_price: f64,
        enrk_price: f64,
        kfiat_price: f64,
    ) -> IgraResult<()> {
        if amount_kas <= BigInt::from(0) {
            return Err(IgraError::InvalidCollateralAmount);
        }

        let mut vault = self.get_vault(vault_id)?;

        if vault.status != VaultStatus::Active {
            return Err(IgraError::InvalidVaultStatus {
                status: format!("{:?}", vault.status),
            });
        }

        if vault.collateral_kas < amount_kas {
            return Err(IgraError::InsufficientBalance {
                required: amount_kas.to_u64().unwrap_or(u64::MAX),
                available: vault.collateral_kas.to_u64().unwrap_or(0),
            });
        }

        // Simulate withdrawal and check ICR
        vault.collateral_kas = vault.collateral_kas.clone() - amount_kas.clone();

        if vault.debt_enrk.clone() + vault.debt_kfiat.clone() > BigInt::from(0) {
            let icr = vault.calculate_icr(kas_price, enrk_price, kfiat_price);
            if (icr as u16) < self.collateral_ratios.mcr_trigger {
                return Err(IgraError::InsufficientRemainingCollateral);
            }
        }

        vault.last_updated_seconds = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        self.vaults.insert(vault_id, vault);

        debug!("Collateral withdrawn: vault={}, amount={}", vault_id, amount_kas);

        Ok(())
    }

    /// Close vault: burn all debt, withdraw all collateral
    pub fn close_vault(
        &mut self,
        vault_id: u64,
        _kas_price: f64,
        _enrk_price: f64,
        _kfiat_price: f64,
    ) -> IgraResult<()> {
        let mut vault = self.get_vault(vault_id)?;

        if vault.debt_enrk.clone() + vault.debt_kfiat.clone() > BigInt::from(0) {
            return Err(IgraError::VaultZeroDebt);
        }

        vault.status = VaultStatus::Closed;
        vault.last_updated_seconds = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        self.vaults.insert(vault_id, vault);

        info!("Vault closed: id={}", vault_id);

        Ok(())
    }

    /// Get all vaults under-collateralized (ICR < MCR)
    pub fn get_liquidation_candidates(
        &self,
        kas_price: f64,
        enrk_price: f64,
        kfiat_price: f64,
    ) -> Vec<Vault> {
        self.vaults
            .values()
            .filter(|v| {
                v.status == VaultStatus::Active
                    && v.is_under_collateralized(
                        kas_price,
                        enrk_price,
                        kfiat_price,
                        self.collateral_ratios.mcr_trigger,
                    )
            })
            .cloned()
            .collect()
    }

    /// Calculate fee amount from debt
    fn calculate_fee(debt: &BigInt, fee_bps: u16) -> IgraResult<BigInt> {
        let fee_factor = fee_bps as f64 / 10000.0;
        let debt_f64 = debt.to_f64().ok_or_else(|| {
            IgraError::FeeCalculationFailed("Debt too large to convert".to_string())
        })?;
        let fee_f64 = debt_f64 * fee_factor;

        if !fee_f64.is_finite() {
            return Err(IgraError::FeeCalculationFailed(
                "Fee calculation overflowed".to_string(),
            ));
        }

        Ok(BigInt::from(fee_f64 as u64))
    }

    /// Get vault count
    pub fn vault_count(&self) -> usize {
        self.vaults.len()
    }

    /// Get total ENRK debt across all vaults
    pub fn total_enrk_debt(&self) -> BigInt {
        self.vaults.values().map(|v| v.debt_enrk.clone()).sum()
    }

    /// Get total kFIAT debt across all vaults
    pub fn total_kfiat_debt(&self) -> BigInt {
        self.vaults.values().map(|v| v.debt_kfiat.clone()).sum()
    }

    /// Get total collateral across all vaults
    pub fn total_collateral(&self) -> BigInt {
        self.vaults.values().map(|v| v.collateral_kas.clone()).sum()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_manager() -> VaultManager {
        VaultManager::new(
            CollateralRatios::default(),
            FeeStructure::default(),
            30,
        )
        .unwrap()
    }

    #[test]
    fn test_vault_creation() {
        let mut manager = create_test_manager();

        let vault_id = manager
            .create_vault("addr_test", BigInt::from(100))
            .unwrap();
        assert_eq!(vault_id, 1);

        let vault = manager.get_vault(1).unwrap();
        assert_eq!(vault.collateral_kas, BigInt::from(100));
        assert_eq!(vault.debt_enrk, BigInt::from(0));
    }

    #[test]
    fn test_vault_creation_invalid_owner() {
        let mut manager = create_test_manager();
        let result = manager.create_vault("", BigInt::from(100));
        assert!(result.is_err());
    }

    #[test]
    fn test_mint_enrk() {
        let mut manager = create_test_manager();
        manager.create_vault("addr_test", BigInt::from(1000)).unwrap();

        let _fee = manager
            .mint_enrk(1, BigInt::from(100), 5.0, 1.0)
            .unwrap();

        let vault = manager.get_vault(1).unwrap();
        // Debt includes amount + fee
        assert!(vault.debt_enrk > BigInt::from(100));
    }

    #[test]
    fn test_collateral_deposit() {
        let mut manager = create_test_manager();
        manager.create_vault("addr_test", BigInt::from(100)).unwrap();

        manager
            .deposit_collateral(1, BigInt::from(50))
            .unwrap();

        let vault = manager.get_vault(1).unwrap();
        assert_eq!(vault.collateral_kas, BigInt::from(150));
    }

    #[test]
    fn test_total_debt_calculation() {
        let mut manager = create_test_manager();

        manager.create_vault("owner1", BigInt::from(1000)).unwrap();
        manager.create_vault("owner2", BigInt::from(1000)).unwrap();

        manager.mint_enrk(1, BigInt::from(100), 5.0, 1.0).unwrap();
        manager.mint_enrk(2, BigInt::from(50), 5.0, 1.0).unwrap();

        let total = manager.total_enrk_debt();
        assert!(total >= BigInt::from(150));
    }
}
