//! x1b scratch (testnet-10 only, SP copy of argent): N-to-N price-population refresh, local cases and tx builders.
//! Env: X1B_DIR (oracle.ag + vault.ag), VARIANT=a|b, TN10_DIR (key + address), STEP (see tests below).
use argent::builder::{args, ArtifactBundle, ArtifactValue, EntryCall, InputSigScript, TxBuilder, TxContext};
use kaspa_addresses::Address;
use kaspa_consensus_core::{
    config::params::MAINNET_PARAMS,
    hashing::{covenant_id::covenant_id, sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash}, sighash_type::SIG_HASH_ALL},
    mass::MassCalculator,
    tx::{CovenantBinding, MutableTransaction, PopulatedTransaction, ScriptPublicKey, Transaction, TransactionId, TransactionOutpoint, UtxoEntry},
    Hash,
};
use kaspa_txscript::{pay_to_address_script, script_builder::ScriptBuilder};
use secp256k1::{Keypair, Secp256k1, SecretKey};
use std::collections::BTreeMap;

fn unhex(s: &str) -> Vec<u8> { (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect() }
fn hex(b: &[u8]) -> String { b.iter().map(|x| format!("{x:02x}")).collect() }
fn env(k: &str) -> String { std::env::var(k).unwrap_or_else(|_| panic!("missing env {k}")) }
fn envo(k: &str) -> Option<String> { std::env::var(k).ok() }
fn op(txid: &str, i: u32) -> TransactionOutpoint { TransactionOutpoint::new(TransactionId::from_bytes(unhex(txid).try_into().unwrap()), i) }
fn sign<T: AsRef<Transaction>>(tx: &MutableTransaction<T>, idx: usize, kp: &Keypair) -> Vec<u8> {
    let reused = SigHashReusedValuesUnsync::new();
    let h = calc_schnorr_signature_hash(&tx.as_verifiable(), idx, SIG_HASH_ALL, &reused);
    let msg = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
    let mut sig = kp.sign_schnorr(msg).as_ref().to_vec();
    sig.push(SIG_HASH_ALL.to_u8());
    sig
}
fn fund_cb(kp: Keypair) -> InputSigScript<'static> {
    InputSigScript::with_transaction(move |tx, idx| ScriptBuilder::new().add_data(&sign(tx, idx, &kp)).unwrap().drain())
}

#[derive(Clone, Debug)]
struct Pop { txid: String, index: u32, value: u64, round: i64, price: i64, slot: i64, n: i64 }
fn read_pop(path: &str) -> Vec<Pop> {
    let v: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap();
    v.as_array().unwrap().iter().map(|e| Pop {
        txid: e["txid"].as_str().unwrap().into(), index: e["index"].as_u64().unwrap() as u32, value: e["value"].as_u64().unwrap(),
        round: e["round"].as_i64().unwrap(), price: e["price"].as_i64().unwrap(), slot: e["slot"].as_i64().unwrap(), n: e["n"].as_i64().unwrap(),
    }).collect()
}
fn write_pop(path: &str, p: &[Pop]) {
    let v: Vec<_> = p.iter().map(|e| serde_json::json!({"txid": e.txid, "index": e.index, "value": e.value, "round": e.round, "price": e.price, "slot": e.slot, "n": e.n})).collect();
    std::fs::write(path, serde_json::to_string(&v).unwrap()).unwrap();
}
#[derive(Clone, Debug)]
struct Fund { txid: String, index: u32, amount: u64 }
fn read_fund() -> Fund {
    let s = env("FUND");
    let p: Vec<&str> = s.split_whitespace().collect();
    Fund { txid: p[0].into(), index: p[1].parse().unwrap(), amount: p[2].parse().unwrap() }
}

struct Cx { kp: Keypair, pk: Vec<u8>, my_spk: ScriptPublicKey, builder: TxBuilder<'static>, oid: Hash, variant: String, dir: String }
impl Cx {
    fn new() -> Cx {
        let dir = env("TN10_DIR");
        let sk = SecretKey::from_slice(&unhex(std::fs::read_to_string(format!("{dir}/tn10_key.hex")).unwrap().trim())).unwrap();
        Cx::with_key(Keypair::from_secret_key(&Secp256k1::new(), &sk), dir)
    }
    fn with_key(kp: Keypair, dir: String) -> Cx {
        let pk = kp.x_only_public_key().0.serialize().to_vec();
        let addr = Address::try_from(std::fs::read_to_string(format!("{dir}/tn10_address.txt")).unwrap().trim()).unwrap();
        let my_spk = pay_to_address_script(&addr);
        let cdir = env("X1B_DIR");
        let out = std::env::temp_dir().join(format!("x1b_{}", std::process::id()));
        let v = Box::leak(Box::new(argent::build_file(format!("{cdir}/vault.ag"), &out.join("v")).unwrap()));
        let o = Box::leak(Box::new(argent::build_file(format!("{cdir}/oracle.ag"), &out.join("o")).unwrap()));
        let bundle = ArtifactBundle::new(&*v).unwrap().with_app("oracle_feed", &*o).unwrap();
        let builder = TxBuilder::from_bundle(&bundle).unwrap();
        let oid = envo("ORACLE_ID").map(|s| Hash::from_bytes(unhex(&s).try_into().unwrap())).unwrap_or(Hash::from_bytes([0x42; 32]));
        Cx { kp, pk, my_spk, builder, oid, variant: envo("VARIANT").unwrap_or("a".into()), dir }
    }
    fn lead_actor(&self) -> &'static str { if self.variant == "b" { "oracle_feed::Leader" } else { "oracle_feed::PriceRound" } }
    fn foll_actor(&self) -> &'static str { if self.variant == "b" { "oracle_feed::Follower" } else { "oracle_feed::PriceRound" } }
    fn actor_of(&self, slot: i64) -> &'static str { if slot == 0 { self.lead_actor() } else { self.foll_actor() } }
    fn ostate(&self, p: &Pop) -> BTreeMap<String, ArtifactValue> { self.ostate_raw(p.round, p.price, p.slot, p.n) }
    fn ostate_raw(&self, round: i64, price: i64, slot: i64, n: i64) -> BTreeMap<String, ArtifactValue> {
        let mut s = BTreeMap::new();
        s.insert("publisher".to_string(), ArtifactValue::Bytes(self.pk.clone()));
        s.insert("round".to_string(), ArtifactValue::Int(round));
        s.insert("price".to_string(), ArtifactValue::Int(price));
        s.insert("slot".to_string(), ArtifactValue::Int(slot));
        s.insert("n".to_string(), ArtifactValue::Int(n));
        s
    }
    fn vstate(&self, debt: i64) -> BTreeMap<String, ArtifactValue> {
        let mut s = BTreeMap::new();
        s.insert("owner".to_string(), ArtifactValue::Bytes(self.pk.clone()));
        s.insert("oracle_covid".to_string(), ArtifactValue::Bytes(self.oid.as_bytes().to_vec()));
        s.insert("debt".to_string(), ArtifactValue::Int(debt));
        s
    }
    fn utxo_of(&self, p: &Pop) -> UtxoEntry {
        self.builder.covenant_utxo(self.actor_of(p.slot), self.ostate(p), p.value, 0, false, Some(self.oid)).unwrap()
    }
}

#[derive(Clone, Debug)]
struct Out { slot: i64, round: i64, price: i64, n: i64, value: u64 }
fn default_outs(pop: &[Pop], new_price: i64) -> Vec<Out> {
    pop.iter().map(|p| Out { slot: p.slot, round: p.round + 1, price: new_price, n: p.n, value: p.value }).collect()
}

fn masses(tx: &Transaction, entries: Vec<UtxoEntry>) -> (u64, u64, u64) {
    let m = MassCalculator::new_with_consensus_params(&MAINNET_PARAMS);
    let nc = m.calc_non_contextual_masses(tx);
    let st = m.calc_contextual_masses(&PopulatedTransaction::new(tx, entries)).map(|x| x.storage_mass).unwrap_or(u64::MAX);
    (nc.compute_mass, nc.transient_mass, st)
}
fn floor_fee(m: (u64, u64, u64)) -> u64 { if envo("FEE_STORAGE").is_some() { 100 * m.0.max((m.1 + 1) / 2).max(m.2) } else { 100 * m.0.max((m.1 + 1) / 2) } }

/// Refresh context. Leader (slot 0 of pop) first, followers after, then the fee input; outputs `outs` bound to input 0, then change.
fn refresh_ctx(c: &Cx, pop: &[Pop], outs: &[Out], new_price: i64, signer: &Keypair, fund: &Fund, fee: u64, drain_to: Option<u64>) -> (TxContext<'static>, Vec<UtxoEntry>) {
    let mut ctx = TxContext::new();
    let mut entries = vec![];
    for (i, p) in pop.iter().enumerate() {
        let st = c.ostate(p);
        let u = c.utxo_of(p);
        entries.push(u.clone());
        let call = if i == 0 {
            let kp = signer.clone();
            if drain_to.is_some() { EntryCall::new(Box::leak(envo("DRAIN_ENTRY").unwrap_or("drain".into()).into_boxed_str()) as &str).args_with(move |tx, ix| args![sign(tx, ix, &kp)]) }
            else { EntryCall::new(Box::leak(envo("REFRESH_ENTRY").unwrap_or("refresh".into()).into_boxed_str()) as &str).args_with(move |tx, ix| args![sign(tx, ix, &kp), new_price]) }
        } else { EntryCall::new("follow") };
        ctx = ctx.actor_input(c.actor_of(p.slot), st, call, op(&p.txid, p.index), u, 0);
    }
    let funding = UtxoEntry::new(fund.amount, c.my_spk.clone(), 0, false, None);
    entries.push(funding.clone());
    ctx = ctx.input(op(&fund.txid, fund.index), funding, fund_cb(c.kp.clone()), 0);
    if let Some(total) = drain_to {
        ctx = ctx.output(c.my_spk.clone(), None, total + fund.amount - fee);
    } else {
        for o in outs {
            ctx = ctx.actor_output(c.actor_of(o.slot), c.ostate_raw(o.round, o.price, o.slot, o.n), CovenantBinding::new(0, c.oid), o.value);
        }
        ctx = ctx.output(c.my_spk.clone(), None, fund.amount - fee);
    }
    (ctx, entries)
}
fn build_refresh(c: &Cx, pop: &[Pop], outs: &[Out], new_price: i64, signer: &Keypair, fund: &Fund, drain: bool) -> Result<(Transaction, (u64, u64, u64), u64), String> {
    let dt = if drain { Some(pop.iter().map(|p| p.value).sum::<u64>()) } else { None };
    let guess = 3_000_000u64;
    let (ctx, entries) = refresh_ctx(c, pop, outs, new_price, signer, fund, guess, dt);
    let tx = c.builder.build(&ctx).map_err(|e| format!("{e}").replace('\n', " "))?;
    let m = masses(&tx, entries.clone());
    let fee = floor_fee(m) + 200;
    let (ctx2, entries2) = refresh_ctx(c, pop, outs, new_price, signer, fund, fee, dt);
    let tx2 = c.builder.build(&ctx2).map_err(|e| format!("{e}").replace('\n', " "))?;
    let m2 = masses(&tx2, entries2);
    Ok((tx2, m2, fee))
}

fn mk_pop(c: &Cx, n: usize, v: u64, price: i64, round: i64) -> Vec<Pop> {
    (0..n).map(|i| Pop { txid: format!("{:02x}", 0x10 + i).repeat(32), index: 0, value: v, round, price, slot: i as i64, n: n as i64 }).collect::<Vec<_>>().into_iter().map(|p| { let _ = c; p }).collect()
}
fn short(s: &str) -> String { s[..s.len().min(150)].to_string() }

#[test]
fn local_cases() {
    let kp = Keypair::from_secret_key(&Secp256k1::new(), &SecretKey::from_slice(&[9u8; 32]).unwrap());
    let c = Cx::with_key(kp.clone(), env("TN10_DIR"));
    // in the local run the publisher key is the throwaway key [9;32]; publisher state uses it
    let xo = kp.x_only_public_key().0.serialize();
    let c = Cx { pk: xo.to_vec(), my_spk: pay_to_address_script(&Address::new(kaspa_addresses::Prefix::Testnet, kaspa_addresses::Version::PubKey, &xo)), ..c };
    let n: usize = envo("LN").map(|s| s.parse().unwrap()).unwrap_or(4);
    let v: u64 = 10_000_000 * n as u64;
    let p0 = 100_000_000i64;
    let pop = mk_pop(&c, n, v, p0, 1);
    let fund = Fund { txid: "ee".repeat(32), index: 0, amount: envo("FUNDAMT").map(|s| s.parse().unwrap()).unwrap_or(v + 1_000_000_000 / 10) };
    let other = Keypair::from_secret_key(&Secp256k1::new(), &SecretKey::from_slice(&[7u8; 32]).unwrap());
    let np = 105_000_000i64;
    let run = |label: &str, pop: &[Pop], outs: &[Out], price: i64, signer: &Keypair| {
        match build_refresh(&c, pop, outs, price, signer, &fund, false) {
            Ok((_, m, fee)) => println!("RESULT[{label}] ACCEPT compute {} transient {} storage {} fee {}", m.0, m.1, m.2, fee),
            Err(e) => println!("RESULT[{label}] REJECT {}", short(&e)),
        }
    };
    println!("VARIANT {} N {} value_each {}", c.variant, n, v);
    run("positive +5%", &pop, &default_outs(&pop, np), np, &kp);
    if envo("POSONLY").is_some() { return; }
    run("positive -10% (bound edge)", &pop, &default_outs(&pop, 90_000_000), 90_000_000, &kp);
    run("positive +10% (bound edge)", &pop, &default_outs(&pop, 110_000_000), 110_000_000, &kp);
    run("wrong signer", &pop, &default_outs(&pop, np), np, &other);
    run("price +10.01% (out of bound)", &pop, &default_outs(&pop, 110_010_000), 110_010_000, &kp);
    run("price -10.01% (out of bound)", &pop, &default_outs(&pop, 89_990_000), 89_990_000, &kp);
    run("price 0", &pop, &default_outs(&pop, 0), 0, &kp);
    run("output price differs from argument", &pop, &default_outs(&pop, np + 1), np, &kp);
    // output with wrong round
    let mut o = default_outs(&pop, np); o[n - 1].round = 7;
    run("output round not +1 (last sibling)", &pop, &o, np, &kp);
    let mut o = default_outs(&pop, np); o[1].price = np + 1_000_000;
    run("one output at a different price", &pop, &o, np, &kp);
    // missing sibling: drop last input and last output
    let pm: Vec<Pop> = pop[..n - 1].to_vec();
    run("missing sibling (N-1 in, N-1 out, n unchanged)", &pm, &default_outs(&pm, np), np, &kp);
    // missing sibling in the middle
    let mut pm2 = pop.clone(); pm2.remove(1);
    run("missing middle sibling (N-1 in, N-1 out)", &pm2, &default_outs(&pm2, np), np, &kp);
    // N inputs but only N-1 outputs
    let mut o = default_outs(&pop, np); o.pop();
    run("N inputs, N-1 outputs (sibling dropped)", &pop, &o, np, &kp);
    // extra output sibling
    let mut o = default_outs(&pop, np); o.push(Out { slot: n as i64, round: 2, price: np, n: n as i64, value: v });
    run("extra output sibling (N inputs, N+1 outputs)", &pop, &o, np, &kp);
    // extra input sibling (slot n, same covenant)
    let mut pe = pop.clone(); pe.push(Pop { txid: "dd".repeat(32), index: 0, value: v, round: 1, price: p0, slot: n as i64, n: n as i64 });
    run("extra input sibling (N+1 inputs)", &pe, &default_outs(&pe, np), np, &kp);
    // duplicated sibling: two outputs with the same slot
    let mut o = default_outs(&pop, np); o[n - 1].slot = 1;
    run("duplicated output slot", &pop, &o, np, &kp);
    // duplicated input slot
    let mut pd = pop.clone(); pd[n - 1].slot = 1;
    run("duplicated input slot (two inputs slot 1)", &pd, &default_outs(&pd, np), np, &kp);
    // mixed rounds
    let mut px = pop.clone(); px[n - 1].round = 0;
    run("mixed rounds (last sibling at round-1)", &px, &default_outs(&px, np), np, &kp);
    let mut px = pop.clone(); px[1].round = 5;
    run("mixed rounds (sibling 1 at round+4)", &px, &default_outs(&px, np), np, &kp);
    // mixed prices
    let mut px = pop.clone(); px[n - 1].price = p0 + 1;
    run("mixed prices (last sibling stale price)", &px, &default_outs(&px, np), np, &kp);
    // value changed
    let mut o = default_outs(&pop, np); o[1].value = v - 1;
    run("value of one sibling changed", &pop, &o, np, &kp);
    // n changed
    let mut o = default_outs(&pop, np); o[1].n = n as i64 + 1;
    run("n changed in one output", &pop, &o, np, &kp);
    // leader not slot 0 first
    let mut pr = pop.clone(); pr.swap(0, 1);
    run("inputs out of order (slot 1 first)", &pr, &default_outs(&pr, np), np, &kp);
    // drain
    match build_refresh(&c, &pop, &[], 0, &kp, &fund, true) { Ok((_, m, f)) => println!("RESULT[drain publisher] ACCEPT compute {} transient {} storage {} fee {}", m.0, m.1, m.2, f), Err(e) => println!("RESULT[drain publisher] REJECT {}", short(&e)) }
    match build_refresh(&c, &pop, &[], 0, &other, &fund, true) { Ok(_) => println!("RESULT[drain wrong signer] ACCEPT"), Err(e) => println!("RESULT[drain wrong signer] REJECT {}", short(&e)) }
}

// ---------- on-chain step builders ----------
fn finish(c: &Cx, label: &str, tx: &Transaction, m: (u64, u64, u64), fee: u64, next_fund: Option<(usize, u64)>) {
    let out = env("X1B_OUT");
    std::fs::write(format!("{out}/tx_{label}.json"), serde_json::to_string(tx).unwrap()).unwrap();
    println!("TXID {}", tx.id());
    println!("MASS compute {} transient {} storage {} fee {}", m.0, m.1, m.2, fee);
    if let Some((idx, amt)) = next_fund { println!("NEXT_FUND {} {} {}", tx.id(), idx, amt); }
    let _ = c;
}

#[test]
fn step_genesis() {
    let c = Cx::new();
    let n: usize = env("N").parse().unwrap();
    let v: u64 = env("V").parse().unwrap();
    let price: i64 = env("PRICE").parse().unwrap();
    let fund = read_fund();
    let build = |fee: u64| {
        let funding = UtxoEntry::new(fund.amount, c.my_spk.clone(), 0, false, None);
        let mut ctx = TxContext::new().input(op(&fund.txid, fund.index), funding, fund_cb(c.kp.clone()), 0);
        for i in 0..n {
            let p = Pop { txid: String::new(), index: 0, value: v, round: 1, price, slot: i as i64, n: n as i64 };
            ctx = ctx.actor_genesis_output(0, "launch::oracle", c.actor_of(i as i64), c.ostate(&p), v);
        }
        ctx = ctx.output(c.my_spk.clone(), None, fund.amount - n as u64 * v - fee);
        (c.builder.build(&ctx), UtxoEntry::new(fund.amount, c.my_spk.clone(), 0, false, None))
    };
    let (r, fe) = build(3_000_000);
    let tx = match r { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {}", format!("{e}").replace('\n', " ")); return; } };
    if envo("DBG").is_some() { for o in &tx.outputs { println!("OUT value {} cov {}", o.value, o.covenant.is_some()); } }
    let m = masses(&tx, vec![fe.clone()]);
    let fee = floor_fee(m) + 200;
    let (r2, _) = build(fee);
    let tx = r2.expect("rebuild");
    let m = masses(&tx, vec![fe]);
    let outpoint = op(&fund.txid, fund.index);
    let ids: Vec<_> = tx.outputs.iter().enumerate().filter(|(_, o)| o.covenant.is_some()).collect();
    let cid = covenant_id(outpoint, ids.iter().map(|(i, o)| (*i as u32, *o)));
    println!("COVENANT_ID {}", hex(cid.as_bytes().as_slice()));
    let id = tx.id().to_string();
    let pop: Vec<Pop> = (0..n).map(|i| Pop { txid: id.clone(), index: i as u32, value: v, round: 1, price, slot: i as i64, n: n as i64 }).collect();
    write_pop(&env("POP_OUT"), &pop);
    finish(&c, "genesis", &tx, m, fee, Some((n, fund.amount - n as u64 * v - fee)));
}

#[test]
fn step_refresh() {
    let c = Cx::new();
    let pop = read_pop(&env("POP"));
    let new_price: i64 = env("NEWPRICE").parse().unwrap();
    let fund = read_fund();
    let drain = envo("DRAIN").is_some();
    let sel: Vec<usize> = envo("PARTIAL").map(|s| s.split(',').map(|x| x.parse().unwrap()).collect()).unwrap_or((0..pop.len()).collect());
    let rest: Vec<Pop> = pop.iter().enumerate().filter(|(i, _)| !sel.contains(i)).map(|(_, p)| p.clone()).collect();
    let pop_all = pop.clone();
    let pop: Vec<Pop> = sel.iter().map(|&i| pop_all[i].clone()).collect();
    let outs = default_outs(&pop, new_price);
    match build_refresh(&c, &pop, &outs, new_price, &c.kp.clone(), &fund, drain) {
        Err(e) => println!("BUILD_FAILED {e}"),
        Ok((tx, m, fee)) => {
            let id = tx.id().to_string();
            if !drain {
                let np: Vec<Pop> = pop.iter().enumerate().map(|(i, p)| Pop { txid: id.clone(), index: i as u32, value: p.value, round: p.round + 1, price: new_price, slot: p.slot, n: p.n }).collect();
                let mut all = np; all.extend(rest); all.sort_by_key(|p| p.slot);
                write_pop(&env("POP_OUT"), &all);
            }
            let next = (tx.outputs.len() - 1, tx.outputs.last().unwrap().value);
            finish(&c, if drain { "drain" } else { "refresh" }, &tx, m, fee, Some(next));
        }
    }
}

/// Vault genesis (collateral from the fee input).
#[test]
fn step_vgen() {
    let c = Cx::new();
    let fund = read_fund();
    let coll: u64 = env("COLLATERAL").parse().unwrap();
    let debt: i64 = env("DEBT").parse().unwrap();
    let build = |fee: u64| {
        let funding = UtxoEntry::new(fund.amount, c.my_spk.clone(), 0, false, None);
        let ctx = TxContext::new().input(op(&fund.txid, fund.index), funding, fund_cb(c.kp.clone()), 0)
            .actor_genesis_output(0, "launch::vault", "Vault", c.vstate(debt), coll)
            .output(c.my_spk.clone(), None, fund.amount - coll - fee);
        c.builder.build(&ctx)
    };
    let fe = UtxoEntry::new(fund.amount, c.my_spk.clone(), 0, false, None);
    let tx = match build(3_000_000) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let fee = floor_fee(masses(&tx, vec![fe.clone()])) + 200;
    let tx = build(fee).unwrap();
    let m = masses(&tx, vec![fe]);
    let outpoint = op(&fund.txid, fund.index);
    let ids: Vec<_> = tx.outputs.iter().enumerate().filter(|(_, o)| o.covenant.is_some()).collect();
    let cid = covenant_id(outpoint, ids.iter().map(|(i, o)| (*i as u32, *o)));
    println!("VAULT_ID {}", hex(cid.as_bytes().as_slice()));
    finish(&c, "vgen", &tx, m, fee, Some((1, fund.amount - coll - fee)));
}

/// Vault entry (liquidate | withdraw) co-spent with one price UTXO (slot SLOT of POP, or the single entry given by POP_ENTRY) via `use`.
/// ENTRY=liquidate|withdraw. For withdraw: WITHDRAW amount. The vault is VAULT_TXID:0 with VAULT_ID, COLLATERAL, DEBT.
#[test]
fn step_vault() {
    let c = Cx::new();
    let pop = read_pop(&env("POP"));
    let slot: i64 = env("SLOT").parse().unwrap();
    let p = pop.iter().find(|p| p.slot == slot).expect("slot").clone();
    let vid = Hash::from_bytes(unhex(&env("VAULT_ID")).try_into().unwrap());
    let coll: u64 = env("COLLATERAL").parse().unwrap();
    let debt: i64 = env("DEBT").parse().unwrap();
    let entry = env("ENTRY");
    let wd: u64 = envo("WITHDRAW").map(|s| s.parse().unwrap()).unwrap_or(0);
    let vs = c.vstate(debt);
    let vu = c.builder.covenant_utxo("Vault", vs.clone(), coll, 0, false, Some(vid)).unwrap();
    let ou = c.utxo_of(&p);
    let entries = vec![vu.clone(), ou.clone()];
    let build = |fee: u64| {
        let kp = c.kp.clone();
        let call = if entry == "withdraw" { EntryCall::new("withdraw").args_with(move |tx, i| args![sign(tx, i, &kp), wd as i64]) } else { EntryCall::new("liquidate") };
        let mut ctx = TxContext::new()
            .actor_input("Vault", vs.clone(), call, op(&env("VAULT_TXID"), envo("VAULT_INDEX").map(|s| s.parse().unwrap()).unwrap_or(0)), vu.clone(), 0)
            .actor_input(c.actor_of(p.slot), c.ostate(&p), EntryCall::new("use"), op(&p.txid, p.index), ou.clone(), 0)
            .actor_output(c.actor_of(p.slot), c.ostate(&p), CovenantBinding::new(1, c.oid), p.value);
        if entry == "withdraw" {
            ctx = ctx.actor_output("Vault", vs.clone(), CovenantBinding::new(0, vid), coll - wd).output(c.my_spk.clone(), None, wd - fee);
        } else {
            ctx = ctx.output(c.my_spk.clone(), None, coll - fee);
        }
        c.builder.build(&ctx)
    };
    let tx = match build(3_000_000) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {}", format!("{e}").replace('\n', " ")); return; } };
    let fee = floor_fee(masses(&tx, entries.clone())) + 200;
    let tx = build(fee).unwrap();
    let m = masses(&tx, entries);
    finish(&c, &format!("vault_{entry}"), &tx, m, fee, None);
}

/// Attempt (build only) a spend of ONE given price entry (from POP, by SLOT) through `use` alone with a fresh fee input: used for the stale-sibling attack on spent outpoints.
#[test]
fn step_use_only() {
    let c = Cx::new();
    let pop = read_pop(&env("POP"));
    let slot: i64 = env("SLOT").parse().unwrap();
    let p = pop.iter().find(|p| p.slot == slot).expect("slot").clone();
    let fund = read_fund();
    let u = c.utxo_of(&p);
    let funding = UtxoEntry::new(fund.amount, c.my_spk.clone(), 0, false, None);
    let build = |fee: u64| {
        let ctx = TxContext::new()
            .actor_input(c.actor_of(p.slot), c.ostate(&p), EntryCall::new("use"), op(&p.txid, p.index), u.clone(), 0)
            .input(op(&fund.txid, fund.index), funding.clone(), fund_cb(c.kp.clone()), 0)
            .actor_output(c.actor_of(p.slot), c.ostate(&p), CovenantBinding::new(0, c.oid), p.value)
            .output(c.my_spk.clone(), None, fund.amount - fee);
        c.builder.build(&ctx)
    };
    let tx = match build(3_000_000) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {}", format!("{e}").replace('\n', " ")); return; } };
    let m = masses(&tx, vec![u.clone(), funding.clone()]);
    let fee = floor_fee(m) + 200;
    let tx = build(fee).unwrap();
    finish(&c, "use_only", &tx, m, fee, None);
}

/// Split one funding UTXO into K outputs of V sompi (plain), change last.
#[test]
fn step_split() {
    let c = Cx::new();
    let fund = read_fund();
    let k: usize = env("K").parse().unwrap();
    let v: u64 = env("V").parse().unwrap();
    let fe = UtxoEntry::new(fund.amount, c.my_spk.clone(), 0, false, None);
    let build = |fee: u64| {
        let mut ctx = TxContext::new().input(op(&fund.txid, fund.index), fe.clone(), fund_cb(c.kp.clone()), 0);
        for _ in 0..k { ctx = ctx.output(c.my_spk.clone(), None, v); }
        ctx = ctx.output(c.my_spk.clone(), None, fund.amount - v * k as u64 - fee);
        c.builder.build(&ctx)
    };
    let tx = match build(3_000_000) { Ok(t) => t, Err(e) => { println!("BUILD_FAILED {e}"); return; } };
    let fee = floor_fee(masses(&tx, vec![fe.clone()])) + 200;
    let tx = build(fee).unwrap();
    let m = masses(&tx, vec![fe]);
    finish(&c, "split", &tx, m, fee, Some((k, fund.amount - v * k as u64 - fee)));
}
