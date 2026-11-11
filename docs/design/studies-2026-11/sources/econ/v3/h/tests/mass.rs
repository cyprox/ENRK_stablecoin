//! Local mass of N ENRK price UTXOs spent via `use` and recreated (same shape as the KAS oracle round).
use std::collections::BTreeMap;
use argent::builder::{ArtifactValue, EntryCall, TxBuilder, TxContext};
use kaspa_consensus_core::{Hash, config::params::MAINNET_PARAMS, mass::MassCalculator,
    tx::{CovenantBinding, PopulatedTransaction, TransactionId, TransactionOutpoint, UtxoEntry}};
const V3: &str = env!("CARGO_MANIFEST_DIR");
#[test]
fn ladder() {
    let a = argent::build_file(format!("{V3}/../price/app.ag"), &std::env::temp_dir().join("enrkp_mass")).unwrap();
    let b = TxBuilder::new(&a).unwrap();
    let id = Hash::from_bytes([0x42; 32]);
    let mut s = BTreeMap::new();
    s.insert("publisher".to_string(), ArtifactValue::Bytes(vec![7; 32]));
    s.insert("round".to_string(), ArtifactValue::Int(5));
    s.insert("price".to_string(), ArtifactValue::Int(100_000_000));
    s.insert("stamp".to_string(), ArtifactValue::Int(1000));
    let calc = MassCalculator::new_with_consensus_params(&MAINNET_PARAMS);
    let val: u64 = 2_100_000_000;
    for n in [1usize, 64, 256, 512, 532, 640] {
        let mut ctx = TxContext::new(); let mut es: Vec<UtxoEntry> = vec![];
        for i in 0..n {
            let u = b.covenant_utxo("EnrkPrice", s.clone(), val, 0, false, Some(id)).unwrap();
            es.push(u.clone());
            ctx = ctx.actor_input("EnrkPrice", s.clone(), EntryCall::new("use"), TransactionOutpoint::new(TransactionId::from_bytes([(i % 250) as u8 + 1; 32]), i as u32), u, 0);
        }
        for i in 0..n { ctx = ctx.actor_output("EnrkPrice", s.clone(), CovenantBinding::new(i as u16, id), val); }
        match b.build(&ctx) {
            Ok(tx) => {
                let nc = calc.calc_non_contextual_masses(&tx);
                let st = calc.calc_contextual_masses(&PopulatedTransaction::new(&tx, es)).map(|m| m.storage_mass);
                println!("MASS N={n} compute={} transient={} storage={:?} script_len={}", nc.compute_mass, nc.transient_mass, st, tx.inputs[0].signature_script.len());
            }
            Err(e) => println!("MASS N={n} FAILED {e}"),
        }
    }
}
