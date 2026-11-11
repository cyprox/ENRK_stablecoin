//! v4 local-only harness (NO network, no keys). Generic single-actor runner:
//!   V4_APP=<app.ag> V4_ACTOR=<Actor> V4_FIELDS=a,b,c V4_CASES=<file> V4_OUT=<file> cargo test --offline --test v4_exec arith -- --nocapture
//! each case line: "<entry> <i64> <i64> ..." (one value per field); result line: "<n> ACCEPT" | "<n> REJECT <msg>".
use argent::builder::{ArtifactBundle, ArtifactValue, EntryCall, TxBuilder, TxContext};
use kaspa_consensus_core::{Hash, tx::{TransactionId, TransactionOutpoint}};
use std::collections::BTreeMap;

fn outpoint(tag: u8) -> TransactionOutpoint { TransactionOutpoint::new(TransactionId::from_bytes([tag; 32]), 0) }

#[test]
fn arith() {
    let app = std::env::var("V4_APP").unwrap();
    let actor: &'static str = Box::leak(std::env::var("V4_ACTOR").unwrap().into_boxed_str());
    let fields: Vec<String> = std::env::var("V4_FIELDS").unwrap().split(',').map(|s| s.to_string()).collect();
    let cases = std::fs::read_to_string(std::env::var("V4_CASES").unwrap()).unwrap();
    let out_path = std::env::var("V4_OUT").unwrap();
    let out = std::env::temp_dir().join(format!("v4_arith_{}", std::process::id()));
    let art = Box::leak(Box::new(argent::build_file(&app, &out).expect("compiles")));
    let bundle = ArtifactBundle::new(&*art).unwrap();
    let builder = TxBuilder::from_bundle(&bundle).unwrap();
    let cid = Hash::from_bytes([0x77; 32]);
    let mut res = String::new();
    for (n, line) in cases.lines().enumerate() {
        let mut it = line.split_whitespace();
        let entry = it.next().unwrap();
        let mut st: BTreeMap<String, ArtifactValue> = BTreeMap::new();
        for f in &fields { st.insert(f.clone(), ArtifactValue::Int(it.next().unwrap().parse::<i64>().unwrap())); }
        let utxo = match builder.covenant_utxo(actor, st.clone(), 1_000_000, 0, false, Some(cid)) { Ok(u) => u, Err(e) => { res += &format!("{n} REJECT build-utxo {e}\n"); continue; } };
        let ctx = TxContext::new().actor_input(actor, st, EntryCall::new(entry), outpoint(1), utxo, 0);
        match builder.build(&ctx) {
            Ok(_) => res += &format!("{n} ACCEPT\n"),
            Err(e) => { let m = format!("{e}").replace('\n', " "); res += &format!("{n} REJECT {}\n", &m[..m.len().min(140)]); }
        }
    }
    std::fs::write(out_path, res).unwrap();
}
