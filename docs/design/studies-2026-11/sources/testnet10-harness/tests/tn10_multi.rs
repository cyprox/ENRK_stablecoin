//! Scratch (testnet-10): create M vaults in one genesis, then liquidate all of them in ONE transaction reading ONE price UTXO.
use argent::builder::{ArtifactBundle, ArtifactValue, EntryCall, InputSigScript, TxBuilder, TxContext};
use kaspa_addresses::Address;
use kaspa_consensus_core::{
    Hash,
    hashing::{covenant_id::covenant_id, sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash}, sighash_type::SIG_HASH_ALL},
    tx::{CovenantBinding, MutableTransaction, ScriptPublicKey, Transaction, TransactionId, TransactionOutpoint, UtxoEntry},
};
use kaspa_txscript::{pay_to_address_script, script_builder::ScriptBuilder};
use secp256k1::{Keypair, Secp256k1, SecretKey};
use std::collections::BTreeMap;

fn unhex(s: &str) -> Vec<u8> { (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect() }
fn hex(b: &[u8]) -> String { b.iter().map(|x| format!("{x:02x}")).collect() }
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
struct C { kp: Keypair, pk: Vec<u8>, my_spk: ScriptPublicKey, builder: TxBuilder<'static>, dir: String }
fn setup() -> C {
    let dir = env("TN10_DIR");
    let sk = SecretKey::from_slice(&unhex(std::fs::read_to_string(format!("{dir}/tn10_key.hex")).unwrap().trim())).unwrap();
    let kp = Keypair::from_secret_key(&Secp256k1::new(), &sk);
    let pk = kp.x_only_public_key().0.serialize().to_vec();
    let addr = Address::try_from(std::fs::read_to_string(format!("{dir}/tn10_address.txt")).unwrap().trim()).unwrap();
    let cdir = env("COSPEND_DIR");
    let out = std::env::temp_dir().join(format!("tn10_multi_{}", std::process::id()));
    let v = Box::leak(Box::new(argent::build_file(format!("{cdir}/vault.ag"), &out.join("v")).unwrap()));
    let o = Box::leak(Box::new(argent::build_file(format!("{cdir}/oracle.ag"), &out.join("o")).unwrap()));
    let b = ArtifactBundle::new(&*v).unwrap().with_app("oracle_feed", &*o).unwrap();
    C { kp, pk, my_spk: pay_to_address_script(&addr), builder: TxBuilder::from_bundle(&b).unwrap(), dir }
}
fn fund_cb(kp: Keypair) -> InputSigScript<'static> {
    InputSigScript::with_transaction(move |tx, idx| ScriptBuilder::new().add_data(&sign(tx, idx, &kp)).unwrap().drain())
}
fn vstate(pk: &[u8], oid: &[u8; 32], debt: i64) -> BTreeMap<String, ArtifactValue> {
    let mut s = BTreeMap::new();
    s.insert("owner".to_string(), ArtifactValue::Bytes(pk.to_vec()));
    s.insert("oracle_covid".to_string(), ArtifactValue::Bytes(oid.to_vec()));
    s.insert("debt".to_string(), ArtifactValue::Int(debt));
    s
}

#[test]
fn vault_genesis_multi() {
    let c = setup();
    let m: usize = env("M").parse().unwrap();
    let collateral: u64 = env("COLLATERAL").parse().unwrap();
    let debt: i64 = env("DEBT").parse().unwrap();
    let fee: u64 = env("FEE").parse().unwrap();
    let oid: [u8; 32] = unhex(&env("ORACLE_ID")).try_into().unwrap();
    let (ft, fi, fa): (String, u32, u64) = (env("FUND_TXID"), env("FUND_INDEX").parse().unwrap(), env("FUND_AMOUNT").parse().unwrap());
    let funding = UtxoEntry::new(fa, c.my_spk.clone(), 0, false, None);
    let mut ctx = TxContext::new().input(op(&ft, fi), funding, fund_cb(c.kp.clone()), 0);
    let st = vstate(&c.pk, &oid, debt);
    for _ in 0..m { ctx = ctx.actor_genesis_output(0, "launch::vault", "Vault", st.clone(), collateral); }
    let change = fa - collateral * m as u64 - fee;
    ctx = ctx.output(c.my_spk.clone(), None, change);
    let tx = match c.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let outpoint = op(&ft, fi);
    let ids: Vec<_> = tx.outputs.iter().enumerate().filter(|(_, o)| o.covenant.is_some()).collect();
    let cid = covenant_id(outpoint, ids.iter().map(|(i, o)| (*i as u32, *o)));
    std::fs::write(format!("{}/tx_vaultgen.json", c.dir), serde_json::to_string(&tx).unwrap()).unwrap();
    std::fs::write(format!("{}/fund.txt", c.dir), format!("{} {} {}", tx.id(), m, change)).unwrap();
    println!("TXID {} VAULT_COVID {}", tx.id(), hex(cid.as_bytes().as_slice()));
}

#[test]
fn liquidate_multi() {
    let c = setup();
    let m: usize = env("M").parse().unwrap();
    let collateral: u64 = env("COLLATERAL").parse().unwrap();
    let debt: i64 = env("DEBT").parse().unwrap();
    let fee: u64 = env("FEE").parse().unwrap();
    let oid_arr: [u8; 32] = unhex(&env("ORACLE_ID")).try_into().unwrap();
    let oracle_id = Hash::from_bytes(oid_arr);
    let vault_id = Hash::from_bytes(unhex(&env("VAULT_COVID")).try_into().unwrap());
    let price: u64 = env("PRICE").parse().unwrap();
    let vtx = env("VAULT_TXID");
    let (ft, fi, fa): (String, u32, u64) = (env("FUND_TXID"), env("FUND_INDEX").parse().unwrap(), env("FUND_AMOUNT").parse().unwrap());
    let st = vstate(&c.pk, &oid_arr, debt);
    let mut os = BTreeMap::new();
    os.insert("publisher".to_string(), ArtifactValue::Bytes(c.pk.clone()));
    os.insert("round".to_string(), ArtifactValue::Int(1));
    let mut ctx = TxContext::new();
    for i in 0..m {
        let utxo = c.builder.covenant_utxo("Vault", st.clone(), collateral, 0, false, Some(vault_id)).unwrap();
        ctx = ctx.actor_input("Vault", st.clone(), EntryCall::new("liquidate"), op(&vtx, i as u32), utxo, 0);
    }
    let m2: usize = std::env::var("M2").ok().and_then(|v| v.parse().ok()).unwrap_or(0);
    if m2 > 0 {
        let vault_id2 = Hash::from_bytes(unhex(&env("VAULT_COVID2")).try_into().unwrap());
        let vtx2 = env("VAULT_TXID2");
        for i in 0..m2 {
            let utxo = c.builder.covenant_utxo("Vault", st.clone(), collateral, 0, false, Some(vault_id2)).unwrap();
            ctx = ctx.actor_input("Vault", st.clone(), EntryCall::new("liquidate"), op(&vtx2, i as u32), utxo, 0);
        }
    }
    let m = m + m2;
    let oracle_utxo = c.builder.covenant_utxo("oracle_feed::PriceRound", os.clone(), price, 0, false, Some(oracle_id)).unwrap();
    ctx = ctx.actor_input("oracle_feed::PriceRound", os.clone(), EntryCall::new("use"), op(&env("ORACLE_TXID"), env("ORACLE_INDEX").parse().unwrap()), oracle_utxo, 0);
    let funding = UtxoEntry::new(fa, c.my_spk.clone(), 0, false, None);
    ctx = ctx.input(op(&ft, fi), funding, fund_cb(c.kp.clone()), 0);
    ctx = ctx.actor_output("oracle_feed::PriceRound", os.clone(), CovenantBinding::new(m as u16, oracle_id), price);
    let payout = collateral * m as u64 + fa - fee;
    ctx = ctx.output(c.my_spk.clone(), None, payout);
    let tx = match c.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    std::fs::write(format!("{}/tx_liqmulti.json", c.dir), serde_json::to_string(&tx).unwrap()).unwrap();
    println!("TXID {} inputs {}", tx.id(), tx.inputs.len());
}
