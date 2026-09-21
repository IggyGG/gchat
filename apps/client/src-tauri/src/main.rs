#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
#[cfg(not(any(target_os = "android", target_os = "ios")))]
fn main() {
    use clap::Parser;
    if std::env::args_os().any(|arg| arg == "--interactive") {
        #[derive(Parser)]
        struct ServiceArgs {
            #[command(flatten)]
            daemon: gchat_core::daemon::DaemonArgs,
        }
        let runtime = tokio::runtime::Runtime::new().expect("service runtime");
        if let Err(error) = runtime.block_on(gchat_core::daemon::run(ServiceArgs::parse().daemon)) {
            eprintln!("{error}");
            std::process::exit(1);
        }
    } else {
        gchat_native::run();
    }
}

#[cfg(any(target_os = "android", target_os = "ios"))]
fn main() {
    gchat_native::run();
}
