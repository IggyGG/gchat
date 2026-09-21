fn main() {
    // The vault has no webview commands: only trusted Rust code can invoke it.
    tauri_plugin::Builder::new(&[])
        .android_path("android")
        .ios_path("ios")
        .build();
}
