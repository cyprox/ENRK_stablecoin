//! v4 local-only: controller poke reading 4 shard siblings. No network.
use argent::builder::{ArtifactBundle, ArtifactValue, EntryCall, TxBuilder, TxContext};
use kaspa_consensus_core::{config::params::MAINNET_PARAMS, mass::MassCalculator, tx::{CovenantBinding, PopulatedTransaction, TransactionId, TransactionOutpoint}, Hash};
use std::collections::BTreeMap;

fn op(tag: u8) -> TransactionOutpoint { TransactionOutpoint::new(TransactionId::from_bytes([tag; 32]), 0) }
fn int(v: i64) -> ArtifactValue { ArtifactValue::Int(v) }
fn st(p: Vec<(&str, ArtifactValue)>) -> BTreeMap<String, ArtifactValue> { p.into_iter().map(|(k, v)| (k.to_string(), v)).collect() }

struct Case<'a> { label: &'a str, shards: Vec<(i64, i64)>, out_shards: Option<Vec<(i64, i64)>>, r: i64, last: i64, lock: u64, foreign: Option<usize>, n_in: usize }

fn run(c: Case) {
    let dir = std::env::var("V4_DIR").unwrap();
    let out = std::env::temp_dir().join(format!("v4_ctl_{}_{}", std::process::id(), c.label.len()));
    let a = Box::leak(Box::new(argent::build_file(format!("{dir}/ctl.ag"), &out.join("c")).unwrap()));
    let s = Box::leak(Box::new(argent::build_file(format!("{dir}/shard.ag"), &out.join("s")).unwrap()));
    let bundle = ArtifactBundle::new(&*a).unwrap().with_app("shards", &*s).unwrap();
    let b = TxBuilder::from_bundle(&bundle).unwrap();
    let sh_id = Hash::from_bytes([0x42; 32]);
    let other_id = Hash::from_bytes([0x43; 32]);
    let ctl_id = Hash::from_bytes([0x77; 32]);
    let cst = st(vec![("shard_covid", ArtifactValue::Bytes(sh_id.as_bytes().to_vec())), ("r", int(c.r)), ("last", int(c.last))]);
    let cu = b.covenant_utxo("Ctl", cst.clone(), 100_000_000, 0, false, Some(ctl_id)).unwrap();
    let mut entries = vec![cu.clone()];
    let mut ctx = TxContext::new().lock_time(c.lock).actor_input("Ctl", cst.clone(), EntryCall::new("poke"), op(1), cu, 0);
    for (i, (f, p)) in c.shards.iter().enumerate().take(c.n_in) {
        let ss = st(vec![("free", int(*f)), ("paid", int(*p))]);
        let id = if c.foreign == Some(i) { other_id } else { sh_id };
        let u = b.covenant_utxo("shards::Cnt", ss.clone(), 2_000_000_000, 0, false, Some(id)).unwrap();
        entries.push(u.clone());
        ctx = ctx.actor_input("shards::Cnt", ss, EntryCall::new("use"), op(10 + i as u8), u, 0);
    }
    // successor controller: expected r computed by the harness caller via env-free path: the script computes it; we pass the value we expect
    let exp_r: i64 = std::env::var("V4_EXPR").map(|v| v.parse().unwrap()).unwrap_or(c.r);
    let nst = st(vec![("shard_covid", ArtifactValue::Bytes(sh_id.as_bytes().to_vec())), ("r", int(exp_r)), ("last", int(c.lock as i64))]);
    ctx = ctx.actor_output("Ctl", nst, CovenantBinding::new(0, ctl_id), 100_000_000);
    let outs = c.out_shards.clone().unwrap_or(c.shards.clone());
    for (i, (f, p)) in outs.iter().enumerate().take(c.n_in) {
        let ss = st(vec![("free", int(*f)), ("paid", int(*p))]);
        ctx = ctx.actor_output("shards::Cnt", ss, CovenantBinding::new(1 + i as u16, if c.foreign == Some(i) { other_id } else { sh_id }), 2_000_000_000);
    }
    match b.build(&ctx) {
        Ok(tx) => {
            let calc = MassCalculator::new_with_consensus_params(&MAINNET_PARAMS);
            let nc = calc.calc_non_contextual_masses(&tx);
            let stor = calc.calc_contextual_masses(&PopulatedTransaction::new(&tx, entries)).map(|m| m.storage_mass);
            println!("RESULT [{}] ACCEPT compute {} transient {} storage {:?}", c.label, nc.compute_mass, nc.transient_mass, stor);
        }
        Err(e) => { let m = format!("{e}").replace('\n', " "); println!("RESULT [{}] REJECT {}", c.label, &m[..m.len().min(150)]); }
    }
}

#[test]
fn ctl_cases() {
    let sh = vec![(100, 900), (50, 450), (0, 500), (10, 90)]; // free ratio 160/2000 = 8% < 30%  -> dir +1
    let base = |l: &'static str| Case { label: l, shards: sh.clone(), out_shards: None, r: 50_000_000, last: 1000, lock: 1000 + 86400, foreign: None, n_in: 4 };
    run(base("poke dir=+1 dt=1d (expected r from python)"));
    run(Case { lock: 1000 + 3599, ..base("dt below DT_MIN") });
    run(Case { lock: 999, ..base("lock_time below last (CLTV)") });
    run(Case { out_shards: Some(vec![(100, 900), (50, 450), (0, 500), (11, 90)]), ..base("shard output tampered") });
    run(Case { n_in: 3, ..base("only 3 shards co-spent") });
    run(Case { foreign: Some(2), ..base("one shard of a foreign covenant id") });
    run(Case { shards: vec![(9_000_000_000_000_000, 1), (1, 1), (1, 1), (1, 1)], out_shards: None, ..base("sum above SUM_MAX") });
}
