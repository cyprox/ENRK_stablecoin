use kaspa_wrpc_client::{prelude::*, client::ConnectOptions, KaspaRpcClient, WrpcEncoding};
use kaspa_rpc_core::api::rpc::RpcApi;
#[tokio::main]
async fn main() {
    let resolver = Resolver::default();
    let client = KaspaRpcClient::new(WrpcEncoding::Borsh, None, Some(resolver), Some(NetworkId::with_suffix(NetworkType::Testnet, std::env::var("TNSUFFIX").ok().and_then(|s| s.parse().ok()).unwrap_or(10))), None).unwrap();
    client.connect(Some(ConnectOptions::blocking_fallback())).await.unwrap();
    let info = client.get_server_info().await.unwrap();
    println!("server: network={:?} synced={} version={}", info.network_id, info.is_synced, info.server_version);
    let d = client.get_block_dag_info().await.unwrap();
    println!("daa {}", d.virtual_daa_score);
    client.disconnect().await.unwrap();
}
