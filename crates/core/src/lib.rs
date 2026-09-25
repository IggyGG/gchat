//! gc-client-core: contacts, conversations, encrypted-at-rest store over gc-node.

pub mod bootstrap;
pub mod build_info;
pub mod chat_service;
pub mod client;
pub mod contact;
pub mod conversation;
pub mod daemon;
pub mod dns;
pub mod model;
pub mod paths;
pub mod private_fs;
pub mod runtime;
pub mod store;
pub mod transcript;

pub mod network;
