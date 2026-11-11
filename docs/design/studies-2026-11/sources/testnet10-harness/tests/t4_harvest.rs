//! Scratch (testnet-10): T4 test 2 HARVEST (and reclaim). Ledger json at $T4SRC/harvest/ledger.json
mod t4_common;
use t4_common::*;
use argent::builder::{ArtifactValue, EntryCall, TxContext};
use kaspa_consensus_core::{hashing::covenant_id::covenant_id, tx::CovenantBinding};
use kaspa_consensus_core::Hash;
use serde_json::{json, Value};

fn dir() -> String { format!("{}/harvest", env("T4SRC")) }
fn setup_h() -> H { setup(&format!("{}/app.ag", dir()), Some(&format!("{}/oracle.ag", dir()))) }
fn ledger() -> Value { serde_json::from_str(&std::fs::read_to_string(format!("{}/ledger.json", dir())).unwrap()).unwrap() }
fn put_next(v: &Value) { std::fs::write(format!("{}/ledger_next.json", dir()), serde_json::to_string_pretty(v).unwrap()).unwrap(); }
fn ostate(pk: &[u8], round: i64, clock: i64) -> std::collections::BTreeMap<String, ArtifactValue> {
    st(vec![("publisher", ArtifactValue::Bytes(pk.to_vec())), ("round", int(round)), ("clock", int(clock))])
}
fn vstate(pk: &[u8], oid: &[u8], debt: i64, anchor: i64) -> std::collections::BTreeMap<String, ArtifactValue> {
    st(vec![("owner", ArtifactValue::Bytes(pk.to_vec())), ("oracle_covid", ArtifactValue::Bytes(oid.to_vec())), ("debt", int(debt)), ("anchor", int(anchor))])
}
fn kstate(pk: &[u8]) -> std::collections::BTreeMap<String, ArtifactValue> { st(vec![("keeper", ArtifactValue::Bytes(pk.to_vec()))]) }

#[test]
fn hv_oracle_genesis() {
    let h = setup_h();
    let (ft, fi, fa) = h.fund();
    let price = envu("PRICE", 100_000_000); let fee = envu("FEE", 500_000); let clock = envu("CLOCK0", 0) as i64;
    let ctx = TxContext::new().input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0)
        .actor_genesis_output(0, "launch::oracle", "oracle_feed::PriceRound", ostate(&h.pk, 1, clock), price)
        .output(h.my_spk.clone(), None, fa - price - fee);
    let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let ids: Vec<_> = tx.outputs.iter().enumerate().filter(|(_, o)| o.covenant.is_some()).collect();
    let cid = covenant_id(op(&ft, fi), ids.iter().map(|(i, o)| (*i as u32, *o)));
    let mut l = ledger();
    l["oracle_cid"] = json!(hex(cid.as_bytes().as_slice()));
    l["oracle"] = json!({"txid": tx.id().to_string(), "idx": 0, "value": price, "round": 1, "clock": clock});
    put_next(&l);
    h.emit_e(&tx, "t4_hv_oracle", 1, fa - price - fee, vec![h.fund_entry(fa)]);
}

#[test]
fn hv_vault_genesis() {
    let h = setup_h();
    let (ft, fi, fa) = h.fund();
    let m = envu("M", 1) as usize; let coll = envu("COLL", 1_200_000_000); let debt = envu("DEBT", 400_000_000) as i64; let fee = envu("FEE", 3_000_000);
    let anchor = envu("ANCHOR", 0) as i64;
    let mut l = ledger();
    let oid = unhex(l["oracle_cid"].as_str().unwrap());
    let s = vstate(&h.pk, &oid, debt, anchor);
    let mut ctx = TxContext::new().input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0);
    for _ in 0..m { ctx = ctx.actor_genesis_output(0, "launch::vault", "Vault", s.clone(), coll); }
    let change = fa - coll * m as u64 - fee;
    ctx = ctx.output(h.my_spk.clone(), None, change);
    let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let ids: Vec<_> = tx.outputs.iter().enumerate().filter(|(_, o)| o.covenant.is_some()).collect();
    let cid = covenant_id(op(&ft, fi), ids.iter().map(|(i, o)| (*i as u32, *o)));
    l["vault_cid"] = json!(hex(cid.as_bytes().as_slice()));
    let mut vs: Vec<Value> = l["vaults"].as_array().cloned().unwrap_or_default();
    // new vault cid differs from older groups: store per-vault cid
    for i in 0..m { vs.push(json!({"txid": tx.id().to_string(), "idx": i, "value": coll, "anchor": anchor, "debt": debt, "cid": hex(cid.as_bytes().as_slice()), "alive": true})); }
    l["vaults"] = json!(vs);
    put_next(&l);
    h.emit_e(&tx, "t4_hv_vgen", m as u32, change, vec![h.fund_entry(fa)]);
}

#[test]
fn hv_harvest() {
    let h = setup_h();
    let (ft, fi, fa) = h.fund();
    let lock = envu("LOCK", 0); let fee = envu("FEE", 5_000_000);
    let mut l = ledger();
    let vids: Vec<usize> = env("VIDS").split(',').map(|x| x.parse().unwrap()).collect();
    let o = l["oracle"].clone(); let oid = unhex(l["oracle_cid"].as_str().unwrap());
    let ocid = Hash::from_bytes(oid.clone().try_into().unwrap());
    let p = o["value"].as_u64().unwrap();
    let os = ostate(&h.pk, o["round"].as_i64().unwrap(), o["clock"].as_i64().unwrap());
    let mut ctx = TxContext::new().lock_time(lock);
    let mut entries = vec![];
    let (mut tot_fee, mut outs) = (0u64, vec![]);
    for (k, &vi) in vids.iter().enumerate() {
        let v = &l["vaults"][vi];
        let (val, anchor, debt) = (v["value"].as_u64().unwrap(), v["anchor"].as_i64().unwrap(), v["debt"].as_i64().unwrap());
        let cid = Hash::from_bytes(unhex(v["cid"].as_str().unwrap()).try_into().unwrap());
        let cur = vstate(&h.pk, &oid, debt, anchor);
        let utxo = h.builder.covenant_utxo("Vault", cur.clone(), val, 0, false, Some(cid)).unwrap();
        entries.push(utxo.clone());
        ctx = ctx.actor_input("Vault", cur, EntryCall::new("harvest").args(vec![argent::builder::ArgValue::Value(ArtifactValue::Bytes(h.pk.clone()))]), op(v["txid"].as_str().unwrap(), v["idx"].as_u64().unwrap() as u32), utxo, 0);
        let dt_s = ((lock as i128) - (anchor as i128)) / 1000;
        let fee_units = (debt as i128) * dt_s * 24000 / 1 / 31_536_000;
        let fee_kas = (fee_units * 100_000_000 / (p as i128)) as u64;
        let bounty = fee_kas * 40 / 100; let note = fee_kas - bounty; let next = val - fee_kas;
        println!("VAULT {vi} dt_s {dt_s} fee_kas {fee_kas} tip {bounty} note {note} next {next}");
        tot_fee += fee_kas;
        outs.push((vi, k, cid, debt, next, note, bounty));
    }
    let n = vids.len();
    let ou = h.builder.covenant_utxo("oracle_feed::PriceRound", os.clone(), p, 0, false, Some(ocid)).unwrap();
    entries.push(ou.clone());
    ctx = ctx.actor_input("oracle_feed::PriceRound", os.clone(), EntryCall::new("use"), op(o["txid"].as_str().unwrap(), o["idx"].as_u64().unwrap() as u32), ou, 0);
    entries.push(h.fund_entry(fa));
    ctx = ctx.input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0);
    for &(_vi, k, cid, debt, next, note, bounty) in &outs {
        ctx = ctx.actor_output("Vault", vstate(&h.pk, &oid, debt, lock as i64), CovenantBinding::new(k as u16, cid), next);
        ctx = ctx.actor_output("FeeNote", kstate(&h.pk), CovenantBinding::new(k as u16, cid), note);
        ctx = ctx.actor_output("Tip", st(vec![("keeper", ArtifactValue::Bytes(h.pk.clone())), ("tag", int(7))]), CovenantBinding::new(k as u16, cid), bounty);
    }
    ctx = ctx.actor_output("oracle_feed::PriceRound", os.clone(), CovenantBinding::new(n as u16, ocid), p);
    let change = fa - fee;
    ctx = ctx.output(h.my_spk.clone(), None, change);
    let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let txid = tx.id().to_string();
    for (j, &(vi, _k, _c, debt, next, note, bounty)) in outs.iter().enumerate() {
        let _ = (debt, note, bounty);
        l["vaults"][vi]["txid"] = json!(txid); l["vaults"][vi]["idx"] = json!(3 * j);
        l["vaults"][vi]["value"] = json!(next); l["vaults"][vi]["anchor"] = json!(lock);
        let mut notes = l["notes"].as_array().cloned().unwrap_or_default();
        notes.push(json!({"txid": txid, "idx": 3*j+1, "value": note, "kind": "note"})); notes.push(json!({"txid": txid, "idx": 3*j+2, "value": bounty, "kind": "tip"}));
        l["notes"] = json!(notes);
    }
    l["oracle"]["txid"] = json!(txid); l["oracle"]["idx"] = json!(3 * n);
    put_next(&l);
    println!("TOTAL_FEE_KAS_SOMPI {tot_fee}");
    h.emit_e(&tx, "t4_hv_harvest", (3 * n + 1) as u32, change, entries);
}

#[test]
fn hv_oracle_use() {
    let h = setup_h();
    let (ft, fi, fa) = h.fund();
    let fee = envu("FEE", 3_000_000);
    let l = ledger(); let o = l["oracle"].clone();
    let ocid = Hash::from_bytes(unhex(l["oracle_cid"].as_str().unwrap()).try_into().unwrap());
    let p = o["value"].as_u64().unwrap();
    let os = ostate(&h.pk, o["round"].as_i64().unwrap(), o["clock"].as_i64().unwrap());
    let ou = h.builder.covenant_utxo("oracle_feed::PriceRound", os.clone(), p, 0, false, Some(ocid)).unwrap();
    let ctx = TxContext::new()
        .actor_input("oracle_feed::PriceRound", os.clone(), EntryCall::new("use"), op(o["txid"].as_str().unwrap(), o["idx"].as_u64().unwrap() as u32), ou.clone(), 0)
        .input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0)
        .actor_output("oracle_feed::PriceRound", os.clone(), CovenantBinding::new(0, ocid), p)
        .output(h.my_spk.clone(), None, fa - fee);
    let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let mut l2 = l.clone(); l2["oracle"]["txid"] = json!(tx.id().to_string()); l2["oracle"]["idx"] = json!(0); put_next(&l2);
    h.emit_e(&tx, "t4_hv_ouse", 1, fa - fee, vec![ou, h.fund_entry(fa)]);
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

/// reclaim vaults (owner sig) to the wallet; VIDS list of ledger vault indices
#[test]
fn hv_reclaim() {
    let h = setup_h();
    let (ft, fi, fa) = h.fund();
    let fee = envu("FEE", 3_000_000);
    let mut l = ledger();
    let oid = unhex(l["oracle_cid"].as_str().unwrap());
    let vids: Vec<usize> = env("VIDS").split(',').map(|x| x.parse().unwrap()).collect();
    let mut ctx = TxContext::new(); let mut entries = vec![]; let mut tot = 0u64;
    for &vi in &vids {
        let v = &l["vaults"][vi];
        let (val, anchor, debt) = (v["value"].as_u64().unwrap(), v["anchor"].as_i64().unwrap(), v["debt"].as_i64().unwrap());
        let cid = Hash::from_bytes(unhex(v["cid"].as_str().unwrap()).try_into().unwrap());
        let cur = vstate(&h.pk, &oid, debt, anchor);
        let utxo = h.builder.covenant_utxo("Vault", cur.clone(), val, 0, false, Some(cid)).unwrap();
        entries.push(utxo.clone()); tot += val; println!("SPK {}", hex(utxo.script_public_key.script()));
        let kp = h.kp.clone();
        ctx = ctx.actor_input("Vault", cur, EntryCall::new("reclaim").args_with(move |tx, i| argent::builder::args![sign_raw(tx, i, &kp)]), op(v["txid"].as_str().unwrap(), v["idx"].as_u64().unwrap() as u32), utxo, 0);
    }
    entries.push(h.fund_entry(fa));
    ctx = ctx.input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0);
    ctx = ctx.output(h.my_spk.clone(), None, fa + tot - fee);
    let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    for &vi in &vids { l["vaults"][vi]["alive"] = json!(false); }
    put_next(&l);
    h.emit_e(&tx, "t4_hv_reclaim", 0, fa + tot - fee, entries);
}

/// T5: build K chained `use` spends of the shared price UTXO (and chained fund), write t5_<k>.json. Uses the surplus ledger oracle.
#[test]
fn hot_chain_build() {
    let h = setup(&format!("{}/harvest/app.ag", env("T4SRC")), Some(&format!("{}/harvest/oracle.ag", env("T4SRC"))));
    let (mut ft, mut fi, mut fa) = h.fund();
    let kn = envu("K", 20) as usize; let fee = envu("FEE", 600_000);
    let l: Value = serde_json::from_str(&std::fs::read_to_string(format!("{}/surplus/ledger.json", env("T4SRC"))).unwrap()).unwrap();
    let o = l["oracle"].clone();
    let ocid = Hash::from_bytes(unhex(l["oracle_cid"].as_str().unwrap()).try_into().unwrap());
    let p = o["value"].as_u64().unwrap();
    let os = ostate(&h.pk, o["round"].as_i64().unwrap(), o["clock"].as_i64().unwrap());
    let (mut ot, mut oi) = (o["txid"].as_str().unwrap().to_string(), o["idx"].as_u64().unwrap() as u32);
    let mut ids = vec![];
    for k in 0..kn {
        let ou = h.builder.covenant_utxo("oracle_feed::PriceRound", os.clone(), p, 0, false, Some(ocid)).unwrap();
        let ctx = TxContext::new()
            .actor_input("oracle_feed::PriceRound", os.clone(), EntryCall::new("use"), op(&ot, oi), ou, 0)
            .input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0)
            .actor_output("oracle_feed::PriceRound", os.clone(), CovenantBinding::new(0, ocid), p)
            .output(h.my_spk.clone(), None, fa - fee);
        let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED k={k} {e}"); return; } };
        let id = tx.id().to_string();
        std::fs::write(format!("{}/t5_{:03}.json", env("TN10_DIR"), k), serde_json::to_string(&tx).unwrap()).unwrap();
        ids.push(id.clone());
        ot = id.clone(); oi = 0; ft = id; fi = 1; fa -= fee;
    }
    std::fs::write(format!("{}/t5_ids.txt", env("TN10_DIR")), ids.join("\n")).unwrap();
    std::fs::write(format!("{}/t5_next_fund.txt", env("TN10_DIR")), format!("{ft} {fi} {fa}")).unwrap();
    // oracle ledger after chain
    let mut l2 = l.clone(); l2["oracle"]["txid"] = json!(ot); l2["oracle"]["idx"] = json!(0);
    std::fs::write(format!("{}/surplus/ledger_hot.json", env("T4SRC")), serde_json::to_string_pretty(&l2).unwrap()).unwrap();
    println!("CHAIN_BUILT K={kn} last={ot}");
}

/// T5: two competing `use` spends of the same price outpoint (A with FUND, B with FUND2), written t5c_a.json / t5c_b.json
#[test]
fn hot_conflict_build() {
    let h = setup(&format!("{}/harvest/app.ag", env("T4SRC")), Some(&format!("{}/harvest/oracle.ag", env("T4SRC"))));
    let (ft, fi, fa) = h.fund();
    let f2: Vec<String> = env("FUND2").split_whitespace().map(|s| s.to_string()).collect();
    let (ft2, fi2, fa2): (String, u32, u64) = (f2[0].clone(), f2[1].parse().unwrap(), f2[2].parse().unwrap());
    let fee = envu("FEE", 600_000);
    let l = ledger_sp();
    let o = l["oracle"].clone();
    let ocid = Hash::from_bytes(unhex(l["oracle_cid"].as_str().unwrap()).try_into().unwrap());
    let p = o["value"].as_u64().unwrap();
    let os = ostate(&h.pk, o["round"].as_i64().unwrap(), o["clock"].as_i64().unwrap());
    for (name, (t, i, a), f) in [("a", (ft, fi, fa), fee), ("b", (ft2, fi2, fa2), fee + 100_000)] {
        let ou = h.builder.covenant_utxo("oracle_feed::PriceRound", os.clone(), p, 0, false, Some(ocid)).unwrap();
        let ctx = TxContext::new()
            .actor_input("oracle_feed::PriceRound", os.clone(), EntryCall::new("use"), op(o["txid"].as_str().unwrap(), o["idx"].as_u64().unwrap() as u32), ou, 0)
            .input(op(&t, i), h.fund_entry(a), fund_cb(h.kp.clone()), 0)
            .actor_output("oracle_feed::PriceRound", os.clone(), CovenantBinding::new(0, ocid), p)
            .output(h.my_spk.clone(), None, a - f);
        let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {name} {e}"); return; } };
        std::fs::write(format!("{}/t5c_{name}.json", env("TN10_DIR")), serde_json::to_string(&tx).unwrap()).unwrap();
        println!("TX_{name} {}", tx.id());
    }
}
fn ledger_sp() -> Value { serde_json::from_str(&std::fs::read_to_string(format!("{}/surplus/ledger.json", env("T4SRC"))).unwrap()).unwrap() }
