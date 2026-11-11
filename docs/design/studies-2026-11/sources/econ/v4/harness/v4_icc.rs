//! v4 local-only: P11 invariants - cap bypass / negative mint / burn attempts on the ICC KCC20 example (no network).
use argent::builder::{args, ArtifactBundle, ArtifactValue, EntryCall, TxBuilder, TxContext};
use kaspa_consensus_core::{hashing::{sighash::{SigHashReusedValuesUnsync, calc_schnorr_signature_hash}, sighash_type::SIG_HASH_ALL}, tx::{CovenantBinding, MutableTransaction, Transaction, TransactionId, TransactionOutpoint}, Hash};
use secp256k1::{Keypair, Secp256k1, SecretKey};
use std::collections::BTreeMap;
type S = BTreeMap<String, ArtifactValue>;
fn kp(b: u8) -> Keypair { Keypair::from_secret_key(&Secp256k1::new(), &SecretKey::from_slice(&[b; 32]).unwrap()) }
fn pkb(k: &Keypair) -> Vec<u8> { k.x_only_public_key().0.serialize().to_vec() }
fn sign<T: AsRef<Transaction>>(tx: &MutableTransaction<T>, i: usize, k: &Keypair) -> Vec<u8> {
    let r = SigHashReusedValuesUnsync::new();
    let h = calc_schnorr_signature_hash(&tx.as_verifiable(), i, SIG_HASH_ALL, &r);
    let m = secp256k1::Message::from_digest_slice(h.as_bytes().as_slice()).unwrap();
    let mut s = k.sign_schnorr(m).as_ref().to_vec(); s.push(SIG_HASH_ALL.to_u8()); s
}
fn op(t: u8) -> TransactionOutpoint { TransactionOutpoint::new(TransactionId::from_bytes([t; 32]), 0) }
fn mst(owner: Vec<u8>, cov: Hash, amount: i64) -> S {
    let mut s = S::new(); s.insert("owner".into(), ArtifactValue::Bytes(owner)); s.insert("kcc20_covid".into(), ArtifactValue::Bytes(cov.as_bytes().to_vec()));
    s.insert("amount".into(), ArtifactValue::Int(amount)); s.insert("initialized".into(), ArtifactValue::Bool(true)); s
}
fn pst(c: Hash) -> S { let mut s = S::new(); s.insert("controller_id".into(), ArtifactValue::Bytes(c.as_bytes().to_vec())); s }
fn kst(o: Vec<u8>, amount: i64) -> S {
    let mut s = S::new(); s.insert("owner_identifier".into(), ArtifactValue::Bytes(o)); s.insert("identifier_type".into(), ArtifactValue::Byte(0)); s.insert("amount".into(), ArtifactValue::Int(amount)); s
}
fn show(label: &str, r: Result<Transaction, argent::builder::BuilderError>) {
    match r { Ok(_) => println!("RESULT [{label}] ACCEPT"), Err(e) => { let m = format!("{e}").replace('\n', " "); println!("RESULT [{label}] REJECT {}", &m[..m.len().min(120)]) } }
}
#[test]
fn icc_cases() {
    let dir = std::env::var("V4_DIR").unwrap();
    let out = std::env::temp_dir().join(format!("v4_icc_{}", std::process::id()));
    let ca = Box::leak(Box::new(argent::build_file(format!("{dir}/minter_x.ag"), &out.join("c")).unwrap()));
    let aa = Box::leak(Box::new(argent::build_file(format!("{dir}/kcc20_asset.ag"), &out.join("a")).unwrap()));
    // ABI surface: which privileged entries exist?
    for (actor, art) in [("KCC20", &*aa), ("MinterProxy", &*aa), ("Minter", &*ca)] {
        let c = art.sil_abi.contract(actor).unwrap();
        let names = ["freeze", "pause", "burn", "sweep", "set_cap", "set_amount", "mint", "transfer", "rotate", "upgrade"];
        let present: Vec<&str> = names.iter().copied().filter(|n| c.entry(n).is_some()).collect();
        println!("ABI {actor}: present among probes = {present:?}");
    }
    let b = TxBuilder::from_bundle(&ArtifactBundle::new(&*ca).unwrap().with_app("kcc20_asset", &*aa).unwrap()).unwrap();
    let owner = kp(9); let opk = pkb(&owner); let rec = vec![0x55; 32];
    let (cc, ac) = (Hash::from_bytes([0xc0; 32]), Hash::from_bytes([0xa5; 32]));
    let (mv, pv, rv) = (3000u64, 2000u64, 1000u64);
    let mint_case = |label: &str, cap: i64, minted: i64, recipient_amt: i64, next_cap: i64, signer: Keypair| {
        let ms = mst(opk.clone(), ac, cap); let mn = mst(opk.clone(), ac, next_cap); let ps = pst(cc); let rs = kst(rec.clone(), recipient_amt);
        let mu = b.covenant_utxo("Minter", ms.clone(), mv, 0, false, Some(cc)).unwrap();
        let pu = b.covenant_utxo("kcc20_asset::MinterProxy", ps.clone(), pv, 0, false, Some(ac)).unwrap();
        let recc = rec.clone(); let rsc = rs.clone();
        let ctx = TxContext::new()
            .actor_input("Minter", ms, EntryCall::new("mint").args_with(move |tx, i| args![sign(tx, i, &signer), recc.clone(), minted]), op(1), mu, 0)
            .actor_input("kcc20_asset::MinterProxy", ps.clone(), EntryCall::new("mint").args(args![ps.clone(), rsc]), op(2), pu, 0)
            .actor_output("Minter", mn, CovenantBinding::new(0, cc), mv)
            .actor_output("kcc20_asset::MinterProxy", ps, CovenantBinding::new(1, ac), pv)
            .actor_output("kcc20_asset::KCC20", rs, CovenantBinding::new(1, ac), rv);
        show(label, b.build(&ctx));
    };
    mint_case("A honest mint 17 of cap 100", 100, 17, 17, 83, kp(9));
    mint_case("B mint 101 > cap 100 (must reject)", 100, 101, 101, -1, kp(9));
    mint_case("C NEGATIVE mint -5: cap rises 100 -> 105", 100, -5, -5, 105, kp(9));
    mint_case("D proxy recipient 50 while controller approves 17 (must reject)", 100, 17, 50, 83, kp(9));
    mint_case("E non-owner signature (must reject)", 100, 17, 17, 83, kp(11));
    // F: controller co-spent through the EXTRA `rotate` entry, proxy mints an arbitrary amount (presence-only co_spent)
    {
        let ms = mst(opk.clone(), ac, 100); let mn = mst(pkb(&kp(12)), ac, 100); let ps = pst(cc); let rs = kst(rec.clone(), 1_000_000_000_000);
        let mu = b.covenant_utxo("Minter", ms.clone(), mv, 0, false, Some(cc)).unwrap();
        let pu = b.covenant_utxo("kcc20_asset::MinterProxy", ps.clone(), pv, 0, false, Some(ac)).unwrap();
        let newpk = pkb(&kp(12)); let rsc = rs.clone(); let o2 = kp(9);
        let ctx = TxContext::new()
            .actor_input("Minter", ms, EntryCall::new("rotate").args_with(move |tx, i| args![sign(tx, i, &o2), newpk.clone()]), op(1), mu, 0)
            .actor_input("kcc20_asset::MinterProxy", ps.clone(), EntryCall::new("mint").args(args![ps.clone(), rsc]), op(2), pu, 0)
            .actor_output("Minter", mn, CovenantBinding::new(0, cc), mv)
            .actor_output("kcc20_asset::MinterProxy", ps, CovenantBinding::new(1, ac), pv)
            .actor_output("kcc20_asset::KCC20", rs, CovenantBinding::new(1, ac), rv);
        show("F CAP BYPASS: controller spent via rotate(), proxy mints 1e12 (cap 100)", b.build(&ctx));
    }
    // G: KCC20 transfer that changes the amount (burn to 0 / inflate)
    for (label, out_amt) in [("G KCC20 transfer 100 -> output amount 0 (burn attempt, must reject)", 0i64), ("H KCC20 transfer 100 -> output 101 (inflate, must reject)", 101), ("I KCC20 transfer amount kept 100", 100)] {
        let ks = kst(opk.clone(), 100); let kn = kst(vec![0x66; 32], out_amt);
        let ku = b.covenant_utxo("kcc20_asset::KCC20", ks.clone(), rv, 0, false, Some(ac)).unwrap();
        let o = kp(9);
        let ctx = TxContext::new()
            .actor_input("kcc20_asset::KCC20", ks, EntryCall::new("transfer").args_with(move |tx, i| args![vec![0x66u8; 32], 0u8, sign(tx, i, &o)]), op(3), ku, 0)
            .actor_output("kcc20_asset::KCC20", kn, CovenantBinding::new(0, ac), rv);
        show(label, b.build(&ctx));
    }
}
