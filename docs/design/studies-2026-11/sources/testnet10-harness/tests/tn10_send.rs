//! Scratch: build+sign a plain self-send on testnet-10 and write the REST body to a file.
use kaspa_addresses::Address;
use kaspa_consensus_core::{
    hashing::{sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash}, sighash_type::SIG_HASH_ALL},
    subnets::SUBNETWORK_ID_NATIVE,
    tx::{MutableTransaction, ScriptPublicKey, Transaction, TransactionInput, TransactionOutpoint, TransactionId, TransactionOutput, UtxoEntry},
};
use kaspa_txscript::{pay_to_address_script, script_builder::ScriptBuilder};
use secp256k1::{Keypair, Secp256k1, SecretKey};

fn unhex(s: &str) -> Vec<u8> { (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect() }
fn hex(b: &[u8]) -> String { b.iter().map(|x| format!("{x:02x}")).collect() }

#[test]
fn build_self_send() {
    let dir = std::env::var("TN10_DIR").unwrap();
    let txid = std::env::var("IN_TXID").unwrap();
    let index: u32 = std::env::var("IN_INDEX").unwrap().parse().unwrap();
    let amount: u64 = std::env::var("IN_AMOUNT").unwrap().parse().unwrap();
    let daa: u64 = std::env::var("IN_DAA").unwrap().parse().unwrap();
    let send: u64 = std::env::var("SEND").unwrap().parse().unwrap();
    let fee: u64 = std::env::var("FEE").unwrap().parse().unwrap();

    let sk = SecretKey::from_slice(&unhex(std::fs::read_to_string(format!("{dir}/tn10_key.hex")).unwrap().trim())).unwrap();
    let kp = Keypair::from_secret_key(&Secp256k1::new(), &sk);
    let addr = Address::try_from(std::fs::read_to_string(format!("{dir}/tn10_address.txt")).unwrap().trim()).unwrap();
    let spk: ScriptPublicKey = pay_to_address_script(&addr);

    let outpoint = TransactionOutpoint::new(TransactionId::from_bytes(unhex(&txid).try_into().unwrap()), index);
    let input = TransactionInput::new(outpoint, vec![], 0, 1);
    let outputs = vec![TransactionOutput::new(send, spk.clone()), TransactionOutput::new(amount - send - fee, spk.clone())];
    let tx = Transaction::new(0, vec![input], outputs, 0, SUBNETWORK_ID_NATIVE, 0, vec![]);
    let entry = UtxoEntry::new(amount, spk.clone(), daa, false, None);
    let mut mtx = MutableTransaction::with_entries(tx, vec![entry]);

    let reused = SigHashReusedValuesUnsync::new();
    let h = calc_schnorr_signature_hash(&mtx.as_verifiable(), 0, SIG_HASH_ALL, &reused);
    let msg = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
    let mut sig = kp.sign_schnorr(msg).as_ref().to_vec();
    sig.push(SIG_HASH_ALL.to_u8());
    mtx.tx.inputs[0].signature_script = ScriptBuilder::new().add_data(&sig).unwrap().drain();

    let t = &mtx.tx;
    let body = format!(
        r#"{{"transaction":{{"version":{},"inputs":[{{"previousOutpoint":{{"transactionId":"{}","index":{}}},"signatureScript":"{}","sequence":{},"sigOpCount":1}}],"outputs":[{}],"lockTime":0,"subnetworkId":"0000000000000000000000000000000000000000"}},"allowOrphan":false}}"#,
        t.version, txid, index, hex(&t.inputs[0].signature_script), t.inputs[0].sequence,
        t.outputs.iter().map(|o| format!(r#"{{"amount":{},"scriptPublicKey":{{"version":{},"scriptPublicKey":"{}"}}}}"#, o.value, o.script_public_key.version(), hex(o.script_public_key.script()))).collect::<Vec<_>>().join(",")
    );
    std::fs::write(format!("{dir}/send_body.json"), body).unwrap();
    println!("BODY_WRITTEN");
}
