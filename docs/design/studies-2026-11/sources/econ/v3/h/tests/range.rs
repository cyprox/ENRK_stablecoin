//! Local engine test: counted-range N->N refresh that must consume the whole population (n in state).
use std::collections::BTreeMap;
use argent::builder::args;
use argent::builder::{ArtifactValue as V, EntryCall, TxBuilder, TxContext};
use kaspa_consensus_core::{Hash, hashing::{sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash}, sighash_type::SIG_HASH_ALL},
    tx::{CovenantBinding, MutableTransaction, Transaction, TransactionId, TransactionOutpoint}};
use secp256k1::{Keypair, Secp256k1, SecretKey};
const V3: &str = env!("CARGO_MANIFEST_DIR");
fn kp(b: u8) -> Keypair { Keypair::from_secret_key(&Secp256k1::new(), &SecretKey::from_slice(&[b; 32]).unwrap()) }
fn pk(b: u8) -> Vec<u8> { kp(b).x_only_public_key().0.serialize().to_vec() }
fn sign<T: AsRef<Transaction>>(tx: &MutableTransaction<T>, i: usize, k: &Keypair) -> Vec<u8> {
    let r = SigHashReusedValuesUnsync::new();
    let h = calc_schnorr_signature_hash(&tx.as_verifiable(), i, SIG_HASH_ALL, &r);
    let m = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
    let mut s = k.sign_schnorr(m).as_ref().to_vec(); s.push(SIG_HASH_ALL.to_u8()); s
}
fn st(round: i64, price: i64, n: i64) -> BTreeMap<String, V> {
    let mut s = BTreeMap::new();
    s.insert("publisher".into(), V::Bytes(pk(1))); s.insert("round".into(), V::Int(round));
    s.insert("price".into(), V::Int(price)); s.insert("stamp".into(), V::Int(1000)); s.insert("n".into(), V::Int(n)); s
}
fn run(label: &str, expect_ok: bool, n_state: i64, inputs: usize, new_prices: Vec<i64>) {
    let a = argent::build_file(format!("{V3}/../range/app.ag"), &std::env::temp_dir().join(format!("enrk_rng_{}", std::process::id()))).expect("compiles");
    let b = TxBuilder::new(&a).unwrap();
    let id = Hash::from_bytes([0x42; 32]);
    let old = st(5, 100_000_000, n_state);
    let val = 500_000_000u64;
    let nexts: Vec<BTreeMap<String, V>> = new_prices.iter().map(|p| st(6, *p, n_state)).collect();
    let arr = V::Array(nexts.iter().cloned().map(V::Object).collect());
    let k = kp(1);
    let mut ctx = TxContext::new();
    for i in 0..inputs {
        let u = b.covenant_utxo("Px", old.clone(), val, 0, false, Some(id)).unwrap();
        let call = if i == 0 { let arr = arr.clone(); let k = k.clone(); EntryCall::new("refresh").args_with(move |tx, ix| args![sign(tx, ix, &k), arr.clone()]) } else { EntryCall::new("refresh") };
        ctx = ctx.actor_input("Px", old.clone(), call, TransactionOutpoint::new(TransactionId::from_bytes([i as u8 + 1; 32]), 0), u, 0);
    }
    for s in &nexts { ctx = ctx.actor_output("Px", s.clone(), CovenantBinding::new(0, id), val); }
    let r = b.build(&ctx).map(|_| ()).map_err(|e| e.to_string());
    let got = r.is_ok();
    println!("RESULT [{label}] expected={} got={} {} {}", if expect_ok {"ACCEPT"} else {"REJECT"}, if got {"ACCEPT"} else {"REJECT"}, if got == expect_ok {"AS-EXPECTED"} else {"UNEXPECTED"}, r.err().unwrap_or_default());
    assert_eq!(got, expect_ok, "{label}");
}
#[test]
fn range_cases() {
    run("R1 n=3, 3 inputs, +1% each", true, 3, 3, vec![101_000_000; 3]);
    run("R2 n=3, 3 inputs, mixed +1/-1/+2%", true, 3, 3, vec![101_000_000, 99_000_000, 102_000_000]);
    run("R3 n=3 but only 2 inputs (stale sibling left behind)", false, 3, 2, vec![101_000_000; 2]);
    run("R4 n=3, 3 inputs, one sibling +3%", false, 3, 3, vec![101_000_000, 103_000_000, 101_000_000]);
    run("R5 n=3, 3 inputs, one sibling price 0", false, 3, 3, vec![101_000_000, 0, 101_000_000]);
    run("R6 n=2 state, 3 inputs (population bigger than n)", false, 2, 3, vec![101_000_000; 3]);
    run("R7 n=1, 1 input", true, 1, 1, vec![101_000_000]);
}
