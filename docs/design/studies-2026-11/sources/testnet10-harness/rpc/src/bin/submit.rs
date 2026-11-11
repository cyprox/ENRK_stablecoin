use kaspa_consensus_core::tx::Transaction;
use kaspa_rpc_core::{api::rpc::RpcApi, RpcTransaction};
use kaspa_wrpc_client::{client::ConnectOptions, prelude::*, KaspaRpcClient, WrpcEncoding};
#[tokio::main]
async fn main() {
    let path = std::env::args().nth(1).expect("tx json path");
    let tx: Transaction = serde_json::from_str(&std::fs::read_to_string(path).unwrap()).expect("tx json");
    let client = KaspaRpcClient::new(WrpcEncoding::Borsh, None, Some(Resolver::default()), Some(NetworkId::with_suffix(NetworkType::Testnet, 10)), None).unwrap();
    client.connect(Some(ConnectOptions::blocking_fallback())).await.unwrap();
    let rpc_tx: RpcTransaction = (&tx).into();
    match client.submit_transaction(rpc_tx, false).await {
        Ok(id) => println!("SUBMITTED {id}"),
        Err(e) => println!("REJECTED {e}"),
    }
    let _ = client.disconnect().await;
}
