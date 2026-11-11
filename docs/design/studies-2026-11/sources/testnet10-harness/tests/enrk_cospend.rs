//! Scratch test (NOT part of the repository): does a liquidation transaction that
//! co-spends an ENRK vault and an ENRK oracle price UTXO pass the real Kaspa
//! script engine?
//!
//!   COSPEND_DIR=<dir with vault.ag + oracle.ag> cargo test --test enrk_cospend -- --nocapture

use std::collections::BTreeMap;

use argent::builder::args;
use argent::builder::{ArtifactBundle, ArtifactValue, EntryCall, TxBuilder, TxContext};
use kaspa_consensus_core::{
    hashing::{
        sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash},
        sighash_type::SIG_HASH_ALL,
    },
    tx::{MutableTransaction, Transaction},
};
use secp256k1::{Keypair, Secp256k1, SecretKey};

fn keypair() -> Keypair {
    let secp = Secp256k1::new();
    Keypair::from_secret_key(&secp, &SecretKey::from_slice(&[9u8; 32]).unwrap())
}

fn sign_input<T: AsRef<Transaction>>(tx: &MutableTransaction<T>, input_idx: usize, kp: &Keypair) -> Vec<u8> {
    let reused = SigHashReusedValuesUnsync::new();
    let h = calc_schnorr_signature_hash(&tx.as_verifiable(), input_idx, SIG_HASH_ALL, &reused);
    let msg = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
    let mut sig = kp.sign_schnorr(msg).as_ref().to_vec();
    sig.push(SIG_HASH_ALL.to_u8());
    sig
}
use kaspa_consensus_core::{
    Hash,
    tx::{CovenantBinding, TransactionId, TransactionOutpoint},
};

const PRICE: u64 = 100_000_000; // oracle UTXO value = price (variant A)

fn outpoint(tag: u8) -> TransactionOutpoint {
    TransactionOutpoint::new(TransactionId::from_bytes([tag; 32]), 0)
}

fn oracle_state() -> BTreeMap<String, ArtifactValue> {
    let mut s = BTreeMap::new();
    s.insert("publisher".to_string(), ArtifactValue::Bytes(vec![0x11; 32]));
    s.insert("round".to_string(), ArtifactValue::Int(1));
    if std::env::var("COSPEND_B").is_ok() {
        s.insert("price".to_string(), ArtifactValue::Int(PRICE as i64));
    }
    s
}

fn vault_state(oracle_id: Hash, debt: i64) -> BTreeMap<String, ArtifactValue> {
    let mut s = BTreeMap::new();
    s.insert("owner".to_string(), ArtifactValue::Bytes(vec![0x22; 32]));
    s.insert("oracle_covid".to_string(), ArtifactValue::Bytes(oracle_id.as_bytes().to_vec()));
    s.insert("debt".to_string(), ArtifactValue::Int(debt));
    s
}

fn run(entry: &str, collateral: u64, debt: i64, declare_oracle_output: bool) {
    run_case("case", entry, collateral, debt, declare_oracle_output, false);
}

fn run_case(label: &str, entry: &str, collateral: u64, debt: i64, declare_oracle_output: bool, forged: bool) {
    let dir = std::env::var("COSPEND_DIR").expect("COSPEND_DIR");
    let out = std::env::temp_dir().join(format!("enrk_cospend_{}", std::process::id()));
    let vault_artifact = argent::build_file(format!("{dir}/vault.ag"), &out.join("v")).expect("vault compiles");
    let oracle_artifact = argent::build_file(format!("{dir}/oracle.ag"), &out.join("o")).expect("oracle compiles");
    let bundle = ArtifactBundle::new(&vault_artifact).expect("bundle").with_app("oracle_feed", &oracle_artifact).expect("with oracle app");
    let builder = TxBuilder::from_bundle(&bundle).expect("builder");

    let oracle_id = Hash::from_bytes([0x42; 32]);
    let vault_id = Hash::from_bytes([0x77; 32]);
    let ostate = oracle_state();
    // forged: the vault points at a different oracle covenant id than the one co-spent
    let vstate = vault_state(if forged { Hash::from_bytes([0x99; 32]) } else { oracle_id }, debt);

    let vault_utxo = builder.covenant_utxo("Vault", vstate.clone(), collateral, 0, false, Some(vault_id)).expect("vault utxo");
    let oracle_utxo = builder
        .covenant_utxo("oracle_feed::PriceRound", ostate.clone(), PRICE, 0, false, Some(oracle_id))
        .expect("oracle utxo");

    let mut ctx = TxContext::new()
        .actor_input("Vault", vstate.clone(), EntryCall::new(entry), outpoint(1), vault_utxo, 0)
        .actor_input("oracle_feed::PriceRound", ostate.clone(), EntryCall::new("use"), outpoint(2), oracle_utxo, 0);
    // The oracle `use` branch must recreate its output. Binding index = authorizing input (1).
    ctx = ctx.actor_output("oracle_feed::PriceRound", ostate.clone(), CovenantBinding::new(1, oracle_id), PRICE);
    let _ = declare_oracle_output;

    match builder.build(&ctx) {
        Ok(_) => println!("RESULT [{label}] {entry}: ACCEPTED by script engine"),
        Err(e) => println!("RESULT [{label}] {entry}: REJECTED: {e}"),
    }
}

#[test]
fn negative_cases() {
    // forged oracle id: vault points elsewhere than the co-spent oracle
    run_case("forged-oracle-id", "liquidate", 1_000_000, 1_000_000, true, true);
    // debt == 0 : icr_percent divides by zero
    run_case("debt-zero", "liquidate", 1_000_000, 0, true, false);
    // liquidatable (ICR 10%) but collateral*price*100 overflows i64 (1e12*1e8*100 = 1e22)
    run_case("overflow-liquidatable", "liquidate", 1_000_000_000_000, 10_000_000_000_000, true, false);
    // expression is (collateral*price*100)/SCALE/debt: bound is collateral*1e8*100 <= 9.22e18, i.e. 9.2e8 sompi (9.2 KAS)
    run_case("9-KAS-ICR90", "liquidate", 900_000_000, 1_000_000_000, true, false);
    run_case("10-KAS-ICR50", "liquidate", 1_000_000_000, 2_000_000_000, true, false);
}

#[test]
fn liquidate_cospend() {
    // collateral 1_000_000 sompi at price 1e8, debt 1_000_000 -> ICR 100% < 150% => liquidatable
    run("liquidate", 1_000_000, 1_000_000, true);
}

#[test]
fn liquidate_cospend_healthy_vault_must_fail() {
    // ICR 1000% : liquidate must be rejected on the ICR check, not on shape.
    run("liquidate", 1_000_000, 10_000, true);
}

#[test]
fn withdraw_cospend() {
    let dir = std::env::var("COSPEND_DIR").expect("COSPEND_DIR");
    let out = std::env::temp_dir().join(format!("enrk_withdraw_{}", std::process::id()));
    let vault_artifact = argent::build_file(format!("{dir}/vault.ag"), &out.join("v")).expect("vault compiles");
    let oracle_artifact = argent::build_file(format!("{dir}/oracle.ag"), &out.join("o")).expect("oracle compiles");
    let bundle = ArtifactBundle::new(&vault_artifact).unwrap().with_app("oracle_feed", &oracle_artifact).unwrap();
    let builder = TxBuilder::from_bundle(&bundle).unwrap();
    let owner = keypair();
    let owner_pk = owner.x_only_public_key().0.serialize().to_vec();
    let oracle_id = Hash::from_bytes([0x42; 32]);
    let vault_id = Hash::from_bytes([0x77; 32]);
    let ostate = oracle_state();
    let mk = |debt: i64| {
        let mut s = vault_state(oracle_id, debt);
        s.insert("owner".to_string(), ArtifactValue::Bytes(owner_pk.clone()));
        s
    };
    // collateral 5 KAS at price 1.0, debt 1e8 sompi-units... ICR must stay >= 200 after withdrawing 1e8
    let (collateral, withdrawn, debt) = (500_000_000u64, 100_000_000u64, 100_000_000i64);
    let vstate = mk(debt);
    let vault_utxo = builder.covenant_utxo("Vault", vstate.clone(), collateral, 0, false, Some(vault_id)).unwrap();
    let oracle_utxo = builder.covenant_utxo("oracle_feed::PriceRound", ostate.clone(), PRICE, 0, false, Some(oracle_id)).unwrap();
    let ctx = TxContext::new()
        .actor_input(
            "Vault",
            vstate.clone(),
            EntryCall::new("withdraw").args_with(move |tx, input_idx| args![sign_input(tx, input_idx, &keypair()), withdrawn as i64]),
            outpoint(1),
            vault_utxo,
            0,
        )
        .actor_input("oracle_feed::PriceRound", ostate.clone(), EntryCall::new("use"), outpoint(2), oracle_utxo, 0)
        .actor_output("Vault", vstate.clone(), CovenantBinding::new(0, vault_id), collateral - withdrawn)
        .actor_output("oracle_feed::PriceRound", ostate.clone(), CovenantBinding::new(1, oracle_id), PRICE);
    match builder.build(&ctx) {
        Ok(_) => println!("RESULT [withdraw] ACCEPTED by script engine"),
        Err(e) => println!("RESULT [withdraw] REJECTED: {e}"),
    }
}

// ---------------------------------------------------------------------------
// Additional cases: withdrawal boundary, price tampering, publisher sweep, mass
// ---------------------------------------------------------------------------

fn is_b() -> bool {
    std::env::var("COSPEND_B").is_ok()
}

fn mk_builder() -> TxBuilder<'static> {
    let dir = std::env::var("COSPEND_DIR").expect("COSPEND_DIR");
    let out = std::env::temp_dir().join(format!("enrk_x_{}_{}", std::process::id(), rand_tag()));
    let v = Box::leak(Box::new(argent::build_file(format!("{dir}/vault.ag"), &out.join("v")).expect("vault compiles")));
    let o = Box::leak(Box::new(argent::build_file(format!("{dir}/oracle.ag"), &out.join("o")).expect("oracle compiles")));
    let bundle = ArtifactBundle::new(&*v).unwrap().with_app("oracle_feed", &*o).unwrap();
    TxBuilder::from_bundle(&bundle).unwrap()
}

fn rand_tag() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos() as u64
}

fn pk() -> Vec<u8> {
    keypair().x_only_public_key().0.serialize().to_vec()
}

fn ostate_with(round: i64, price: i64) -> BTreeMap<String, ArtifactValue> {
    let mut s = BTreeMap::new();
    s.insert("publisher".to_string(), ArtifactValue::Bytes(pk()));
    s.insert("round".to_string(), ArtifactValue::Int(round));
    if is_b() {
        s.insert("price".to_string(), ArtifactValue::Int(price));
    }
    s
}

fn vstate_owner(oracle_id: Hash, debt: i64) -> BTreeMap<String, ArtifactValue> {
    let mut s = vault_state(oracle_id, debt);
    s.insert("owner".to_string(), ArtifactValue::Bytes(pk()));
    s
}

fn withdraw_case(label: &str, collateral: u64, withdrawn: u64, debt: i64) {
    let builder = mk_builder();
    let oracle_id = Hash::from_bytes([0x42; 32]);
    let vault_id = Hash::from_bytes([0x77; 32]);
    let ostate = ostate_with(1, PRICE as i64);
    let vstate = vstate_owner(oracle_id, debt);
    let vault_utxo = builder.covenant_utxo("Vault", vstate.clone(), collateral, 0, false, Some(vault_id)).unwrap();
    let oracle_utxo = builder.covenant_utxo("oracle_feed::PriceRound", ostate.clone(), PRICE, 0, false, Some(oracle_id)).unwrap();
    let ctx = TxContext::new()
        .actor_input(
            "Vault",
            vstate.clone(),
            EntryCall::new("withdraw").args_with(move |tx, i| args![sign_input(tx, i, &keypair()), withdrawn as i64]),
            outpoint(1),
            vault_utxo,
            0,
        )
        .actor_input("oracle_feed::PriceRound", ostate.clone(), EntryCall::new("use"), outpoint(2), oracle_utxo, 0)
        .actor_output("Vault", vstate.clone(), CovenantBinding::new(0, vault_id), collateral - withdrawn)
        .actor_output("oracle_feed::PriceRound", ostate.clone(), CovenantBinding::new(1, oracle_id), PRICE);
    match builder.build(&ctx) {
        Ok(_) => println!("RESULT [{label}] ACCEPTED"),
        Err(e) => println!("RESULT [{label}] REJECTED: {e}"),
    }
}

#[test]
fn withdraw_boundaries() {
    // debt 1e8, price 1.0 => ICR = remaining_collateral / 1e8 * 100
    withdraw_case("withdraw-to-exactly-200pct", 300_000_000, 100_000_000, 100_000_000);
    withdraw_case("withdraw-to-199pct (must reject)", 300_000_000, 101_000_000, 100_000_000);
    withdraw_case("withdraw-to-150pct (must reject)", 300_000_000, 150_000_000, 100_000_000);
    withdraw_case("withdraw-zero (must reject)", 300_000_000, 0, 100_000_000);
}

#[test]
fn price_tampering() {
    // An attacker co-spends the oracle through `use` but recreates it at a LOWER price,
    // to make a healthy vault liquidatable. Must be rejected.
    let builder = mk_builder();
    let oracle_id = Hash::from_bytes([0x42; 32]);
    let vault_id = Hash::from_bytes([0x77; 32]);
    let ostate = ostate_with(1, PRICE as i64);
    let vstate = vstate_owner(oracle_id, 10_000); // ICR 1000% at the true price
    let vault_utxo = builder.covenant_utxo("Vault", vstate.clone(), 1_000_000, 0, false, Some(vault_id)).unwrap();
    let oracle_utxo = builder.covenant_utxo("oracle_feed::PriceRound", ostate.clone(), PRICE, 0, false, Some(oracle_id)).unwrap();
    let (out_state, out_value) = if is_b() { (ostate_with(1, 1), PRICE) } else { (ostate.clone(), 1) };
    let ctx = TxContext::new()
        .actor_input("Vault", vstate.clone(), EntryCall::new("liquidate"), outpoint(1), vault_utxo, 0)
        .actor_input("oracle_feed::PriceRound", ostate.clone(), EntryCall::new("use"), outpoint(2), oracle_utxo, 0)
        .actor_output("oracle_feed::PriceRound", out_state, CovenantBinding::new(1, oracle_id), out_value);
    match builder.build(&ctx) {
        Ok(_) => println!("RESULT [price-tamper via use] ACCEPTED  <-- VULNERABLE"),
        Err(e) => println!("RESULT [price-tamper via use] REJECTED: {e}"),
    }
}

fn sweep_case(label: &str, signer: &Keypair, new_price: i64) {
    let builder = mk_builder();
    let oracle_id = Hash::from_bytes([0x42; 32]);
    let ostate = ostate_with(1, PRICE as i64);
    let next = ostate_with(2, new_price);
    let utxo = builder.covenant_utxo("oracle_feed::PriceRound", ostate.clone(), PRICE, 0, false, Some(oracle_id)).unwrap();
    let signer = signer.clone();
    let (left, right, call) = if is_b() {
        // value conserved, price in state
        let l = 40_000_000u64;
        (l, PRICE - l, EntryCall::new("sweep").args_with(move |tx, i| args![sign_input(tx, i, &signer), new_price, 40_000_000i64]))
    } else {
        // price is the value: two children of new_price each
        let v = new_price as u64;
        (v, v, EntryCall::new("sweep").args_with(move |tx, i| args![sign_input(tx, i, &signer)]))
    };
    let ctx = TxContext::new()
        .actor_input("oracle_feed::PriceRound", ostate.clone(), call, outpoint(2), utxo, 0)
        .actor_output("oracle_feed::PriceRound", next.clone(), CovenantBinding::new(0, oracle_id), left)
        .actor_output("oracle_feed::PriceRound", next.clone(), CovenantBinding::new(0, oracle_id), right);
    match builder.build(&ctx) {
        Ok(_) => println!("RESULT [{label}] ACCEPTED"),
        Err(e) => println!("RESULT [{label}] REJECTED: {e}"),
    }
}

#[test]
fn sweep_cases() {
    sweep_case("sweep by publisher, price 1.0 -> 0.5", &keypair(), 50_000_000);
    let secp = Secp256k1::new();
    let other = Keypair::from_secret_key(&secp, &SecretKey::from_slice(&[7u8; 32]).unwrap());
    sweep_case("sweep by NON-publisher (must reject)", &other, 50_000_000);
    sweep_case("sweep to price 0 (must reject)", &keypair(), 0);
}

#[test]
fn liquidation_mass() {
    use kaspa_consensus_core::{config::params::MAINNET_PARAMS, mass::MassCalculator, tx::PopulatedTransaction};
    let builder = mk_builder();
    let oracle_id = Hash::from_bytes([0x42; 32]);
    let vault_id = Hash::from_bytes([0x77; 32]);
    let ostate = ostate_with(1, PRICE as i64);
    let vstate = vstate_owner(oracle_id, 1_000_000);
    let vault_utxo = builder.covenant_utxo("Vault", vstate.clone(), 1_000_000, 0, false, Some(vault_id)).unwrap();
    let oracle_utxo = builder.covenant_utxo("oracle_feed::PriceRound", ostate.clone(), PRICE, 0, false, Some(oracle_id)).unwrap();
    let entries = vec![vault_utxo.clone(), oracle_utxo.clone()];
    let ctx = TxContext::new()
        .actor_input("Vault", vstate.clone(), EntryCall::new("liquidate"), outpoint(1), vault_utxo, 0)
        .actor_input("oracle_feed::PriceRound", ostate.clone(), EntryCall::new("use"), outpoint(2), oracle_utxo, 0)
        .actor_output("oracle_feed::PriceRound", ostate.clone(), CovenantBinding::new(1, oracle_id), PRICE);
    let tx = builder.build(&ctx).expect("liquidation builds");
    let calc = MassCalculator::new_with_consensus_params(&MAINNET_PARAMS);
    let nc = calc.calc_non_contextual_masses(&tx);
    let pop = PopulatedTransaction::new(&tx, entries);
    let storage = calc.calc_contextual_masses(&pop).map(|m| m.storage_mass);
    let size: usize = borsh_free_size(&tx);
    let min_fee = 100u64 * std::cmp::max(nc.compute_mass, 2 * size as u64);
    let lim = MAINNET_PARAMS.block_mass_limits().after();
    println!(
        "MASS liquidate: compute {} transient {} storage {:?} | approx size {} B | min relay fee {} sompi ({:.6} KAS) | block limits c{} t{} s{}",
        nc.compute_mass, nc.transient_mass, storage, size, min_fee, min_fee as f64 / 1e8, lim.compute, lim.transient, lim.storage
    );
}

fn borsh_free_size(tx: &Transaction) -> usize {
    // transient mass is 4 x serialized size, so recover size from the non-contextual masses is unnecessary;
    // approximate with the sum of script/sig lengths plus fixed overhead (reporting only).
    let sig: usize = tx.inputs.iter().map(|i| i.signature_script.len()).sum();
    let spk: usize = tx.outputs.iter().map(|o| o.script_public_key.script().len()).sum();
    sig + spk + 100 * tx.inputs.len() + 60 * tx.outputs.len() + 80
}
