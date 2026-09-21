/// Errors deliberately contain no native exception text, slots or secrets.
#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("invalid unlock slot")]
    InvalidSlot,
    #[error("invalid unlock secret")]
    InvalidSecret,
    #[error("native unlock storage is unavailable")]
    NativeUnavailable,
    #[error("native unlock storage is unsupported on this platform")]
    Unsupported,
}

pub type Result<T> = std::result::Result<T, Error>;
