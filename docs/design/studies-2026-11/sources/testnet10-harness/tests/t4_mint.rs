//! Scratch (testnet-10): T4 test 4 PAIRED MINT. `mt_local`: in-memory build (fake ids). `mt_genesis`, `mt_open`: on-chain.
mod t4_common;
use t4_common::*;
use argent::builder::{args, state, EntryCall, TxContext, ArtifactValue};
use kaspa_consensus_core::{hashing::covenant_id::covenant_id, tx::CovenantBinding, Hash};
use std::collections::BTreeMap;

fn app() -> String { format!("{}/mint/app.ag", env("T4SRC")) }
fn kst(owner: Vec<u8>, amount: i64) -> BTreeMap<String, ArtifactValue> { state! { owner_identifier: owner, identifier_type: 0_u8, amount: amount } }
fn pst(c: Hash) -> BTreeMap<String, ArtifactValue> { state! { controller_id: c } }

fn open_ctx<'a>(h: &H, i_cid: Hash, e_cid: Hash, k_cid: Hash, iop: (String, u32), eop: (String, u32), kop: (String, u32), total: i64, vals: (u64, u64, u64, u64, u64), extra: Option<(&str, u32, u64)>, fee: u64, tweak_k: i64) -> TxContext<'a> {
    let (iv, pv, rv, vv, _) = vals;
    let k = total * 30 / 100 + tweak_k; let e = total - total * 30 / 100;
    let owner = vec![0x55u8; 32];
    let istate = state! { owner: h.pk.clone() };
    let iutxo = h.builder.covenant_utxo("Issuer", istate.clone(), iv, 0, false, Some(i_cid)).unwrap();
    let eutxo = h.builder.covenant_utxo("kcc20_asset::MinterProxy", pst(i_cid), pv, 0, false, Some(e_cid)).unwrap();
    let kutxo = h.builder.covenant_utxo("kcc20_asset::MinterProxy", pst(i_cid), pv, 0, false, Some(k_cid)).unwrap();
    let ve = state! { owner: h.pk.clone(), debt_enrk: e, debt_kfiat: total * 30 / 100 };
    let mut ctx = TxContext::new()
        .actor_input("Issuer", istate.clone(),
            EntryCall::new("open").args(args![total, owner.clone(), h.pk.clone(), e_cid, k_cid]),
            op(&iop.0, iop.1), iutxo, 0)
        .actor_input("kcc20_asset::MinterProxy", pst(i_cid), EntryCall::new("mint").args(args![pst(i_cid), kst(owner.clone(), e)]), op(&eop.0, eop.1), eutxo, 0)
        .actor_input("kcc20_asset::MinterProxy", pst(i_cid), EntryCall::new("mint").args(args![pst(i_cid), kst(owner.clone(), k)]), op(&kop.0, kop.1), kutxo, 0);
    if let Some((ft, fi, fa)) = extra { ctx = ctx.input(op(ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0); let _ = fee; }
    ctx = ctx
        .actor_output("Issuer", istate, CovenantBinding::new(0, i_cid), iv)
        .actor_output("Vault", ve, CovenantBinding::new(0, i_cid), vv)
        .actor_output("kcc20_asset::MinterProxy", pst(i_cid), CovenantBinding::new(1, e_cid), pv)
        .actor_output("kcc20_asset::KCC20", kst(owner.clone(), e), CovenantBinding::new(1, e_cid), rv)
        .actor_output("kcc20_asset::MinterProxy", pst(i_cid), CovenantBinding::new(2, k_cid), pv)
        .actor_output("kcc20_asset::KCC20", kst(owner, k), CovenantBinding::new(2, k_cid), rv);
    if let Some((_, _, fa)) = extra { ctx = ctx.output(h.my_spk.clone(), None, fa - vv - 2 * rv - fee); }
    ctx
}

#[test]
fn mt_local() {
    unsafe { std::env::set_var("T4_ALIAS", "kcc20_asset") }; let h = setup(&app(), Some(&format!("{}/mint/kcc20_asset.ag", env("T4SRC"))));
    let (i, e, k) = (Hash::from_bytes([0x31; 32]), Hash::from_bytes([0x32; 32]), Hash::from_bytes([0x33; 32]));
    let z = "00".repeat(32);
    for (name, total, tweak) in [("ratio30_ok", 1000, 0), ("ratio_wrong_kfiat_plus1", 1000, 1)] {
        let ctx = open_ctx(&h, i, e, k, (z.clone(), 0), (z.clone(), 1), (z.clone(), 2), total, (500_000_000, 500_000_000, 100_000_000, 500_000_000, 0), None, 0, tweak);
        match h.builder.build(&ctx) {
            Ok(tx) => {
                let m = kaspa_consensus_core::mass::MassCalculator::new_with_consensus_params(&kaspa_consensus_core::config::params::MAINNET_PARAMS).calc_non_contextual_masses(&tx);
                println!("LOCAL[{name}] BUILD_OK compute {} transient {} inputs {} outputs {}", m.compute_mass, m.transient_mass, tx.inputs.len(), tx.outputs.len());
            }
            Err(e) => println!("LOCAL[{name}] BUILD_FAILED {e}"),
        }
    }
}

fn ledger_path() -> String { format!("{}/mint/ledger.json", env("T4SRC")) }

#[test]
fn mt_genesis() {
    unsafe { std::env::set_var("T4_ALIAS", "kcc20_asset") };
    let h = setup(&app(), Some(&format!("{}/mint/kcc20_asset.ag", env("T4SRC"))));
    let (ft, fi, fa) = h.fund();
    let (iv, pv) = (envu("IV", 600_000_000), envu("PV", 600_000_000)); let fee = envu("FEE", 1_000_000);
    let istate = state! { owner: h.pk.clone() };
    // preliminary: issuer group alone gives its covenant id
    let pre = TxContext::new().input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0)
        .actor_genesis_output(0, "launch::issuer", "Issuer", istate.clone(), iv)
        .output(h.my_spk.clone(), None, fa - iv - fee);
    let pt = h.builder.build(&pre).unwrap();
    let i_cid = pt.outputs[0].covenant.unwrap().covenant_id;
    let ctx = TxContext::new().input(op(&ft, fi), h.fund_entry(fa), fund_cb(h.kp.clone()), 0)
        .actor_genesis_output(0, "launch::issuer", "Issuer", istate, iv)
        .actor_genesis_output(0, "launch::enrk", "kcc20_asset::MinterProxy", pst(i_cid), pv)
        .actor_genesis_output(0, "launch::kfiat", "kcc20_asset::MinterProxy", pst(i_cid), pv)
        .output(h.my_spk.clone(), None, fa - iv - 2 * pv - fee);
    let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let c = |i: usize| tx.outputs[i].covenant.unwrap().covenant_id;
    assert_eq!(c(0), i_cid, "issuer cid changed between preliminary and final build");
    println!("ISSUER_CID {} ENRK_CID {} KFIAT_CID {}", hex(c(0).as_bytes().as_slice()), hex(c(1).as_bytes().as_slice()), hex(c(2).as_bytes().as_slice()));
    std::fs::write(ledger_path(), serde_json::to_string_pretty(&serde_json::json!({"txid": tx.id().to_string(), "i": hex(c(0).as_bytes().as_slice()), "e": hex(c(1).as_bytes().as_slice()), "k": hex(c(2).as_bytes().as_slice()), "iv": iv, "pv": pv})).unwrap()).unwrap();
    h.emit_e(&tx, "t4_mt_genesis", 3, fa - iv - 2 * pv - fee, vec![h.fund_entry(fa)]);
}

#[test]
fn mt_open() {
    unsafe { std::env::set_var("T4_ALIAS", "kcc20_asset") };
    let h = setup(&app(), Some(&format!("{}/mint/kcc20_asset.ag", env("T4SRC"))));
    let (ft, fi, fa) = h.fund();
    let l: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(ledger_path()).unwrap()).unwrap();
    let h32 = |k: &str| Hash::from_bytes(unhex(l[k].as_str().unwrap()).try_into().unwrap());
    let t = l["txid"].as_str().unwrap().to_string();
    let (iv, pv) = (l["iv"].as_u64().unwrap(), l["pv"].as_u64().unwrap());
    let fee = envu("FEE", 3_000_000); let total = envu("TOTAL", 1000) as i64; let tweak = envu("TWEAK", 0) as i64;
    let ctx = open_ctx(&h, h32("i"), h32("e"), h32("k"), (t.clone(), 0), (t.clone(), 1), (t.clone(), 2), total, (iv, pv, 100_000_000, 300_000_000, 0), Some((&ft, fi, fa)), fee, tweak);
    let tx = match h.builder.build(&ctx) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let (iv, pv, rv, vv) = (iv, pv, 100_000_000u64, 300_000_000u64);
    let ents = vec![
        h.builder.covenant_utxo("Issuer", state! { owner: h.pk.clone() }, iv, 0, false, Some(h32("i"))).unwrap(),
        h.builder.covenant_utxo("kcc20_asset::MinterProxy", pst(h32("i")), pv, 0, false, Some(h32("e"))).unwrap(),
        h.builder.covenant_utxo("kcc20_asset::MinterProxy", pst(h32("i")), pv, 0, false, Some(h32("k"))).unwrap(),
        h.fund_entry(fa)];
    h.emit_e(&tx, "t4_mt_open", 6, fa - vv - 2 * rv - fee, ents);
}
