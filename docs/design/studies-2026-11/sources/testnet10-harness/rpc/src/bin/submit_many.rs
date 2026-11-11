use kaspa_consensus_core::tx::Transaction;
use kaspa_rpc_core::{api::rpc::RpcApi, RpcTransaction};
use kaspa_wrpc_client::{client::ConnectOptions, prelude::*, KaspaRpcClient, WrpcEncoding};
// usage: submit_many <tx1.json> <tx2.json> ... ; submits sequentially over one connection, prints per-tx ack time (ms since first submit)
#[tokio::main]
async fn main() {
    let paths: Vec<String> = std::env::args().skip(1).collect();
    let txs: Vec<Transaction> = paths.iter().map(|p| serde_json::from_str(&std::fs::read_to_string(p).unwrap()).expect("tx json")).collect();
    let client = KaspaRpcClient::new(WrpcEncoding::Borsh, None, Some(Resolver::default()), Some(NetworkId::with_suffix(NetworkType::Testnet, 10)), None).unwrap();
    client.connect(Some(ConnectOptions::blocking_fallback())).await.unwrap();
    let t0 = std::time::Instant::now();
    let w0 = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_millis();
    println!("WALL_START_MS {w0}");
    for (i, tx) in txs.iter().enumerate() {
        let rpc_tx: RpcTransaction = tx.into();
        match client.submit_transaction(rpc_tx, false).await {
            Ok(id) => println!("SUBMITTED {i} {id} t_ms {}", t0.elapsed().as_millis()),
            Err(e) => println!("REJECTED {i} {} t_ms {} :: {e}", tx.id(), t0.elapsed().as_millis()),
        }
    }
    let _ = client.disconnect().await;
}
