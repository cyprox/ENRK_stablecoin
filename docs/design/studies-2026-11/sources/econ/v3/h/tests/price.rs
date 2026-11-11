//! Local engine tests of the ENRK price UTXO and a consumer gate. LOCAL ONLY: nothing is broadcast.
use std::collections::BTreeMap;
use argent::builder::args;
use argent::builder::{ArtifactBundle, ArtifactValue, EntryCall, TxBuilder, TxContext};
use kaspa_consensus_core::{
    Hash,
    hashing::{sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash}, sighash_type::SIG_HASH_ALL},
    tx::{CovenantBinding, MutableTransaction, Transaction, TransactionId, TransactionOutpoint},
};
use secp256k1::{Keypair, Secp256k1, SecretKey};

const V3: &str = env!("CARGO_MANIFEST_DIR");
const STAMP: i64 = 1000;
const GAP: u64 = 100;
const VAL: u64 = 400_000_000;

fn kp(b: u8) -> Keypair { Keypair::from_secret_key(&Secp256k1::new(), &SecretKey::from_slice(&[b; 32]).unwrap()) }
fn pk(b: u8) -> Vec<u8> { kp(b).x_only_public_key().0.serialize().to_vec() }
fn sign<T: AsRef<Transaction>>(tx: &MutableTransaction<T>, i: usize, k: &Keypair) -> Vec<u8> {
    let r = SigHashReusedValuesUnsync::new();
    let h = calc_schnorr_signature_hash(&tx.as_verifiable(), i, SIG_HASH_ALL, &r);
    let m = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
    let mut s = k.sign_schnorr(m).as_ref().to_vec(); s.push(SIG_HASH_ALL.to_u8()); s
}
fn op(t: u8) -> TransactionOutpoint { TransactionOutpoint::new(TransactionId::from_bytes([t; 32]), 0) }
fn pst(round: i64, price: i64, stamp: i64) -> BTreeMap<String, ArtifactValue> {
    let mut s = BTreeMap::new();
    s.insert("publisher".into(), ArtifactValue::Bytes(pk(1)));
    s.insert("round".into(), ArtifactValue::Int(round));
    s.insert("price".into(), ArtifactValue::Int(price));
    s.insert("stamp".into(), ArtifactValue::Int(stamp));
    s
}
fn builder() -> TxBuilder<'static> {
    let out = std::env::temp_dir().join(format!("enrkp_{}", std::process::id()));
    let p = Box::leak(Box::new(argent::build_file(format!("{V3}/../price/app.ag"), &out.join("p")).expect("price compiles")));
    TxBuilder::from_bundle(Box::leak(Box::new(ArtifactBundle::new(&*p).unwrap()))).unwrap()
}
fn report(label: &str, expect_ok: bool, r: Result<(), String>) {
    let got_ok = r.is_ok();
    let verdict = if got_ok == expect_ok { "AS-EXPECTED" } else { "UNEXPECTED" };
    println!("RESULT [{label}] expected={} got={} {verdict} {}", if expect_ok {"ACCEPT"} else {"REJECT"}, if got_ok {"ACCEPT"} else {"REJECT"}, r.err().unwrap_or_default());
    assert_eq!(got_ok, expect_ok, "{label}");
}

/// update with explicit knobs
fn update(label: &str, expect_ok: bool, cur: (i64, i64, i64), next_price: i64, lock: u64, left_v: u64, left_out: u64, right_out: u64, signer: u8) {
    let b = builder();
    let id = Hash::from_bytes([0x42; 32]);
    let cs = pst(cur.0, cur.1, cur.2);
    let utxo = b.covenant_utxo("EnrkPrice", cs.clone(), VAL, 0, false, Some(id)).unwrap();
    let ns = pst(cur.0 + 1, next_price, lock as i64);
    let k = kp(signer);
    let ctx = TxContext::new().lock_time(lock)
        .actor_input("EnrkPrice", cs, EntryCall::new("update").args_with(move |tx, i| args![sign(tx, i, &k), next_price, left_v as i64]), op(1), utxo, 0)
        .actor_output("EnrkPrice", ns.clone(), CovenantBinding::new(0, id), left_out)
        .actor_output("EnrkPrice", ns, CovenantBinding::new(0, id), right_out);
    report(label, expect_ok, b.build(&ctx).map(|_| ()).map_err(|e| e.to_string()));
}

#[test]
fn price_update_cases() {
    let (r, p, s) = (5, 100_000_000i64, STAMP);
    let ok_lock = s as u64 + GAP;
    let half = VAL / 2;
    update("U1 +1.5% at gap", true, (r, p, s), 101_500_000, ok_lock, half, half, VAL - half, 1);
    update("U2 -1.5% at gap", true, (r, p, s), 98_500_000, ok_lock, half, half, VAL - half, 1);
    update("U3 +2.0000% boundary", true, (r, p, s), 102_000_000, ok_lock, half, half, VAL - half, 1);
    update("U4 -2.0000% boundary", true, (r, p, s), 98_000_000, ok_lock, half, half, VAL - half, 1);
    update("U5 +2.0001% rejected", false, (r, p, s), 102_000_001, ok_lock, half, half, VAL - half, 1);
    update("U6 -2.0001% rejected", false, (r, p, s), 97_999_999, ok_lock, half, half, VAL - half, 1);
    update("U7 +50% rejected", false, (r, p, s), 150_000_000, ok_lock, half, half, VAL - half, 1);
    update("U8 price 0 rejected", false, (r, p, s), 0, ok_lock, half, half, VAL - half, 1);
    update("U9 negative price rejected", false, (r, p, s), -5, ok_lock, half, half, VAL - half, 1);
    update("U10 lock one DAA below gap rejected", false, (r, p, s), 101_000_000, ok_lock - 1, half, half, VAL - half, 1);
    update("U11 lock far later accepted (stamp follows)", true, (r, p, s), 101_000_000, ok_lock + 50_000, half, half, VAL - half, 1);
    update("U12 wrong signer rejected", false, (r, p, s), 101_000_000, ok_lock, half, half, VAL - half, 2);
    update("U13 value not conserved rejected", false, (r, p, s), 101_000_000, ok_lock, half, half, VAL - half - 1, 1);
    update("U14 stored price 0 (bad genesis) rejected", false, (r, 0, s), 1, ok_lock, half, half, VAL - half, 1);
    update("U15 stored price above PRICE_MAX rejected", false, (r, 1_000_000_000_001, s), 1_000_000_000_001, ok_lock, half, half, VAL - half, 1);
    update("U16 price at PRICE_MAX, +0.5% rejected (cap)", false, (r, 1_000_000_000_000, s), 1_000_000_000_001, ok_lock, half, half, VAL - half, 1);
    update("U17 price at PRICE_MAX, -1% accepted", true, (r, 1_000_000_000_000, s), 990_000_000_000, ok_lock, half, half, VAL - half, 1);
    update("U18 ms-domain lock_time (>=5e11) rejected", false, (r, p, s), 101_000_000, 1_700_000_000_000, half, half, VAL - half, 1);
    update("U19 left_value 0 rejected", false, (r, p, s), 101_000_000, ok_lock, 0, 0, VAL, 1);
}

#[test]
fn price_use_cases() {
    let b = builder();
    let id = Hash::from_bytes([0x42; 32]);
    let cs = pst(5, 100_000_000, STAMP);
    let utxo = b.covenant_utxo("EnrkPrice", cs.clone(), VAL, 0, false, Some(id)).unwrap();
    let mk = |out_state: BTreeMap<String, ArtifactValue>, out_val: u64| {
        let ctx = TxContext::new()
            .actor_input("EnrkPrice", cs.clone(), EntryCall::new("use"), op(1), utxo.clone(), 0)
            .actor_output("EnrkPrice", out_state, CovenantBinding::new(0, id), out_val);
        b.build(&ctx).map(|_| ()).map_err(|e| e.to_string())
    };
    report("S1 use, unchanged", true, mk(cs.clone(), VAL));
    report("S2 use, price changed to +1%", false, mk(pst(5, 101_000_000, STAMP), VAL));
    report("S3 use, stamp changed", false, mk(pst(5, 100_000_000, STAMP + 10), VAL));
    report("S4 use, value reduced", false, mk(cs.clone(), VAL - 1));
}

#[test]
fn gate_cases() {
    let out = std::env::temp_dir().join(format!("enrkg_{}", std::process::id()));
    let g = Box::leak(Box::new(argent::build_file(format!("{V3}/../gate/gate.ag"), &out.join("g")).expect("gate compiles")));
    let p = Box::leak(Box::new(argent::build_file(format!("{V3}/../price/app.ag"), &out.join("p")).expect("price compiles")));
    let bundle = Box::leak(Box::new(ArtifactBundle::new(&*g).unwrap().with_app("enrk_price_feed", &*p).unwrap()));
    let b = TxBuilder::from_bundle(bundle).unwrap();
    let pid = Hash::from_bytes([0x42; 32]);
    let gid = Hash::from_bytes([0x77; 32]);
    let run = |label: &str, expect_ok: bool, entry: &str, price: i64, stamp: i64, lock: u64, forged: bool| {
        let ps = pst(5, price, stamp);
        let mut gs = BTreeMap::new();
        gs.insert("owner".to_string(), ArtifactValue::Bytes(pk(3)));
        gs.insert("price_covid".to_string(), ArtifactValue::Bytes(if forged { vec![0x99; 32] } else { pid.as_bytes().to_vec() }));
        gs.insert("target".to_string(), ArtifactValue::Int(100_000_000));
        let gu = b.covenant_utxo("Gate", gs.clone(), 100_000_000, 0, false, Some(gid)).unwrap();
        let pu = b.covenant_utxo("enrk_price_feed::EnrkPrice", ps.clone(), VAL, 0, false, Some(pid)).unwrap();
        let ctx = TxContext::new().lock_time(lock)
            .actor_input("Gate", gs.clone(), EntryCall::new(entry), op(1), gu, 0)
            .actor_input("enrk_price_feed::EnrkPrice", ps.clone(), EntryCall::new("use"), op(2), pu, 0)
            .actor_output("Gate", gs.clone(), CovenantBinding::new(0, gid), 100_000_000)
            .actor_output("enrk_price_feed::EnrkPrice", ps.clone(), CovenantBinding::new(1, pid), VAL);
        report(label, expect_ok, b.build(&ctx).map(|_| ()).map_err(|e| e.to_string()));
    };
    run("G1 depeg_trigger price -5% (band 3%)", true, "depeg_trigger", 95_000_000, STAMP, 0, false);
    run("G2 depeg_trigger price -2%", false, "depeg_trigger", 98_000_000, STAMP, 0, false);
    run("G3 depeg_trigger price exactly -3%", false, "depeg_trigger", 97_000_000, STAMP, 0, false);
    run("G4 depeg_trigger forged oracle id", false, "depeg_trigger", 95_000_000, STAMP, 0, true);
    run("G5 oracle_dead at stamp+MAX_AGE", true, "oracle_dead", 100_000_000, STAMP, (STAMP + 36000) as u64, false);
    run("G6 oracle_dead one DAA early", false, "oracle_dead", 100_000_000, STAMP, (STAMP + 36000 - 1) as u64, false);
    run("G7 oracle_dead claimed with lock 0 (understated)", false, "oracle_dead", 100_000_000, STAMP, 0, false);
}
