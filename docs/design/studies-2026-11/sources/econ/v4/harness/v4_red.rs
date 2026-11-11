//! v4 local-only: targeted redemption + per-vault liquidation fee tests (no network).
use argent::builder::{args, ArtifactBundle, ArtifactValue, EntryCall, TxBuilder, TxContext};
use kaspa_consensus_core::{config::params::MAINNET_PARAMS, mass::MassCalculator, tx::{CovenantBinding, PopulatedTransaction, TransactionId, TransactionOutpoint}, Hash};
use secp256k1::{Keypair, Secp256k1, SecretKey};
use std::collections::BTreeMap;

fn kp(b: u8) -> Keypair { Keypair::from_secret_key(&Secp256k1::new(), &SecretKey::from_slice(&[b; 32]).unwrap()) }
fn pkb(k: &Keypair) -> Vec<u8> { k.x_only_public_key().0.serialize().to_vec() }
fn op(t: u8) -> TransactionOutpoint { TransactionOutpoint::new(TransactionId::from_bytes([t; 32]), 0) }
fn ost() -> BTreeMap<String, ArtifactValue> {
    let mut s = BTreeMap::new();
    s.insert("publisher".into(), ArtifactValue::Bytes(pkb(&kp(9)))); s.insert("round".into(), ArtifactValue::Int(1)); s.insert("last".into(), ArtifactValue::Int(1000)); s
}
fn vst(oid: Hash, debt: i64, free: i64) -> BTreeMap<String, ArtifactValue> {
    let mut s = BTreeMap::new();
    s.insert("owner".into(), ArtifactValue::Bytes(pkb(&kp(21)))); s.insert("oracle_covid".into(), ArtifactValue::Bytes(oid.as_bytes().to_vec()));
    s.insert("debt".into(), ArtifactValue::Int(debt)); s.insert("free".into(), ArtifactValue::Int(free)); s
}
fn pst(to: Vec<u8>) -> BTreeMap<String, ArtifactValue> { let mut s = BTreeMap::new(); s.insert("to".into(), ArtifactValue::Bytes(to)); s }

struct C<'a> { label: &'a str, entry: &'a str, price: u64, c: u64, debt: i64, free: i64, x: i64, pay: u64, next_v: u64, next_debt: i64 }
fn run(k: C) {
    let dir = std::env::var("V4_DIR").unwrap();
    let out = std::env::temp_dir().join(format!("v4_red_{}", std::process::id()));
    let v = Box::leak(Box::new(argent::build_file(format!("{dir}/vault_redeem.ag"), &out.join("v")).unwrap()));
    let o = Box::leak(Box::new(argent::build_file(format!("{dir}/oracle.ag"), &out.join("o")).unwrap()));
    let b = TxBuilder::from_bundle(&ArtifactBundle::new(&*v).unwrap().with_app("oracle_feed", &*o).unwrap()).unwrap();
    let (oid, vid) = (Hash::from_bytes([0x42; 32]), Hash::from_bytes([0x77; 32]));
    let os = ost(); let vs = vst(oid, k.debt, k.free);
    let vu = b.covenant_utxo("Vault", vs.clone(), k.c, 0, false, Some(vid)).unwrap();
    let ou = b.covenant_utxo("oracle_feed::PriceRound", os.clone(), k.price, 0, false, Some(oid)).unwrap();
    let entries = vec![vu.clone(), ou.clone()];
    let rp = pkb(&kp(33)); let rp2 = rp.clone(); let x = k.x;
    let call = EntryCall::new(k.entry).args_with(move |_tx, _i| args![x, rp2.clone()]);
    let ctx = TxContext::new()
        .actor_input("Vault", vs.clone(), call, op(1), vu, 0)
        .actor_input("oracle_feed::PriceRound", os.clone(), EntryCall::new("use"), op(2), ou, 0)
        .actor_output("Vault", vst(oid, k.next_debt, k.free), CovenantBinding::new(0, vid), k.next_v)
        .actor_output("Pay", pst(rp), CovenantBinding::new(0, vid), k.pay)
        .actor_output("oracle_feed::PriceRound", os, CovenantBinding::new(1, oid), k.price);
    match b.build(&ctx) {
        Ok(tx) => {
            let m = MassCalculator::new_with_consensus_params(&MAINNET_PARAMS);
            let nc = m.calc_non_contextual_masses(&tx);
            let lab = k.label.to_string();
            let r = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| m.calc_contextual_masses(&PopulatedTransaction::new(&tx, entries)).map(|x| x.storage_mass)));
            match r { Ok(s) => println!("RESULT [{}] ACCEPT compute {} transient {} storage {:?}", lab, nc.compute_mass, nc.transient_mass, s),
                      Err(_) => println!("RESULT [{}] ACCEPT by script engine; storage-mass calculator PANICS (zero-value covenant output)", lab) }
        }
        Err(e) => { let m = format!("{e}").replace('\n', " "); println!("RESULT [{}] REJECT {}", k.label, &m[..m.len().min(110)]) }
    }
}
#[test]
fn red_cases() {
    let p = 100_000_000u64;
    // redeem. vault: c=1e9 sompi (10 KAS), p=1.0 -> value 1e9; debt 4e8 -> ICR 250
    let r = |label, price, c, debt, free, x: i64, pay, nv: u64, nd| run(C { label, entry: "redeem", price, c, debt, free, x, pay, next_v: nv, next_debt: nd });
    r("redeem ICR250 x=1e8 (fee capped 10%): net 9e7", p, 1_000_000_000, 400_000_000, 1, 100_000_000, 90_000_000, 910_000_000, 300_000_000);
    r("redeem ICR111 x=1e8 (fee 1.6%): net 98.4e6", p, 500_000_000, 450_000_000, 1, 100_000_000, 98_400_000, 401_600_000, 350_000_000);
    r("redeem PAID vault (must reject)", p, 1_000_000_000, 400_000_000, 0, 100_000_000, 90_000_000, 910_000_000, 300_000_000);
    r("redeem x > debt (must reject)", p, 1_000_000_000, 400_000_000, 1, 500_000_000, 90_000_000, 910_000_000, 0);
    r("redeem leaves dust debt 5e7 (must reject)", p, 1_000_000_000, 400_000_000, 1, 350_000_000, 300_000_000, 700_000_000, 50_000_000);
    r("redeem full debt x=4e8", p, 1_000_000_000, 400_000_000, 1, 400_000_000, 360_000_000, 640_000_000, 0);
    r("redeem pay over by 1 sompi (must reject)", p, 1_000_000_000, 400_000_000, 1, 100_000_000, 90_000_001, 909_999_999, 300_000_000);
    r("redeem x below MIN_REDEEM (must reject)", p, 1_000_000_000, 400_000_000, 1, 999_999, 899_999, 999_100_001, 399_000_001);
    r("redeem price below P_LO=1e6 (must reject)", 999_999, 1_000_000_000, 400_000_000, 1, 100_000_000, 90_000_000, 910_000_000, 300_000_000);
    // stale-low sibling 0.9 instead of 1.0: collateral per unit +11 %
    r("redeem at stale-LOW sibling p=0.9: net 1e8/0.9*0.9=1e8", 90_000_000, 1_000_000_000, 400_000_000, 1, 100_000_000, 100_000_000, 900_000_000, 300_000_000);
    r("redeem from UNDERWATER vault ICR 80% (guard absent)", p, 360_000_000, 450_000_000, 1, 100_000_000, 99_500_000, 260_500_000, 350_000_000);
    // liquidate: ICR 120 (c=5.4e8, d=4.5e8)
    let l = |label, price, c, debt, x: i64, pay, nv: u64, nd| run(C { label, entry: "liquidate", price, c, debt, free: 1, x, pay, next_v: nv, next_debt: nd });
    l("liquidate ICR120 FULL repay=4.5e8 clean fee 10%: seize 4.95e8", p, 540_000_000, 450_000_000, 450_000_000, 495_000_000, 45_000_000, 0);
    l("liquidate ICR120 PARTIAL repay=1e8 dirty 9%: seize 1.09e8", p, 540_000_000, 450_000_000, 100_000_000, 109_000_000, 431_000_000, 350_000_000);
    l("liquidate PARTIAL claiming clean fee (must reject)", p, 540_000_000, 450_000_000, 100_000_000, 110_000_000, 430_000_000, 350_000_000);
    l("liquidate repay=0 (must reject)", p, 540_000_000, 450_000_000, 0, 0, 540_000_000, 450_000_000);
    l("liquidate repay>debt (must reject)", p, 540_000_000, 450_000_000, 450_000_001, 495_000_000, 45_000_000, 0);
    l("liquidate healthy ICR250 (must reject)", p, 1_000_000_000, 400_000_000, 100_000_000, 109_000_000, 891_000_000, 300_000_000);
    l("liquidate repay=1 unit (no close factor, dust)", p, 540_000_000, 450_000_000, 1, 1, 539_999_999, 449_999_999);
    l("liquidate UNDERWATER ICR90 full: seize capped at all collateral", p, 405_000_000, 450_000_000, 450_000_000, 405_000_000, 0, 0);
}
