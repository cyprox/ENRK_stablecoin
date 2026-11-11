//! Scratch: generate a throwaway TESTNET-10 key (never mainnet). Secret kept in the scratchpad only.
use kaspa_addresses::{Address, Prefix, Version};
use secp256k1::{Keypair, Secp256k1, SecretKey};
use std::{fs, io::Read, os::unix::fs::PermissionsExt};

#[test]
fn keygen() {
    let dir = std::env::var("TN10_DIR").expect("TN10_DIR");
    let keyfile = format!("{dir}/tn10_key.hex");
    if !std::path::Path::new(&keyfile).exists() {
        let mut b = [0u8; 32];
        fs::File::open("/dev/urandom").unwrap().read_exact(&mut b).unwrap();
        let sk = SecretKey::from_slice(&b).expect("valid key");
        fs::write(&keyfile, hex(&sk.secret_bytes())).unwrap();
        fs::set_permissions(&keyfile, fs::Permissions::from_mode(0o600)).unwrap();
    }
    let sk = SecretKey::from_slice(&unhex(fs::read_to_string(&keyfile).unwrap().trim())).unwrap();
    let kp = Keypair::from_secret_key(&Secp256k1::new(), &sk);
    let xonly = kp.x_only_public_key().0.serialize();
    let addr = Address::new(Prefix::Testnet, Version::PubKey, &xonly);
    let af = format!("{dir}/tn10_address.txt");
    fs::write(&af, addr.to_string()).unwrap();
    println!("TN10_ADDRESS {}", addr);
}
fn hex(b: &[u8]) -> String { b.iter().map(|x| format!("{x:02x}")).collect() }
fn unhex(s: &str) -> Vec<u8> { (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect() }
