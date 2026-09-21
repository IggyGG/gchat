fn main() {
    // This executable also runs the retained-profile daemon with --interactive.
    // Its startup future needs the same main-thread reserve as the CLI daemon.
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("windows")
        && std::env::var("CARGO_CFG_TARGET_ENV").as_deref() == Ok("msvc")
    {
        println!("cargo:rustc-link-arg-bin=gchat-desktop=/STACK:8388608");
    }
    tauri_build::build()
}
