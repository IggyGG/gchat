// Exercise the desktop's actual argument policy without requiring a GUI runtime.
#![cfg(not(any(target_os = "android", target_os = "ios")))]

#[path = "../../../apps/client/src-tauri/src/startup.rs"]
mod startup;
