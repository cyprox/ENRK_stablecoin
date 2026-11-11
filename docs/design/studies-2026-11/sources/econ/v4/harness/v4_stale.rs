//! v4 local-only: stale-oracle behaviours with a lower-bound clock (no network).
use argent::builder::{args, ArtifactBundle, ArtifactValue, EntryCall, TxBuilder, TxContext};
use kaspa_consensus_core::{config::params::MAINNET_PARAMS, hashing::{sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash}, sighash_type::SIG_HASH_ALL}, mass::MassCalculator, tx::{CovenantBinding, MutableTransaction, PopulatedTransaction, Transaction, TransactionId, TransactionOutpoint}, Hash};
use secp256k1::{Keypair, Secp256k1, SecretKey};
use std::collections::BTreeMap;

fn kp(b: u8) -> Keypair { Keypair::from_secret_key(&Secp256k1::new(), &SecretKey::from_slice(&[b; 32]).unwrap()) }
fn pkb(k: &Keypair) -> Vec<u8> { k.x_only_public_key().0.serialize().to_vec() }
fn sign<T: AsRef<Transaction>>(tx: &MutableTransaction<T>, i: usize, k: &Keypair) -> Vec<u8> {
    let r = SigHashReusedValuesUnsync::new();
    let h = calc_schnorr_signature_hash(&tx.as_verifiable(), i, SIG_HASH_ALL, &r);
    let m = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
    let mut s = k.sign_schnorr(m).as_ref().to_vec(); s.push(SIG_HASH_ALL.to_u8()); s
}
fn op(t: u8) -> TransactionOutpoint { TransactionOutpoint::new(TransactionId::from_bytes([t; 32]), 0) }
fn ost(round: i64, last: i64) -> BTreeMap<String, ArtifactValue> {
    let mut s = BTreeMap::new();
    s.insert("publisher".into(), ArtifactValue::Bytes(pkb(&kp(9)))); s.insert("round".into(), ArtifactValue::Int(round)); s.insert("last".into(), ArtifactValue::Int(last)); s
}
fn vst(oid: Hash, debt: i64) -> BTreeMap<String, ArtifactValue> {
    let mut s = BTreeMap::new();
    s.insert("owner".into(), ArtifactValue::Bytes(pkb(&kp(21)))); s.insert("oracle_covid".into(), ArtifactValue::Bytes(oid.as_bytes().to_vec())); s.insert("debt".into(), ArtifactValue::Int(debt)); s
}
fn run(label: &str, entry: &str, lock: u64, price: u64, c: u64, debt: i64, withdrawn: u64) {
    let dir = std::env::var("V4_DIR").unwrap();
    let out = std::env::temp_dir().join(format!("v4_stale_{}", std::process::id()));
    let v = Box::leak(Box::new(argent::build_file(format!("{dir}/vault_stale.ag"), &out.join("v")).unwrap()));
    let o = Box::leak(Box::new(argent::build_file(format!("{dir}/oracle.ag"), &out.join("o")).unwrap()));
    let b = TxBuilder::from_bundle(&ArtifactBundle::new(&*v).unwrap().with_app("oracle_feed", &*o).unwrap()).unwrap();
    let (oid, vid) = (Hash::from_bytes([0x42; 32]), Hash::from_bytes([0x77; 32]));
    let os = ost(1, 1000); let vs = vst(oid, debt);
    let vu = b.covenant_utxo("Vault", vs.clone(), c, 0, false, Some(vid)).unwrap();
    let ou = b.covenant_utxo("oracle_feed::PriceRound", os.clone(), price, 0, false, Some(oid)).unwrap();
    let entries = vec![vu.clone(), ou.clone()];
    let owner = kp(21);
    let call = if entry == "withdraw" { EntryCall::new("withdraw").args_with(move |tx, i| args![sign(tx, i, &owner), withdrawn as i64]) } else { EntryCall::new("liquidate") };
    let mut ctx = TxContext::new().lock_time(lock)
        .actor_input("Vault", vs.clone(), call, op(1), vu, 0)
        .actor_input("oracle_feed::PriceRound", os.clone(), EntryCall::new("use"), op(2), ou, 0)
        .actor_output("oracle_feed::PriceRound", os, CovenantBinding::new(1, oid), price);
    if entry == "withdraw" { ctx = ctx.actor_output("Vault", vs, CovenantBinding::new(0, vid), c - withdrawn); }
    match b.build(&ctx) {
        Ok(tx) => {
            let m = MassCalculator::new_with_consensus_params(&MAINNET_PARAMS);
            let nc = m.calc_non_contextual_masses(&tx);
            let s = m.calc_contextual_masses(&PopulatedTransaction::new(&tx, entries)).map(|x| x.storage_mass);
            println!("RESULT [{label}] ACCEPT compute {} transient {} storage {:?}", nc.compute_mass, nc.transient_mass, s)
        }
        Err(e) => { let m = format!("{e}").replace('\n', " "); println!("RESULT [{label}] REJECT {}", &m[..m.len().min(110)]) }
    }
}
#[test]
fn stale_cases() {
    let (p, c, d) = (100_000_000u64, 300_000_000u64, 100_000_000i64); // ICR 300 % at fresh price
    let last = 1000u64; let decay = 864_000u64;
    run("liquidate, claimed age 0 (healthy)", "liquidate", last, p, c, d, 0);
    run("liquidate, age = DECAY/2 (ICR exactly 150, not < 150)", "liquidate", last + decay / 2, p, c, d, 0);
    run("liquidate, age = 0.6 DECAY (price x0.4, ICR 120)", "liquidate", last + decay * 6 / 10, p, c, d, 0);
    run("liquidate, age = DECAY (price 0)", "liquidate", last + decay, p, c, d, 0);
    run("liquidate, age = 10 x DECAY (clamped)", "liquidate", last + 10 * decay, p, c, d, 0);
    run("liquidate, lock_time below oracle clock (CLTV)", "liquidate", last - 1, p, c, d, 0);
    run("liquidate, oracle price 0 (must reject)", "liquidate", last + decay, 0, c, d, 0);
    run("withdraw to 200 %, owner claims age 0 while real age is arbitrary", "withdraw", last, p, c, d, 100_000_000);
    run("withdraw to 200 %, honest age = DECAY", "withdraw", last + decay, p, c, d, 100_000_000);
}
