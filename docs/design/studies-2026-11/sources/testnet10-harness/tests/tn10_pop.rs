//! Scratch (testnet-10): grow an oracle population by sweep batches and spend the whole population in one round.
use argent::builder::{args, ArtifactBundle, ArtifactValue, EntryCall, InputSigScript, TxBuilder, TxContext};
use kaspa_addresses::Address;
use kaspa_consensus_core::{
    Hash,
    hashing::{sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash}, sighash_type::SIG_HASH_ALL},
    tx::{CovenantBinding, MutableTransaction, ScriptPublicKey, Transaction, TransactionId, TransactionOutpoint, UtxoEntry},
};
use kaspa_txscript::{pay_to_address_script, script_builder::ScriptBuilder};
use secp256k1::{Keypair, Secp256k1, SecretKey};
use std::collections::BTreeMap;

fn unhex(s: &str) -> Vec<u8> { (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect() }
fn env(k: &str) -> String { std::env::var(k).unwrap_or_else(|_| panic!("missing env {k}")) }
fn op(txid: &str, i: u32) -> TransactionOutpoint { TransactionOutpoint::new(TransactionId::from_bytes(unhex(txid).try_into().unwrap()), i) }
fn sign<T: AsRef<Transaction>>(tx: &MutableTransaction<T>, idx: usize, kp: &Keypair) -> Vec<u8> {
    let reused = SigHashReusedValuesUnsync::new();
    let h = calc_schnorr_signature_hash(&tx.as_verifiable(), idx, SIG_HASH_ALL, &reused);
    let msg = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
    let mut sig = kp.sign_schnorr(msg).as_ref().to_vec();
    sig.push(SIG_HASH_ALL.to_u8());
    sig
}

struct Ctx { kp: Keypair, pk: Vec<u8>, my_spk: ScriptPublicKey, builder: TxBuilder<'static>, oracle_id: Hash, dir: String }

fn setup() -> Ctx {
    let dir = env("TN10_DIR");
    let sk = SecretKey::from_slice(&unhex(std::fs::read_to_string(format!("{dir}/tn10_key.hex")).unwrap().trim())).unwrap();
    let kp = Keypair::from_secret_key(&Secp256k1::new(), &sk);
    let pk = kp.x_only_public_key().0.serialize().to_vec();
    let addr = Address::try_from(std::fs::read_to_string(format!("{dir}/tn10_address.txt")).unwrap().trim()).unwrap();
    let my_spk = pay_to_address_script(&addr);
    let cdir = env("COSPEND_DIR");
    let out = std::env::temp_dir().join(format!("tn10_pop_{}", std::process::id()));
    let v = Box::leak(Box::new(argent::build_file(format!("{cdir}/vault.ag"), &out.join("v")).unwrap()));
    let o = Box::leak(Box::new(argent::build_file(format!("{cdir}/oracle.ag"), &out.join("o")).unwrap()));
    let bundle = ArtifactBundle::new(&*v).unwrap().with_app("oracle_feed", &*o).unwrap();
    let builder = TxBuilder::from_bundle(&bundle).unwrap();
    let oracle_id = Hash::from_bytes(unhex(&env("ORACLE_ID")).try_into().unwrap());
    Ctx { kp, pk, my_spk, builder, oracle_id, dir }
}

fn ostate(pk: &[u8], round: i64) -> BTreeMap<String, ArtifactValue> {
    let mut s = BTreeMap::new();
    s.insert("publisher".to_string(), ArtifactValue::Bytes(pk.to_vec()));
    s.insert("round".to_string(), ArtifactValue::Int(round));
    s
}

fn fund_cb(kp: Keypair) -> InputSigScript<'static> {
    InputSigScript::with_transaction(move |tx, idx| ScriptBuilder::new().add_data(&sign(tx, idx, &kp)).unwrap().drain())
}

#[derive(Clone, Debug)]
struct Pop { txid: String, index: u32, value: u64, round: i64 }

fn read_pop(path: &str) -> Vec<Pop> {
    let v: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap();
    v.as_array().unwrap().iter().map(|e| Pop { txid: e["txid"].as_str().unwrap().into(), index: e["index"].as_u64().unwrap() as u32, value: e["value"].as_u64().unwrap(), round: e["round"].as_i64().unwrap() }).collect()
}
fn write_pop(path: &str, p: &[Pop]) {
    let v: Vec<_> = p.iter().map(|e| serde_json::json!({"txid": e.txid, "index": e.index, "value": e.value, "round": e.round})).collect();
    std::fs::write(path, serde_json::to_string(&v).unwrap()).unwrap();
}

#[test]
fn sweep_batch() {
    let c = setup();
    let pop = read_pop(&env("POP"));
    let m: usize = env("M").parse().unwrap();
    let fee: u64 = env("FEE").parse().unwrap();
    let (ft, fi, fa): (String, u32, u64) = (env("FUND_TXID"), env("FUND_INDEX").parse().unwrap(), env("FUND_AMOUNT").parse().unwrap());
    let minv: u64 = std::env::var("MINV").ok().and_then(|v| v.parse().ok()).unwrap_or(2_000_000_000);
    let sel: Vec<Pop> = pop.iter().filter(|p| p.value >= minv).take(m).cloned().collect();
    assert_eq!(sel.len(), m, "not enough entries above MINV");
    let rest: Vec<Pop> = pop.iter().filter(|p| !sel.iter().any(|s| s.txid == p.txid && s.index == p.index)).cloned().collect();
    let mut ctx = TxContext::new();
    for p in &sel {
        let st = ostate(&c.pk, p.round);
        let utxo = c.builder.covenant_utxo("oracle_feed::PriceRound", st.clone(), p.value, 0, false, Some(c.oracle_id)).unwrap();
        let kp = c.kp.clone();
        ctx = ctx.actor_input("oracle_feed::PriceRound", st, EntryCall::new("sweep").args_with(move |tx, i| args![sign(tx, i, &kp)]), op(&p.txid, p.index), utxo, 0);
    }
    let funding = UtxoEntry::new(fa, c.my_spk.clone(), 0, false, None);
    ctx = ctx.input(op(&ft, fi), funding, fund_cb(c.kp.clone()), 0);
    for (i, p) in sel.iter().enumerate() {
        let next = ostate(&c.pk, p.round + 1);
        let half = p.value / 2;
        ctx = ctx.actor_output("oracle_feed::PriceRound", next.clone(), CovenantBinding::new(i as u16, c.oracle_id), half);
        ctx = ctx.actor_output("oracle_feed::PriceRound", next.clone(), CovenantBinding::new(i as u16, c.oracle_id), p.value - half);
    }
    let change = fa - fee;
    ctx = ctx.output(c.my_spk.clone(), None, change);
    let tx = match c.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let id = tx.id().to_string();
    let mut np = rest;
    for (i, p) in sel.iter().enumerate() {
        np.push(Pop { txid: id.clone(), index: (2 * i) as u32, value: p.value / 2, round: p.round + 1 });
        np.push(Pop { txid: id.clone(), index: (2 * i + 1) as u32, value: p.value - p.value / 2, round: p.round + 1 });
    }
    write_pop(&env("OUT_POP"), &np);
    std::fs::write(format!("{}/tx_sweep.json", c.dir), serde_json::to_string(&tx).unwrap()).unwrap();
    std::fs::write(format!("{}/fund.txt", c.dir), format!("{} {} {}", id, 2 * m, change)).unwrap();
    println!("TXID {id} POP {}", np.len());
}

#[test]
fn round_pop() {
    let c = setup();
    let all = read_pop(&env("POP"));
    let val: Option<u64> = std::env::var("VAL").ok().and_then(|v| v.parse().ok());
    let pop: Vec<Pop> = all.iter().filter(|p| val.map_or(true, |v| p.value == v)).cloned().collect();
    let others: Vec<Pop> = all.iter().filter(|p| !val.map_or(true, |v| p.value == v)).cloned().collect();
    let fee: u64 = env("FEE").parse().unwrap();
    let (ft, fi, fa): (String, u32, u64) = (env("FUND_TXID"), env("FUND_INDEX").parse().unwrap(), env("FUND_AMOUNT").parse().unwrap());
    let mut ctx = TxContext::new();
    for p in &pop {
        let st = ostate(&c.pk, p.round);
        let utxo = c.builder.covenant_utxo("oracle_feed::PriceRound", st.clone(), p.value, 0, false, Some(c.oracle_id)).unwrap();
        ctx = ctx.actor_input("oracle_feed::PriceRound", st, EntryCall::new("use"), op(&p.txid, p.index), utxo, 0);
    }
    let funding = UtxoEntry::new(fa, c.my_spk.clone(), 0, false, None);
    ctx = ctx.input(op(&ft, fi), funding, fund_cb(c.kp.clone()), 0);
    for (i, p) in pop.iter().enumerate() {
        ctx = ctx.actor_output("oracle_feed::PriceRound", ostate(&c.pk, p.round), CovenantBinding::new(i as u16, c.oracle_id), p.value);
    }
    let change = fa - fee;
    ctx = ctx.output(c.my_spk.clone(), None, change);
    let tx = match c.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let id = tx.id().to_string();
    let mut np: Vec<Pop> = pop.iter().enumerate().map(|(i, p)| Pop { txid: id.clone(), index: i as u32, value: p.value, round: p.round }).collect();
    np.extend(others);
    write_pop(&env("OUT_POP"), &np);
    std::fs::write(format!("{}/tx_round.json", c.dir), serde_json::to_string(&tx).unwrap()).unwrap();
    std::fs::write(format!("{}/fund.txt", c.dir), format!("{} {} {}", id, pop.len(), change)).unwrap();
    println!("TXID {id} N {}", pop.len());
}

#[test]
fn split_funding() {
    let c = setup();
    let k: usize = env("K").parse().unwrap();
    let v: u64 = env("V").parse().unwrap();
    let fee: u64 = env("FEE").parse().unwrap();
    let (ft, fi, fa): (String, u32, u64) = (env("FUND_TXID"), env("FUND_INDEX").parse().unwrap(), env("FUND_AMOUNT").parse().unwrap());
    let funding = UtxoEntry::new(fa, c.my_spk.clone(), 0, false, None);
    let mut ctx = TxContext::new().input(op(&ft, fi), funding, fund_cb(c.kp.clone()), 0);
    for _ in 0..k { ctx = ctx.output(c.my_spk.clone(), None, v); }
    let change = fa - v * k as u64 - fee;
    ctx = ctx.output(c.my_spk.clone(), None, change);
    let tx = match c.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let id = tx.id().to_string();
    std::fs::write(format!("{}/tx_split.json", c.dir), serde_json::to_string(&tx).unwrap()).unwrap();
    std::fs::write(format!("{}/fund.txt", c.dir), format!("{} {} {}", id, k, change)).unwrap();
    println!("TXID {id}");
}
