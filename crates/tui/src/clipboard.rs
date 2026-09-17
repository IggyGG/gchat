//! Clipboard with honest reporting. A local helper is tried first; over SSH
//! (where a helper would run on the wrong machine) or without one, the
//! OSC 52 escape is written, which some terminals silently ignore.

use base64::Engine;
use std::io::Write;
use std::process::{Command, Stdio};

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CopyOutcome {
    /// A local helper accepted the text.
    Tool(&'static str),
    /// OSC 52 was written to the terminal; delivery cannot be confirmed.
    Osc52,
    Failed(String),
}

impl CopyOutcome {
    /// Status line text; never claims more than what was verified.
    pub fn message(&self) -> String {
        match self {
            CopyOutcome::Tool(name) => format!("copied ({name})"),
            CopyOutcome::Osc52 => {
                "sent to the terminal clipboard (OSC 52); if nothing arrived, press e to export a file"
                    .into()
            }
            CopyOutcome::Failed(error) => format!("clipboard failed: {error}; press e to export"),
        }
    }
    pub fn is_failure(&self) -> bool {
        matches!(self, CopyOutcome::Failed(_))
    }
}

fn env_set(name: &str) -> bool {
    std::env::var_os(name).is_some_and(|value| !value.is_empty())
}

/// Local helpers worth trying in this environment, in order.
fn helpers() -> Vec<(&'static str, &'static [&'static str])> {
    let mut list: Vec<(&'static str, &'static [&'static str])> = Vec::new();
    if env_set("TERMUX_VERSION") {
        list.push(("termux-clipboard-set", &[]));
    }
    if cfg!(target_os = "macos") {
        list.push(("pbcopy", &[]));
    }
    if env_set("WAYLAND_DISPLAY") {
        list.push(("wl-copy", &[]));
    }
    if env_set("DISPLAY") {
        list.push(("xclip", &["-selection", "clipboard"]));
        list.push(("xsel", &["--clipboard", "--input"]));
    }
    if cfg!(windows) {
        list.push(("clip.exe", &[]));
    }
    list
}

fn run_helper(program: &str, args: &[&str], text: &str) -> Result<(), std::io::Error> {
    let mut child = Command::new(program)
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()?;
    if let Some(mut stdin) = child.stdin.take() {
        stdin.write_all(text.as_bytes())?;
    }
    let status = child.wait()?;
    if status.success() {
        Ok(())
    } else {
        Err(std::io::Error::other(format!(
            "{program} exited with {status}"
        )))
    }
}

fn write_osc52(text: &str) -> Result<(), std::io::Error> {
    let encoded = base64::engine::general_purpose::STANDARD.encode(text);
    let mut out = std::io::stdout();
    write!(out, "\x1b]52;c;{encoded}\x07")?;
    out.flush()
}

pub fn copy(text: &str) -> CopyOutcome {
    // Over SSH a local helper would fill the *remote* machine's clipboard,
    // so OSC 52 is the only thing that reaches the user. Two exceptions:
    // a Windows sshd session (`clip.exe` is what the user at that machine
    // wants, and conhost has no OSC 52), and Termux (its sshd is the
    // phone itself, and `termux-clipboard-set` fills the phone clipboard).
    let over_ssh = env_set("SSH_TTY") || env_set("SSH_CONNECTION");
    if !over_ssh || cfg!(windows) || env_set("TERMUX_VERSION") {
        for (program, args) in helpers() {
            match run_helper(program, args, text) {
                Ok(()) => return CopyOutcome::Tool(program),
                Err(error) if error.kind() == std::io::ErrorKind::NotFound => continue,
                Err(_) => continue,
            }
        }
    }
    match write_osc52(text) {
        Ok(()) => CopyOutcome::Osc52,
        Err(error) => CopyOutcome::Failed(error.to_string()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn messages_are_honest() {
        assert_eq!(CopyOutcome::Tool("wl-copy").message(), "copied (wl-copy)");
        assert!(CopyOutcome::Osc52.message().contains("press e"));
        assert!(CopyOutcome::Failed("x".into()).is_failure());
    }
}
