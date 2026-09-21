//! Desktop attaches to its local service; phones own one outbound client.
#[cfg(not(any(target_os = "android", target_os = "ios")))]
mod desktop;
#[cfg(any(target_os = "android", target_os = "ios", test))]
#[cfg_attr(not(any(target_os = "android", target_os = "ios")), allow(dead_code))]
mod mobile;
#[cfg(any(target_os = "android", target_os = "ios", test))]
mod mobile_export;
#[cfg(not(any(target_os = "android", target_os = "ios")))]
mod startup;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    #[cfg(not(any(target_os = "android", target_os = "ios")))]
    desktop::run();
    #[cfg(any(target_os = "android", target_os = "ios"))]
    mobile::run();
}
