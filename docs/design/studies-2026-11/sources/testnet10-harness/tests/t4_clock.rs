//! Scratch (testnet-10): test 1 CLOCK. CLTV + OpTxLockTime.
mod t4_common;
use t4_common::*;
use argent::builder::{EntryCall, TxContext};
use kaspa_consensus_core::{hashing::covenant_id::covenant_id, tx::{CovenantBinding, MutableTransaction}};
use kaspa_consensus_core::tx::Transaction;

fn app() -> String { format!("{}/clock/app.ag", env("T4SRC")) }
fn cstate(pk: &[u8], ms: i64, daa: i64, raw: i64) -> std::collections::BTreeMap<String, argent::builder::ArtifactValue> {
    st(vec![("owner", argent::builder::ArtifactValue::Bytes(pk.to_vec())), ("anchor_ms", int(ms)), ("anchor_daa", int(daa)), ("raw_seen", int(raw))])
}

#[test]
fn ck_genesis() {
    let h = setup(&app(), None);
    let (ft, fi, fa) = h.fund();
    let v = envu("V", 500_000_000); let fee = envu("FEE", 3_000_000);
    let s = cstate(&h.pk, envu("ANCHOR_MS", 0) as i64, envu("ANCHOR_DAA", 0) as i64, 0);
    let ctx = TxContext::new().input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0)
        .actor_genesis_output(0, "launch::ck", "Ck", s, v)
        .output(h.my_spk.clone(), None, fa - v - fee);
    let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let ids: Vec<_> = tx.outputs.iter().enumerate().filter(|(_, o)| o.covenant.is_some()).collect();
    let cid = covenant_id(op(&ft, fi), ids.iter().map(|(i, o)| (*i as u32, *o)));
    println!("COVENANT_ID {}", hex(cid.as_bytes().as_slice()));
    h.emit(&tx, "t4_ck_genesis", 1, fa - v - fee);
}

#[test]
fn ck_poke() {
    let h = setup(&app(), None);
    let (ft, fi, fa) = h.fund();
    let entry = env("ENTRY");
    let lock = envu("LOCK", 0);
    let seq = envu("SEQ", 0);
    let fee = envu("FEE", 3_000_000);
    let v = envu("V", 500_000_000);
    let (ms, daa, raw) = (envu("STATE_MS", 0) as i64, envu("STATE_DAA", 0) as i64, envu("STATE_RAW", 0) as i64);
    let cid = kaspa_consensus_core::Hash::from_bytes(unhex(&env("CV_ID")).try_into().unwrap());
    let cur = cstate(&h.pk, ms, daa, raw);
    let nxt = match entry.as_str() {
        "poke_time" => cstate(&h.pk, lock as i64, daa, raw),
        "poke_daa" => cstate(&h.pk, ms, lock as i64, raw),
        _ => cstate(&h.pk, ms, daa, lock as i64),
    };
    let utxo = h.builder.covenant_utxo("Ck", cur.clone(), v, 0, false, Some(cid)).unwrap();
    println!("COV_SPK {}", hex(utxo.script_public_key.script()));
    let patch = std::env::var("PATCH_SEQ_MAX").is_ok();
    let ctx = TxContext::new().lock_time(lock)
        .actor_input("Ck", cur.clone(), EntryCall::new(&entry), op(&env("CV_TXID"), envu("CV_INDEX", 0) as u32), utxo.clone(), seq)
        .input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), seq)
        .actor_output("Ck", nxt, CovenantBinding::new(0, cid), v)
        .output(h.my_spk.clone(), None, fa - fee);
    let mut tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    if patch {
        for i in tx.inputs.iter_mut() { i.sequence = u64::MAX; }
        let m = MutableTransaction::with_entries(tx.clone(), vec![utxo, h.fund_entry(fa)]);
        let sig = sign_idx(&m, 1, &h.kp);
        tx.inputs[1].signature_script = sig;
        println!("PATCHED all input sequences to MAX after build (engine bypass for node test)");
    }
    h.emit(&tx, "t4_ck_poke", 1, fa - fee);
}
#[allow(unused)] fn _u(_: Transaction) {}
