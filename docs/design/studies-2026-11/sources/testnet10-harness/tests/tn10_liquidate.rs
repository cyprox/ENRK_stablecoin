//! Scratch (testnet-10): build the real liquidation transaction (vault + oracle price UTXO).
use argent::builder::{ArtifactBundle, ArtifactValue, EntryCall, TxBuilder, TxContext};
use kaspa_addresses::Address;
use kaspa_consensus_core::{
    Hash,
    tx::{CovenantBinding, ScriptPublicKey, TransactionId, TransactionOutpoint},
};
use kaspa_txscript::pay_to_address_script;
use std::collections::BTreeMap;

fn unhex(s: &str) -> Vec<u8> { (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect() }
fn env(k: &str) -> String { std::env::var(k).unwrap_or_else(|_| panic!("missing env {k}")) }
fn op(txid: &str, i: u32) -> TransactionOutpoint { TransactionOutpoint::new(TransactionId::from_bytes(unhex(txid).try_into().unwrap()), i) }

#[test]
fn liquidate_onchain() {
    let dir = env("TN10_DIR");
    let addr = Address::try_from(std::fs::read_to_string(format!("{dir}/tn10_address.txt")).unwrap().trim()).unwrap();
    let my_spk: ScriptPublicKey = pay_to_address_script(&addr);
    let pk = {
        use secp256k1::{Keypair, Secp256k1, SecretKey};
        let sk = SecretKey::from_slice(&unhex(std::fs::read_to_string(format!("{dir}/tn10_key.hex")).unwrap().trim())).unwrap();
        Keypair::from_secret_key(&Secp256k1::new(), &sk).x_only_public_key().0.serialize().to_vec()
    };
    let cdir = env("COSPEND_DIR");
    let out = std::env::temp_dir().join(format!("tn10_liq_{}", std::process::id()));
    let v = Box::leak(Box::new(argent::build_file(format!("{cdir}/vault.ag"), &out.join("v")).unwrap()));
    let o = Box::leak(Box::new(argent::build_file(format!("{cdir}/oracle.ag"), &out.join("o")).unwrap()));
    let bundle = ArtifactBundle::new(&*v).unwrap().with_app("oracle_feed", &*o).unwrap();
    let builder = TxBuilder::from_bundle(&bundle).unwrap();

    let oracle_id = Hash::from_bytes(unhex(&env("ORACLE_ID")).try_into().unwrap());
    let vault_id = Hash::from_bytes(unhex(&env("VAULT_ID")).try_into().unwrap());
    let collateral: u64 = env("COLLATERAL").parse().unwrap();
    let debt: i64 = env("DEBT").parse().unwrap();
    let price: u64 = env("PRICE").parse().unwrap();
    let fee: u64 = env("FEE").parse().unwrap();

    let mut vs = BTreeMap::new();
    vs.insert("owner".to_string(), ArtifactValue::Bytes(pk.clone()));
    vs.insert("oracle_covid".to_string(), ArtifactValue::Bytes(oracle_id.as_bytes().to_vec()));
    vs.insert("debt".to_string(), ArtifactValue::Int(debt));
    let mut os = BTreeMap::new();
    os.insert("publisher".to_string(), ArtifactValue::Bytes(pk));
    os.insert("round".to_string(), ArtifactValue::Int(1));
    if std::env::var("COSPEND_B").is_ok() { os.insert("price".to_string(), ArtifactValue::Int(env("PRICE").parse::<i64>().unwrap())); }

    let vault_utxo = builder.covenant_utxo("Vault", vs.clone(), collateral, 0, false, Some(vault_id)).unwrap();
    let oracle_utxo = builder.covenant_utxo("oracle_feed::PriceRound", os.clone(), price, 0, false, Some(oracle_id)).unwrap();
    let ctx = TxContext::new()
        .actor_input("Vault", vs.clone(), EntryCall::new("liquidate"), op(&env("VAULT_TXID"), 0), vault_utxo, 0)
        .actor_input("oracle_feed::PriceRound", os.clone(), EntryCall::new("use"), op(&env("ORACLE_TXID"), 0), oracle_utxo, 0)
        .actor_output("oracle_feed::PriceRound", os.clone(), CovenantBinding::new(1, oracle_id), price)
        .output(my_spk, None, collateral - fee);
    let tx = builder.build(&ctx).expect("liquidation builds");
    println!("TXID {}", tx.id());
    println!("COMMITS {:?} {:?}", tx.inputs[0].compute_commit, tx.inputs[1].compute_commit);
    std::fs::write(format!("{dir}/tx_liquidate.json"), serde_json::to_string(&tx).unwrap()).unwrap();
}
