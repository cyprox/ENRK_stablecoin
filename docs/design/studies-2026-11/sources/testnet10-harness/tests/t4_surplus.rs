//! Scratch (testnet-10): T4 test 3 SURPLUS ROUTING. Ledger json at $T4SRC/surplus/ledger.json
mod t4_common;
use t4_common::*;
use argent::builder::{ArgValue, ArtifactValue, EntryCall, TxContext};
use kaspa_consensus_core::{hashing::covenant_id::covenant_id, tx::CovenantBinding};
use kaspa_consensus_core::Hash;
use serde_json::{json, Value};

fn dir() -> String { format!("{}/surplus", env("T4SRC")) }
fn setup_h() -> H { setup(&format!("{}/app.ag", dir()), Some(&format!("{}/oracle.ag", dir()))) }
fn ledger() -> Value { serde_json::from_str(&std::fs::read_to_string(format!("{}/ledger.json", dir())).unwrap()).unwrap() }
fn put_next(v: &Value) { std::fs::write(format!("{}/ledger_next.json", dir()), serde_json::to_string_pretty(v).unwrap()).unwrap(); }
fn ostate(pk: &[u8], round: i64, clock: i64) -> std::collections::BTreeMap<String, ArtifactValue> {
    st(vec![("publisher", ArtifactValue::Bytes(pk.to_vec())), ("round", int(round)), ("clock", int(clock))])
}
fn vstate(pk: &[u8], oid: &[u8], debt: i64) -> std::collections::BTreeMap<String, ArtifactValue> {
    st(vec![("owner", ArtifactValue::Bytes(pk.to_vec())), ("oracle_covid", ArtifactValue::Bytes(oid.to_vec())), ("debt", int(debt))])
}
fn sign_raw<T: AsRef<kaspa_consensus_core::tx::Transaction>>(tx: &kaspa_consensus_core::tx::MutableTransaction<T>, idx: usize, kp: &secp256k1::Keypair) -> Vec<u8> {
    use kaspa_consensus_core::hashing::{sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash}, sighash_type::SIG_HASH_ALL};
    let reused = SigHashReusedValuesUnsync::new();
    let hh = calc_schnorr_signature_hash(&tx.as_verifiable(), idx, SIG_HASH_ALL, &reused);
    let msg = secp256k1::Message::from_digest_slice(hh.as_bytes().as_slice()).unwrap();
    let mut sig = kp.sign_schnorr(msg).as_ref().to_vec();
    sig.push(SIG_HASH_ALL.to_u8());
    sig
}

#[test]
fn sp_vault_genesis() {
    let h = setup_h();
    let (ft, fi, fa) = h.fund();
    let m = envu("M", 1) as usize; let coll = envu("COLL", 1_200_000_000); let debt = envu("DEBT", 850_000_000) as i64; let fee = envu("FEE", 3_000_000);
    let mut l = ledger();
    let oid = unhex(l["oracle_cid"].as_str().unwrap());
    let s = vstate(&h.pk, &oid, debt);
    let mut ctx = TxContext::new().input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0);
    for _ in 0..m { ctx = ctx.actor_genesis_output(0, "launch::vault", "Vault", s.clone(), coll); }
    let change = fa - coll * m as u64 - fee;
    ctx = ctx.output(h.my_spk.clone(), None, change);
    let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let ids: Vec<_> = tx.outputs.iter().enumerate().filter(|(_, o)| o.covenant.is_some()).collect();
    let cid = covenant_id(op(&ft, fi), ids.iter().map(|(i, o)| (*i as u32, *o)));
    let mut vs: Vec<Value> = l["vaults"].as_array().cloned().unwrap_or_default();
    for i in 0..m { vs.push(json!({"txid": tx.id().to_string(), "idx": i, "value": coll, "debt": debt, "cid": hex(cid.as_bytes().as_slice()), "alive": true})); }
    l["vaults"] = json!(vs);
    put_next(&l);
    h.emit_e(&tx, "t4_sp_vgen", m as u32, change, vec![h.fund_entry(fa)]);
}

#[test]
fn sp_liquidate() {
    let h = setup_h();
    let (ft, fi, fa) = h.fund();
    let fee = envu("FEE", 5_000_000);
    let mut l = ledger();
    let vids: Vec<usize> = env("VIDS").split(',').map(|x| x.parse().unwrap()).collect();
    let o = l["oracle"].clone(); let oid = unhex(l["oracle_cid"].as_str().unwrap());
    let ocid = Hash::from_bytes(oid.clone().try_into().unwrap());
    let p = o["value"].as_u64().unwrap();
    let os = ostate(&h.pk, o["round"].as_i64().unwrap(), o["clock"].as_i64().unwrap());
    let mut ctx = TxContext::new(); let mut entries = vec![]; let mut outs = vec![]; let mut owed_tot = 0u64; let mut routed = 0u64;
    for (k, &vi) in vids.iter().enumerate() {
        let v = &l["vaults"][vi];
        let (val, debt) = (v["value"].as_u64().unwrap(), v["debt"].as_i64().unwrap());
        let cid = Hash::from_bytes(unhex(v["cid"].as_str().unwrap()).try_into().unwrap());
        let cur = vstate(&h.pk, &oid, debt);
        let utxo = h.builder.covenant_utxo("Vault", cur.clone(), val, 0, false, Some(cid)).unwrap();
        entries.push(utxo.clone());
        ctx = ctx.actor_input("Vault", cur, EntryCall::new("liquidate"), op(v["txid"].as_str().unwrap(), v["idx"].as_u64().unwrap() as u32), utxo, 0);
        let owed = (debt as u128 * 100_000_000 / p as u128) as u64; let surplus = val - owed;
        let s1 = surplus * 50 / 100; let s2 = surplus * 30 / 100; let s3 = surplus - s1 - s2;
        if vi == vids[0] { println!("SPLIT surplus {surplus} refund {s1} junior {s2} reserve {s3}"); }
        owed_tot += owed; routed += surplus;
        outs.push((k, cid, s1, s2, s3));
    }
    let n = vids.len();
    let ou = h.builder.covenant_utxo("oracle_feed::PriceRound", os.clone(), p, 0, false, Some(ocid)).unwrap();
    entries.push(ou.clone());
    ctx = ctx.actor_input("oracle_feed::PriceRound", os.clone(), EntryCall::new("use"), op(o["txid"].as_str().unwrap(), o["idx"].as_u64().unwrap() as u32), ou, 0);
    entries.push(h.fund_entry(fa));
    ctx = ctx.input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0);
    let pk = h.pk.clone();
    for &(k, cid, s1, s2, s3) in &outs {
        ctx = ctx.actor_output("Refund", st(vec![("owner", ArtifactValue::Bytes(pk.clone()))]), CovenantBinding::new(k as u16, cid), s1);
        ctx = ctx.actor_output("Pot", st(vec![("keeper", ArtifactValue::Bytes(pk.clone())), ("tag", int(1))]), CovenantBinding::new(k as u16, cid), s2);
        ctx = ctx.actor_output("Pot", st(vec![("keeper", ArtifactValue::Bytes(pk.clone())), ("tag", int(2))]), CovenantBinding::new(k as u16, cid), s3);
    }
    ctx = ctx.actor_output("oracle_feed::PriceRound", os.clone(), CovenantBinding::new(n as u16, ocid), p);
    let change = fa + owed_tot - fee;
    ctx = ctx.output(h.my_spk.clone(), None, change);
    let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let txid = tx.id().to_string();
    for (j, &vi) in vids.iter().enumerate() {
        l["vaults"][vi]["alive"] = json!(false);
        let mut pots = l["pots"].as_array().cloned().unwrap_or_default();
        for (t, kind) in ["refund", "junior", "reserve"].iter().enumerate() { let (_, c, a1, a2, a3) = outs[j]; let vv = [a1, a2, a3][t]; pots.push(json!({"txid": txid, "idx": 3*j+t, "kind": kind, "value": vv, "cid": hex(c.as_bytes().as_slice())})); }
        l["pots"] = json!(pots);
    }
    l["oracle"]["txid"] = json!(txid); l["oracle"]["idx"] = json!(3 * n);
    put_next(&l);
    println!("ROUTED_SURPLUS_TOTAL {routed}");
    h.emit_e(&tx, "t4_sp_liq", (3 * n + 1) as u32, change, entries);
}

#[test]
fn sp_reclaim() {
    let h = setup_h();
    let (ft, fi, fa) = h.fund();
    let fee = envu("FEE", 3_000_000);
    let mut l = ledger();
    let oid = unhex(l["oracle_cid"].as_str().unwrap());
    let vids: Vec<usize> = env("VIDS").split(',').map(|x| x.parse().unwrap()).collect();
    let mut ctx = TxContext::new(); let mut entries = vec![]; let mut tot = 0u64;
    for &vi in &vids {
        let v = &l["vaults"][vi];
        let (val, debt) = (v["value"].as_u64().unwrap(), v["debt"].as_i64().unwrap());
        let cid = Hash::from_bytes(unhex(v["cid"].as_str().unwrap()).try_into().unwrap());
        let cur = vstate(&h.pk, &oid, debt);
        let utxo = h.builder.covenant_utxo("Vault", cur.clone(), val, 0, false, Some(cid)).unwrap();
        entries.push(utxo.clone()); tot += val;
        let kp = h.kp.clone();
        ctx = ctx.actor_input("Vault", cur, EntryCall::new("reclaim").args_with(move |tx, i| argent::builder::args![sign_raw(tx, i, &kp)]), op(v["txid"].as_str().unwrap(), v["idx"].as_u64().unwrap() as u32), utxo, 0);
    }
    entries.push(h.fund_entry(fa));
    ctx = ctx.input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0);
    ctx = ctx.output(h.my_spk.clone(), None, fa + tot - fee);
    let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    for &vi in &vids { l["vaults"][vi]["alive"] = json!(false); }
    put_next(&l);
    h.emit_e(&tx, "t4_sp_reclaim", 0, fa + tot - fee, entries);
}

/// recover pots/refunds listed in ledger "pots" (indices PIDS) via their spend entries
#[test]
fn sp_take() {
    let h = setup_h();
    let (ft, fi, fa) = h.fund();
    let fee = envu("FEE", 3_000_000);
    let l = ledger();
    let pids: Vec<usize> = env("PIDS").split(',').map(|x| x.parse().unwrap()).collect();
    let vcid = Hash::from_bytes(unhex(l["vaults"][0]["cid"].as_str().unwrap()).try_into().unwrap());
    let mut ctx = TxContext::new(); let mut entries = vec![]; let mut tot = 0u64;
    let pk = h.pk.clone();
    for &pi in &pids {
        let pt = &l["pots"][pi];
        let kind = pt["kind"].as_str().unwrap();
        let val = pt["value"].as_u64().unwrap();
        let (actor, state, entry) = match kind {
            "refund" => ("Refund", st(vec![("owner", ArtifactValue::Bytes(pk.clone()))]), "claim"),
            "junior" => ("Pot", st(vec![("keeper", ArtifactValue::Bytes(pk.clone())), ("tag", int(1))]), "take"),
            _ => ("Pot", st(vec![("keeper", ArtifactValue::Bytes(pk.clone())), ("tag", int(2))]), "take"),
        };
        let cid = Hash::from_bytes(unhex(pt["cid"].as_str().unwrap()).try_into().unwrap());
        let utxo = h.builder.covenant_utxo(actor, state.clone(), val, 0, false, Some(cid)).unwrap();
        entries.push(utxo.clone()); tot += val;
        let kp = h.kp.clone();
        ctx = ctx.actor_input(actor, state, EntryCall::new(entry).args_with(move |tx, i| argent::builder::args![sign_raw(tx, i, &kp)]), op(pt["txid"].as_str().unwrap(), pt["idx"].as_u64().unwrap() as u32), utxo, 0);
    }
    let _ = vcid; let _ = ArgValue::Value(ArtifactValue::Int(0));
    entries.push(h.fund_entry(fa));
    ctx = ctx.input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0);
    ctx = ctx.output(h.my_spk.clone(), None, fa + tot - fee);
    let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    h.emit_e(&tx, "t4_sp_take", 0, fa + tot - fee, entries);
}
