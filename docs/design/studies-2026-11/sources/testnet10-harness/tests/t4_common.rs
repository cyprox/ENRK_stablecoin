#![allow(dead_code)]
//! Scratch (testnet-10 only) shared helpers for the econ-t4 on-chain tests.
use argent::builder::{ArtifactBundle, ArtifactValue, InputSigScript, TxBuilder};
use kaspa_addresses::Address;
use kaspa_consensus_core::{
    config::params::MAINNET_PARAMS,
    hashing::sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash},
    hashing::sighash_type::SIG_HASH_ALL,
    mass::MassCalculator,
    tx::{MutableTransaction, ScriptPublicKey, Transaction, TransactionId, TransactionOutpoint, UtxoEntry},
};
use kaspa_txscript::{pay_to_address_script, script_builder::ScriptBuilder};
use secp256k1::{Keypair, Secp256k1, SecretKey};
use std::collections::BTreeMap;

pub fn unhex(s: &str) -> Vec<u8> { (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect() }
pub fn hex(b: &[u8]) -> String { b.iter().map(|x| format!("{x:02x}")).collect() }
pub fn env(k: &str) -> String { std::env::var(k).unwrap_or_else(|_| panic!("missing env {k}")) }
pub fn envu(k: &str, d: u64) -> u64 { std::env::var(k).ok().map(|v| v.parse().unwrap()).unwrap_or(d) }
pub fn op(txid: &str, i: u32) -> TransactionOutpoint { TransactionOutpoint::new(TransactionId::from_bytes(unhex(txid).try_into().unwrap()), i) }
pub fn int(v: i64) -> ArtifactValue { ArtifactValue::Int(v) }
pub fn sign_idx(tx: &MutableTransaction<Transaction>, idx: usize, kp: &Keypair) -> Vec<u8> {
    let reused = SigHashReusedValuesUnsync::new();
    let h = calc_schnorr_signature_hash(&tx.as_verifiable(), idx, SIG_HASH_ALL, &reused);
    let msg = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
    let mut sig = kp.sign_schnorr(msg).as_ref().to_vec();
    sig.push(SIG_HASH_ALL.to_u8());
    ScriptBuilder::new().add_data(&sig).unwrap().drain()
}
pub fn fund_cb(kp: Keypair) -> InputSigScript<'static> {
    InputSigScript::with_transaction(move |tx, idx| sign_idx_any(tx, idx, &kp))
}
fn sign_idx_any<T: AsRef<Transaction>>(tx: &MutableTransaction<T>, idx: usize, kp: &Keypair) -> Vec<u8> {
    let reused = SigHashReusedValuesUnsync::new();
    let h = calc_schnorr_signature_hash(&tx.as_verifiable(), idx, SIG_HASH_ALL, &reused);
    let msg = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
    let mut sig = kp.sign_schnorr(msg).as_ref().to_vec();
    sig.push(SIG_HASH_ALL.to_u8());
    ScriptBuilder::new().add_data(&sig).unwrap().drain()
}

pub struct H { pub kp: Keypair, pub pk: Vec<u8>, pub my_spk: ScriptPublicKey, pub builder: TxBuilder<'static>, pub dir: String }
/// `app`: path to app.ag; `oracle`: optional path to oracle.ag (alias oracle_feed).
pub fn setup(app: &str, oracle: Option<&str>) -> H {
    let dir = env("TN10_DIR");
    let sk = SecretKey::from_slice(&unhex(std::fs::read_to_string(format!("{dir}/tn10_key.hex")).unwrap().trim())).unwrap();
    let kp = Keypair::from_secret_key(&Secp256k1::new(), &sk);
    let pk = kp.x_only_public_key().0.serialize().to_vec();
    let addr = Address::try_from(std::fs::read_to_string(format!("{dir}/tn10_address.txt")).unwrap().trim()).unwrap();
    let out = std::env::temp_dir().join(format!("tn10_t4_{}", std::process::id()));
    let v = Box::leak(Box::new(argent::build_file(app, &out.join("v")).unwrap()));
    let mut b = ArtifactBundle::new(&*v).unwrap();
    if let Some(o) = oracle {
        let o = Box::leak(Box::new(argent::build_file(o, &out.join("o")).unwrap()));
        b = b.with_app(&std::env::var("T4_ALIAS").unwrap_or("oracle_feed".into()), &*o).unwrap();
    }
    H { kp, pk, my_spk: pay_to_address_script(&addr), builder: TxBuilder::from_bundle(&b).unwrap(), dir }
}
impl H {
    /// funding UTXO: file "txid index amount"
    pub fn fund(&self) -> (String, u32, u64) {
        let p = std::env::var("FUND_FILE").unwrap_or(format!("{}/t4_fund.txt", self.dir));
        let s = std::fs::read_to_string(p).unwrap();
        let f: Vec<&str> = s.split_whitespace().collect();
        (f[0].to_string(), f[1].parse().unwrap(), f[2].parse().unwrap())
    }
    pub fn fund_entry(&self, amt: u64) -> UtxoEntry { UtxoEntry::new(amt, self.my_spk.clone(), 0, false, None) }
    /// write tx json + next-fund record; print masses
    pub fn emit(&self, tx: &Transaction, name: &str, change_idx: u32, change: u64) {
        std::fs::write(format!("{}/{name}.json", self.dir), serde_json::to_string(tx).unwrap()).unwrap();
        std::fs::write(format!("{}/t4_fund_next.txt", self.dir), format!("{} {} {}", tx.id(), change_idx, change)).unwrap();
        let m = MassCalculator::new_with_consensus_params(&MAINNET_PARAMS).calc_non_contextual_masses(tx);
        println!("TXID {}", tx.id());
        println!("LOCAL_MASS compute {} transient {} inputs {} outputs {} json={name}.json", m.compute_mass, m.transient_mass, tx.inputs.len(), tx.outputs.len());
    }
}
impl H {
    pub fn emit_e(&self, tx: &Transaction, name: &str, change_idx: u32, change: u64, entries: Vec<UtxoEntry>) {
        self.emit(tx, name, change_idx, change);
        let m = MassCalculator::new_with_consensus_params(&MAINNET_PARAMS);
        let mt = MutableTransaction::with_entries(tx.clone(), entries);
        println!("STORAGE_MASS {:?}", m.calc_contextual_masses(&mt.as_verifiable()).map(|c| c.storage_mass));
    }
}
pub fn st(pairs: Vec<(&str, ArtifactValue)>) -> BTreeMap<String, ArtifactValue> { pairs.into_iter().map(|(k, v)| (k.to_string(), v)).collect() }
