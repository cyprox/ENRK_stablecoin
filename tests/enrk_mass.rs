//! Measure the cost of an ENRK oracle round transition.
//!
//! Two open questions:
//!
//!   - Question 2 of kaspanet/kips issue #46: the compute-mass ceiling on N,
//!     the number of price UTXOs one round transition can carry. Every input
//!     runs a covenant script, so compute mass - not storage mass - is the
//!     expected binding constraint.
//!
//!   - The KIP-9 asymmetry claimed in L1-Native-Reduced-Spec section 2.4: a
//!     falling price is said to cost storage mass proportional to N and to the
//!     depth of the fall. That claim only applies to variant A, where the price
//!     is the amount. Variant B keeps amounts constant, so it should cost
//!     nothing. This has never been measured, only derived.
//!
//! Run:
//!   ENRK_ORACLE=examples/enrk/a/oracle.ag cargo test --test enrk_mass -- --nocapture
//!   ENRK_ORACLE=examples/enrk/b/oracle.ag cargo test --test enrk_mass -- --nocapture

use std::collections::BTreeMap;

use argent::builder::{ArtifactValue, EntryCall, TxBuilder, TxContext};
use kaspa_consensus_core::{
    Hash,
    config::params::MAINNET_PARAMS,
    mass::{MassCalculator, UtxoCell, calc_storage_mass},
    tx::{CovenantBinding, PopulatedTransaction, TransactionId, TransactionOutpoint, UtxoEntry},
};

/// Value locked in each price UTXO. In variant A this is the price itself.
const UTXO_VALUE: u64 = 100_000_000;

const LADDER: [usize; 11] = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024];

fn oracle_source() -> String {
    std::env::var("ENRK_ORACLE").unwrap_or_else(|_| "examples/enrk/a/oracle.ag".to_string())
}

/// Variant B carries an extra `price` state field; variant A does not.
fn price_in_state(source: &str) -> bool {
    source.contains("/b/")
}

fn round_state(source: &str, round: i64, price: i64) -> BTreeMap<String, ArtifactValue> {
    let mut state = BTreeMap::new();
    state.insert("publisher".to_string(), ArtifactValue::Bytes(vec![0x11; 32]));
    state.insert("round".to_string(), ArtifactValue::Int(round));
    if price_in_state(source) {
        state.insert("price".to_string(), ArtifactValue::Int(price));
    }
    state
}

fn outpoint(index: usize) -> TransactionOutpoint {
    let mut bytes = [0u8; 32];
    bytes[0..8].copy_from_slice(&(index as u64).to_le_bytes());
    TransactionOutpoint::new(TransactionId::from_bytes(bytes), 0)
}

/// N price UTXOs consumed and N recreated unchanged, each input running the
/// open `use` branch. This is the shape of a round transition that does not
/// change the price, and the shape whose N we need to bound.
#[test]
fn oracle_round_scaling() {
    let source = oracle_source();
    let out_dir = std::env::temp_dir().join("enrk_mass_oracle");
    let artifact = argent::build_file(&source, &out_dir).expect("oracle app compiles");
    let builder = TxBuilder::new(&artifact).expect("builder accepts oracle artifact");

    let covenant_id = Hash::from_bytes([0x42; 32]);
    let state = round_state(&source, 1, 100);
    let calculator = MassCalculator::new_with_consensus_params(&MAINNET_PARAMS);
    let limits = MAINNET_PARAMS.block_mass_limits().after();

    println!("\nsource: {source}");
    println!("limits: compute {} / transient {} / storage {}", limits.compute, limits.transient, limits.storage);
    println!("{:>6}  {:>12}  {:>12}  {:>12}  {:>10}", "N", "compute", "transient", "storage", "sigscript");

    for n in LADDER {
        let mut context = TxContext::new();
        let mut entries: Vec<UtxoEntry> = Vec::with_capacity(n);

        for index in 0..n {
            let utxo = builder
                .covenant_utxo("PriceRound", state.clone(), UTXO_VALUE, 0, false, Some(covenant_id))
                .expect("price utxo builds");
            entries.push(utxo.clone());
            context = context.actor_input("PriceRound", state.clone(), EntryCall::new("use"), outpoint(index), utxo, 0);
        }
        for _ in 0..n {
            context = context.actor_output("PriceRound", state.clone(), CovenantBinding::new(0, covenant_id), UTXO_VALUE);
        }

        match builder.build(&context) {
            Ok(transaction) => {
                let non_contextual = calculator.calc_non_contextual_masses(&transaction);
                let populated = PopulatedTransaction::new(&transaction, entries);
                let storage = calculator.calc_contextual_masses(&populated).map(|masses| masses.storage_mass);
                let sigscript: usize = transaction.inputs.iter().map(|input| input.signature_script.len()).sum();
                println!(
                    "{n:>6}  {:>12}  {:>12}  {:>12}  {sigscript:>10}",
                    non_contextual.compute_mass,
                    non_contextual.transient_mass,
                    storage.map(|mass| mass.to_string()).unwrap_or_else(|| "incomputable".to_string()),
                );
            }
            Err(error) => {
                println!("{n:>6}  FAILED: {error}");
                break;
            }
        }
    }
}

/// Storage mass depends only on input and output amounts, so the KIP-9
/// asymmetry can be measured exactly without building a transaction.
///
/// `k` is the per-round price ratio: 1.0 is a flat round, below 1.0 is a
/// falling price. Variant A must pay this. Variant B always runs at k = 1.0
/// because its amounts never move, so its column is the k = 1.0 row.
#[test]
fn storage_mass_by_price_ratio() {
    let parameter = MAINNET_PARAMS.storage_mass_parameter;
    let limits = MAINNET_PARAMS.block_mass_limits().after();

    println!("\nstorage mass parameter: {parameter}");
    println!("storage limit per block: {}", limits.storage);
    println!("{:>6}  {:>12}  {:>12}  {:>12}  {:>12}", "N", "k=1.00", "k=0.99", "k=0.90", "k=0.50");

    for n in LADDER {
        let mut row = String::new();
        for ratio in [1.0_f64, 0.99, 0.90, 0.50] {
            let output_value = (UTXO_VALUE as f64 * ratio) as u64;
            let inputs: Vec<UtxoCell> = (0..n).map(|_| UtxoCell::new(1, UTXO_VALUE)).collect();
            let outputs: Vec<UtxoCell> = (0..n).map(|_| UtxoCell::new(1, output_value)).collect();
            let mass = calc_storage_mass(false, inputs.into_iter(), outputs.into_iter(), parameter);
            row.push_str(&format!("  {:>12}", mass.map(|m| m.to_string()).unwrap_or_else(|| "none".to_string())));
        }
        println!("{n:>6}{row}");
    }
}
