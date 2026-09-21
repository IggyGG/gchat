fn main() {
    // The retained-profile daemon startup future exceeds Windows' default
    // 1 MiB main-thread stack in unoptimized native builds. Match the ordinary
    // Linux/macOS main-thread reserve; pages are committed only as needed.
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("windows")
        && std::env::var("CARGO_CFG_TARGET_ENV").as_deref() == Ok("msvc")
    {
        println!("cargo:rustc-link-arg-bin=gchat=/STACK:8388608");
    }
}
