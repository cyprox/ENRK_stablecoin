//! v4 local-only: P19 liquidation settled by ENRK note retirement (no network).
use argent::builder::{args, ArtifactBundle, ArtifactValue, EntryCall, TxBuilder, TxContext};
use kaspa_consensus_core::{config::params::MAINNET_PARAMS, hashing::{sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash}, sighash_type::SIG_HASH_ALL}, mass::MassCalculator, tx::{CovenantBinding, MutableTransaction, PopulatedTransaction, Transaction, TransactionId, TransactionOutpoint}, Hash};
use secp256k1::{Keypair, Secp256k1, SecretKey};
use std::collections::BTreeMap;
type S = BTreeMap<String, ArtifactValue>;
fn kp(b: u8) -> Keypair { Keypair::from_secret_key(&Secp256k1::new(), &SecretKey::from_slice(&[b; 32]).unwrap()) }
fn pkb(k: &Keypair) -> Vec<u8> { k.x_only_public_key().0.serialize().to_vec() }
fn sign<T: AsRef<Transaction>>(tx: &MutableTransaction<T>, i: usize, k: &Keypair) -> Vec<u8> {
    let r = SigHashReusedValuesUnsync::new();
    let h = calc_schnorr_signature_hash(&tx.as_verifiable(), i, SIG_HASH_ALL, &r);
    let m = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
    let mut s = k.sign_schnorr(m).as_ref().to_vec(); s.push(SIG_HASH_ALL.to_u8()); s
}
fn op(t: u8) -> TransactionOutpoint { TransactionOutpoint::new(TransactionId::from_bytes([t; 32]), 0) }
fn ost() -> S { let mut s = S::new(); s.insert("publisher".into(), ArtifactValue::Bytes(pkb(&kp(9)))); s.insert("round".into(), ArtifactValue::Int(1)); s.insert("last".into(), ArtifactValue::Int(1000)); s }
fn vst(oid: Hash, eid: Hash, debt: i64) -> S {
    let mut s = S::new(); s.insert("owner".into(), ArtifactValue::Bytes(pkb(&kp(21)))); s.insert("oracle_covid".into(), ArtifactValue::Bytes(oid.as_bytes().to_vec()));
    s.insert("enrk_covid".into(), ArtifactValue::Bytes(eid.as_bytes().to_vec())); s.insert("debt".into(), ArtifactValue::Int(debt)); s
}
fn nst(holder: Vec<u8>, ctl: Hash, amount: i64) -> S {
    let mut s = S::new(); s.insert("holder".into(), ArtifactValue::Bytes(holder)); s.insert("controller_id".into(), ArtifactValue::Bytes(ctl.as_bytes().to_vec())); s.insert("amount".into(), ArtifactValue::Int(amount)); s
}
fn pst(to: Vec<u8>) -> S { let mut s = S::new(); s.insert("to".into(), ArtifactValue::Bytes(to)); s }
#[derive(Clone, Copy, PartialEq)] enum Mode { Retire, TransferInstead, NoteAlone }
fn run(label: &str, mode: Mode, note_amt: i64, pay: u64, note_ctl: u8, holder_key: u8, c: u64, debt: i64) {
    let dir = std::env::var("V4_DIR").unwrap();
    let out = std::env::temp_dir().join(format!("v4_bid_{}", std::process::id()));
    let v = Box::leak(Box::new(argent::build_file(format!("{dir}/vault_bid.ag"), &out.join("v")).unwrap()));
    let o = Box::leak(Box::new(argent::build_file(format!("{dir}/oracle.ag"), &out.join("o")).unwrap()));
    let t = Box::leak(Box::new(argent::build_file(format!("{dir}/tok.ag"), &out.join("t")).unwrap()));
    let b = TxBuilder::from_bundle(&ArtifactBundle::new(&*v).unwrap().with_app("oracle_feed", &*o).unwrap().with_app("tok", &*t).unwrap()).unwrap();
    let (oid, vid, eid) = (Hash::from_bytes([0x42; 32]), Hash::from_bytes([0x77; 32]), Hash::from_bytes([0x55; 32]));
    let nctl = Hash::from_bytes([note_ctl; 32]);
    let p = 100_000_000u64;
    let os = ost(); let vs = vst(oid, eid, debt);
    let ns = nst(pkb(&kp(holder_key)), nctl, note_amt);
    let vu = b.covenant_utxo("Vault", vs.clone(), c, 0, false, Some(vid)).unwrap();
    let ou = b.covenant_utxo("oracle_feed::PriceRound", os.clone(), p, 0, false, Some(oid)).unwrap();
    let nu = b.covenant_utxo("tok::Note", ns.clone(), 50_000_000, 0, false, Some(eid)).unwrap();
    let liq = pkb(&kp(33)); let liq2 = liq.clone();
    let seize = pay; let repay = note_amt;
    let mut ctx = TxContext::new();
    let mut entries = vec![];
    let hk = kp(holder_key);
    if mode != Mode::NoteAlone {
        ctx = ctx.actor_input("Vault", vs.clone(), EntryCall::new("liquidate_bid").args_with(move |_t, _i| args![liq2.clone()]), op(1), vu.clone(), 0)
            .actor_input("oracle_feed::PriceRound", os.clone(), EntryCall::new("use"), op(2), ou.clone(), 0);
        entries.push(vu); entries.push(ou);
    }
    let ni = entries.len();
    match mode {
        Mode::Retire | Mode::NoteAlone => { ctx = ctx.actor_input("tok::Note", ns.clone(), EntryCall::new("retire").args_with(move |tx, i| args![sign(tx, i, &hk)]), op(3), nu.clone(), 0); }
        Mode::TransferInstead => { ctx = ctx.actor_input("tok::Note", ns.clone(), EntryCall::new("transfer").args_with(move |tx, i| args![liq.clone(), sign(tx, i, &hk)]), op(3), nu.clone(), 0);
            ctx = ctx.actor_output("tok::Note", nst(pkb(&kp(33)), nctl, note_amt), CovenantBinding::new(ni as u16, eid), 50_000_000); }
    }
    entries.push(nu);
    if mode != Mode::NoteAlone {
        ctx = ctx.actor_output("Vault", vst(oid, eid, debt - repay), CovenantBinding::new(0, vid), c - seize)
            .actor_output("Pay", pst(pkb(&kp(33))), CovenantBinding::new(0, vid), seize)
            .actor_output("oracle_feed::PriceRound", os, CovenantBinding::new(1, oid), p);
    }
    match b.build(&ctx) {
        Ok(tx) => {
            let m = MassCalculator::new_with_consensus_params(&MAINNET_PARAMS);
            let nc = m.calc_non_contextual_masses(&tx);
            let s = m.calc_contextual_masses(&PopulatedTransaction::new(&tx, entries)).map(|x| x.storage_mass);
            println!("RESULT [{label}] ACCEPT compute {} transient {} storage {:?}", nc.compute_mass, nc.transient_mass, s)
        }
        Err(e) => { let m = format!("{e}").replace('\n', " "); println!("RESULT [{label}] REJECT {}", &m[..m.len().min(130)]) }
    }
}
#[test]
fn bid_cases() {
    let (c, d) = (540_000_000u64, 450_000_000i64); // ICR 120
    run("bid 2e8 retired by holder: seize 2.18e8", Mode::Retire, 200_000_000, 218_000_000, 0x77, 40, c, d);
    run("bid 4.5e8 (full): seize 4.905e8", Mode::Retire, 450_000_000, 490_500_000, 0x77, 40, c, d);
    run("pay over by 1 sompi (must reject)", Mode::Retire, 200_000_000, 218_000_001, 0x77, 40, c, d);
    run("note retired alone, no vault co-spent (must reject)", Mode::NoteAlone, 200_000_000, 0, 0x77, 40, c, d);
    run("note names a different controller id (must reject)", Mode::Retire, 200_000_000, 218_000_000, 0x78, 40, c, d);
    run("healthy vault ICR 250 (must reject)", Mode::Retire, 200_000_000, 218_000_000, 0x77, 40, 1_000_000_000, 400_000_000);
    run("NOTE KEPT: note spent by transfer() while the vault pays the liquidator", Mode::TransferInstead, 200_000_000, 218_000_000, 0x77, 40, c, d);
}
