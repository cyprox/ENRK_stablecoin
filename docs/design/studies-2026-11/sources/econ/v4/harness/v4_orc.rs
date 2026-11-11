//! v4 local-only: bounded sweep / rotation negative tests for orc/oracle_b.ag. No network.
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
fn stt(pubk: Vec<u8>, round: i64, last: i64) -> BTreeMap<String, ArtifactValue> {
    let mut s = BTreeMap::new();
    s.insert("publisher".into(), ArtifactValue::Bytes(pubk)); s.insert("round".into(), ArtifactValue::Int(round)); s.insert("last".into(), ArtifactValue::Int(last)); s
}
fn builder() -> TxBuilder<'static> {
    let dir = std::env::var("V4_DIR").unwrap();
    let out = std::env::temp_dir().join(format!("v4_orc_{}", std::process::id()));
    let a = Box::leak(Box::new(argent::build_file(format!("{dir}/oracle_b.ag"), &out).unwrap()));
    TxBuilder::from_bundle(&ArtifactBundle::new(&*a).unwrap()).unwrap()
}
const ID: u8 = 0x42;
fn report(label: &str, b: &TxBuilder, ctx: TxContext, entries: Vec<kaspa_consensus_core::tx::UtxoEntry>) {
    match b.build(&ctx) {
        Ok(tx) => {
            let c = MassCalculator::new_with_consensus_params(&MAINNET_PARAMS);
            let nc = c.calc_non_contextual_masses(&tx);
            let s = c.calc_contextual_masses(&PopulatedTransaction::new(&tx, entries)).map(|m| m.storage_mass);
            println!("RESULT [{label}] ACCEPT compute {} transient {} storage {:?}", nc.compute_mass, nc.transient_mass, s)
        }
        Err(e) => { let m = format!("{e}").replace('\n', " "); println!("RESULT [{label}] REJECT {}", &m[..m.len().min(120)]) }
    }
}
fn sweep(label: &str, signer: &Keypair, publisher: &Keypair, parent_v: u64, lval: u64, rval: u64, last: i64, lock: u64) {
    let b = builder(); let id = Hash::from_bytes([ID; 32]);
    let ps = stt(pkb(publisher), 1, last); let ns = stt(pkb(publisher), 2, lock as i64);
    let u = b.covenant_utxo("PriceRound", ps.clone(), parent_v, 0, false, Some(id)).unwrap();
    let sg = signer.clone();
    let ctx = TxContext::new().lock_time(lock)
        .actor_input("PriceRound", ps, EntryCall::new("sweep").args_with(move |tx, i| args![sign(tx, i, &sg)]), op(1), u.clone(), 0)
        .actor_output("PriceRound", ns.clone(), CovenantBinding::new(0, id), lval)
        .actor_output("PriceRound", ns, CovenantBinding::new(0, id), rval);
    report(label, &b, ctx, vec![u]);
}
fn rotate(label: &str, signer_old: &Keypair, signer_new: &Keypair, publisher: &Keypair, new_pub: &Keypair) {
    let b = builder(); let id = Hash::from_bytes([ID; 32]);
    let ps = stt(pkb(publisher), 1, 1000); let ns = stt(pkb(new_pub), 1, 1000);
    let u = b.covenant_utxo("PriceRound", ps.clone(), 100_000_000, 0, false, Some(id)).unwrap();
    let (so, sn, np) = (signer_old.clone(), signer_new.clone(), pkb(new_pub));
    let ctx = TxContext::new()
        .actor_input("PriceRound", ps, EntryCall::new("rotate").args_with(move |tx, i| args![sign(tx, i, &so), np.clone(), sign(tx, i, &sn)]), op(1), u.clone(), 0)
        .actor_output("PriceRound", ns, CovenantBinding::new(0, id), 100_000_000);
    report(label, &b, ctx, vec![u]);
}
#[test]
fn orc_cases() {
    let (a, bk, c) = (kp(9), kp(10), kp(11));
    let v = 100_000_000u64; let last = 1000i64; let ok_lock = 1000 + 600u64;
    sweep("sweep +10.00% (lock = last+GAP)", &a, &a, v, 110_000_000, 110_000_000, last, ok_lock);
    sweep("sweep -10.00%", &a, &a, v, 90_000_000, 90_000_000, last, ok_lock);
    sweep("sweep +10.01% (must reject)", &a, &a, v, 110_100_000, 110_100_000, last, ok_lock);
    sweep("sweep -10.01% (must reject)", &a, &a, v, 89_900_000, 89_900_000, last, ok_lock);
    sweep("sweep to price 0 (must reject)", &a, &a, v, 0, 0, last, ok_lock);
    sweep("sweep to 900 < P_MIN from 1000 (must reject)", &a, &a, 1000, 900, 900, last, ok_lock);
    sweep("sweep with non-publisher key (must reject)", &c, &a, v, 105_000_000, 105_000_000, last, ok_lock);
    sweep("sweep one block-gap too early (must reject)", &a, &a, v, 105_000_000, 105_000_000, last, ok_lock - 1);
    sweep("unequal siblings (must reject)", &a, &a, v, 105_000_000, 104_000_000, last, ok_lock);
    sweep("parent above P_MAX (must reject)", &a, &a, 600_000_000, 600_000_000, 600_000_000, last, ok_lock);
    sweep("child above P_MAX from P_MAX (must reject)", &a, &a, 500_000_000, 520_000_000, 520_000_000, last, ok_lock);
    rotate("rotate old+new sig", &a, &bk, &a, &bk);
    rotate("rotate, new key did not sign (must reject)", &a, &c, &a, &bk);
    rotate("rotate, old key did not sign (must reject)", &c, &bk, &a, &bk);
    sweep("after rotation: sweep by OLD key (must reject)", &a, &bk, v, 105_000_000, 105_000_000, last, ok_lock);
    sweep("after rotation: sweep by NEW key", &bk, &bk, v, 105_000_000, 105_000_000, last, ok_lock);
}
