use kaspa_rpc_core::api::rpc::RpcApi;
use kaspa_wrpc_client::{client::ConnectOptions, prelude::*, KaspaRpcClient, WrpcEncoding};
#[tokio::main]
async fn main() {
    let client = KaspaRpcClient::new(WrpcEncoding::Borsh, None, Some(Resolver::default()), Some(NetworkId::with_suffix(NetworkType::Testnet, 10)), None).unwrap();
    client.connect(Some(ConnectOptions::blocking_fallback())).await.unwrap();
    let d = client.get_block_dag_info().await.unwrap();
    let now = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_millis();
    let tip = d.tip_hashes[0];
    let b = client.get_block(tip, false).await.unwrap();
    println!("daa {} past_median_time {} tip_timestamp {} tip_daa {} wall_ms {}", d.virtual_daa_score, d.past_median_time, b.header.timestamp, b.header.daa_score, now);
    println!("pmt_lag_ms {} tip_lag_ms {}", now as i128 - d.past_median_time as i128, now as i128 - b.header.timestamp as i128);
    client.disconnect().await.unwrap();
}
