//! Scratch (testnet-10 only): build a covenant genesis transaction for the ENRK oracle or vault.
//!   STEP=oracle|vault  COSPEND_DIR=<fixed dir>  TN10_DIR=<dir with key>
//!   IN_TXID IN_INDEX IN_AMOUNT IN_DAA describe the funding UTXO; N, PRICE (oracle) / COLLATERAL, DEBT, ORACLE_ID (vault)
use argent::builder::{ArtifactBundle, ArtifactValue, InputSigScript, TxBuilder, TxContext};
use kaspa_addresses::Address;
use kaspa_consensus_core::{
    hashing::{covenant_id::covenant_id, sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash}, sighash_type::SIG_HASH_ALL},
    tx::{MutableTransaction, ScriptPublicKey, TransactionId, TransactionOutpoint, UtxoEntry},
};
use kaspa_txscript::{pay_to_address_script, script_builder::ScriptBuilder};
use secp256k1::{Keypair, Secp256k1, SecretKey};
use std::collections::BTreeMap;

fn unhex(s: &str) -> Vec<u8> { (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect() }
fn hex(b: &[u8]) -> String { b.iter().map(|x| format!("{x:02x}")).collect() }
fn env(k: &str) -> String { std::env::var(k).unwrap_or_else(|_| panic!("missing env {k}")) }

#[test]
fn launch() {
    let dir = env("TN10_DIR");
    let sk = SecretKey::from_slice(&unhex(std::fs::read_to_string(format!("{dir}/tn10_key.hex")).unwrap().trim())).unwrap();
    let kp = Keypair::from_secret_key(&Secp256k1::new(), &sk);
    let pk = kp.x_only_public_key().0.serialize().to_vec();
    let addr = Address::try_from(std::fs::read_to_string(format!("{dir}/tn10_address.txt")).unwrap().trim()).unwrap();
    let my_spk: ScriptPublicKey = pay_to_address_script(&addr);

    let cdir = env("COSPEND_DIR");
    let out = std::env::temp_dir().join(format!("tn10_launch_{}", std::process::id()));
    let v = Box::leak(Box::new(argent::build_file(format!("{cdir}/vault.ag"), &out.join("v")).unwrap()));
    let o = Box::leak(Box::new(argent::build_file(format!("{cdir}/oracle.ag"), &out.join("o")).unwrap()));
    let bundle = ArtifactBundle::new(&*v).unwrap().with_app("oracle_feed", &*o).unwrap();
    let builder = TxBuilder::from_bundle(&bundle).unwrap();

    let txid = env("IN_TXID");
    let index: u32 = env("IN_INDEX").parse().unwrap();
    let amount: u64 = env("IN_AMOUNT").parse().unwrap();
    let daa: u64 = env("IN_DAA").parse().unwrap();
    let fee: u64 = env("FEE").parse().unwrap();
    let outpoint = TransactionOutpoint::new(TransactionId::from_bytes(unhex(&txid).try_into().unwrap()), index);
    let funding = UtxoEntry::new(amount, my_spk.clone(), daa, false, None);

    let step = env("STEP");
    let kp2 = kp.clone();
    let sig_cb = InputSigScript::with_transaction(move |tx, idx| {
        let reused = SigHashReusedValuesUnsync::new();
        let h = calc_schnorr_signature_hash(&tx.as_verifiable(), idx, SIG_HASH_ALL, &reused);
        let msg = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
        let mut sig = kp2.sign_schnorr(msg).as_ref().to_vec();
        sig.push(SIG_HASH_ALL.to_u8());
        ScriptBuilder::new().add_data(&sig).unwrap().drain()
    });
    let mut ctx = TxContext::new().input(outpoint, funding.clone(), sig_cb, 0);
    let mut spent = 0u64;
    if step == "oracle" {
        let n: usize = env("N").parse().unwrap();
        let price: u64 = env("PRICE").parse().unwrap();
        let mut st = BTreeMap::new();
        st.insert("publisher".to_string(), ArtifactValue::Bytes(pk.clone()));
        st.insert("round".to_string(), ArtifactValue::Int(1));
        if std::env::var("COSPEND_B").is_ok() { st.insert("price".to_string(), ArtifactValue::Int(price as i64)); }
        for _ in 0..n {
            ctx = ctx.actor_genesis_output(0, "launch::oracle", "oracle_feed::PriceRound", st.clone(), price);
            spent += price;
        }
    } else {
        let oracle_id: [u8; 32] = unhex(&env("ORACLE_ID")).try_into().unwrap();
        let collateral: u64 = env("COLLATERAL").parse().unwrap();
        let debt: i64 = env("DEBT").parse().unwrap();
        let mut st = BTreeMap::new();
        st.insert("owner".to_string(), ArtifactValue::Bytes(pk.clone()));
        st.insert("oracle_covid".to_string(), ArtifactValue::Bytes(oracle_id.to_vec()));
        st.insert("debt".to_string(), ArtifactValue::Int(debt));
        ctx = ctx.actor_genesis_output(0, "launch::vault", "Vault", st, collateral);
        spent += collateral;
    }
    let change = amount - spent - fee;
    ctx = ctx.output(my_spk.clone(), None, change);

    let tx = builder.build(&ctx).expect("genesis tx builds");
    println!("VERSION {} INPUT_COMMIT {:?}", tx.version, tx.inputs[0].compute_commit);
    let _ = &funding;
    // covenant id of the genesis group (public chain data)
    let ids: Vec<_> = tx.outputs.iter().enumerate().filter(|(_, o)| o.covenant.is_some()).collect();
    let cid = covenant_id(outpoint, ids.iter().map(|(i, o)| (*i as u32, *o)));
    println!("COVENANT_ID {}", hex(cid.as_bytes().as_slice()));
    println!("TXID {}", tx.id());
    println!("CHANGE_INDEX {}", tx.outputs.len() - 1);
    println!("OUTPUTS {} CHANGE {}", tx.outputs.len(), change);
    std::fs::write(format!("{dir}/tx_{step}.json"), serde_json::to_string(&tx).unwrap()).unwrap();
}
