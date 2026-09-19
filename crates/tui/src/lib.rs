//! gchat: terminal client for the GC/1 protocol. The binary in `main.rs` is
//! a thin shell; everything testable lives here.

pub mod app;
pub mod clipboard;
pub mod exec;
mod files;
pub mod form;
pub mod input;
pub mod service_ui;
pub mod text;
pub mod ui;
