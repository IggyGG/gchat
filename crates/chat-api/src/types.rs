fn main() {
    if std::env::args().any(|arg| arg == "--rpc") {
        println!(
            "{}",
            serde_json::to_string_pretty(&gchat_api::rpc::export()).expect("chat schemas")
        );
    } else {
        print!("{}", gchat_api::typescript());
    }
}
