//! Scratch (testnet-10): spend N oracle price UTXOs through `use` and recreate them, paying the fee from an ordinary input.
use argent::builder::{ArtifactBundle, ArtifactValue, EntryCall, InputSigScript, TxBuilder, TxContext};
use kaspa_addresses::Address;
use kaspa_consensus_core::{
    Hash,
    hashing::{sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash}, sighash_type::SIG_HASH_ALL},
    tx::{CovenantBinding, ScriptPublicKey, TransactionId, TransactionOutpoint, UtxoEntry},
};
use kaspa_txscript::{pay_to_address_script, script_builder::ScriptBuilder};
use secp256k1::{Keypair, Secp256k1, SecretKey};
use std::collections::BTreeMap;

fn unhex(s: &str) -> Vec<u8> { (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect() }
fn env(k: &str) -> String { std::env::var(k).unwrap_or_else(|_| panic!("missing env {k}")) }
fn op(txid: &str, i: u32) -> TransactionOutpoint { TransactionOutpoint::new(TransactionId::from_bytes(unhex(txid).try_into().unwrap()), i) }

#[test]
fn round() {
    let dir = env("TN10_DIR");
    let sk = SecretKey::from_slice(&unhex(std::fs::read_to_string(format!("{dir}/tn10_key.hex")).unwrap().trim())).unwrap();
    let kp = Keypair::from_secret_key(&Secp256k1::new(), &sk);
    let pk = kp.x_only_public_key().0.serialize().to_vec();
    let addr = Address::try_from(std::fs::read_to_string(format!("{dir}/tn10_address.txt")).unwrap().trim()).unwrap();
    let my_spk: ScriptPublicKey = pay_to_address_script(&addr);
    let cdir = env("COSPEND_DIR");
    let out = std::env::temp_dir().join(format!("tn10_round_{}", std::process::id()));
    let v = Box::leak(Box::new(argent::build_file(format!("{cdir}/vault.ag"), &out.join("v")).unwrap()));
    let o = Box::leak(Box::new(argent::build_file(format!("{cdir}/oracle.ag"), &out.join("o")).unwrap()));
    let bundle = ArtifactBundle::new(&*v).unwrap().with_app("oracle_feed", &*o).unwrap();
    let builder = TxBuilder::from_bundle(&bundle).unwrap();

    let oracle_id = Hash::from_bytes(unhex(&env("ORACLE_ID")).try_into().unwrap());
    let n: u32 = env("N").parse().unwrap();
    let price: u64 = env("PRICE").parse().unwrap();
    let fee: u64 = env("FEE").parse().unwrap();
    let genesis_txid = env("ORACLE_TXID");
    let mut os = BTreeMap::new();
    os.insert("publisher".to_string(), ArtifactValue::Bytes(pk));
    os.insert("round".to_string(), ArtifactValue::Int(1));
    if std::env::var("COSPEND_B").is_ok() { os.insert("price".to_string(), ArtifactValue::Int(env("PRICE").parse::<i64>().unwrap())); }

    let fund_amount: u64 = env("FUND_AMOUNT").parse().unwrap();
    let funding = UtxoEntry::new(fund_amount, my_spk.clone(), 0, false, None);
    let kp2 = kp.clone();
    let sig_cb = InputSigScript::with_transaction(move |tx, idx| {
        let reused = SigHashReusedValuesUnsync::new();
        let h = calc_schnorr_signature_hash(&tx.as_verifiable(), idx, SIG_HASH_ALL, &reused);
        let msg = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
        let mut sig = kp2.sign_schnorr(msg).as_ref().to_vec();
        sig.push(SIG_HASH_ALL.to_u8());
        ScriptBuilder::new().add_data(&sig).unwrap().drain()
    });
    let mut ctx = TxContext::new();
    for i in 0..n {
        let utxo = builder.covenant_utxo("oracle_feed::PriceRound", os.clone(), price, 0, false, Some(oracle_id)).unwrap();
        ctx = ctx.actor_input("oracle_feed::PriceRound", os.clone(), EntryCall::new("use"), op(&genesis_txid, i), utxo, 0);
    }
    ctx = ctx.input(op(&env("FUND_TXID"), env("FUND_INDEX").parse().unwrap()), funding, sig_cb, 0);
    for i in 0..n {
        ctx = ctx.actor_output("oracle_feed::PriceRound", os.clone(), CovenantBinding::new(i as u16, oracle_id), price);
    }
    ctx = ctx.output(my_spk, None, fund_amount - fee);
    let tx = match builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    println!("TXID {}", tx.id());
    println!("CHANGE_AMOUNT {}", fund_amount - fee);
    std::fs::write(format!("{dir}/tx_round.json"), serde_json::to_string(&tx).unwrap()).unwrap();
}
