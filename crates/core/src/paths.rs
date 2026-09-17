//! Default on-disk locations for the single-binary client.
//!
//! No directory crate: the rules are small and the platform set is fixed.
//! `GCHAT_HOME` (or `--home`) replaces every directory at once, which is how
//! tests and a second identity on one machine stay isolated.

use std::path::{Path, PathBuf};

const APP: &str = "gchat";

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AppPaths {
    pub data_dir: PathBuf,
    pub config_dir: PathBuf,
    pub runtime_dir: PathBuf,
    pub profile: PathBuf,
    pub archive: PathBuf,
    pub socket: PathBuf,
    pub outbox: PathBuf,
    pub passphrase_file: PathBuf,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Platform {
    /// Linux, BSDs, Termux, iSH: XDG with a data-dir fallback for the socket.
    Unix,
    MacOs,
    Windows,
}

impl Platform {
    pub fn current() -> Self {
        if cfg!(windows) {
            Platform::Windows
        } else if cfg!(target_os = "macos") {
            Platform::MacOs
        } else {
            Platform::Unix
        }
    }
}

/// Resolve the platform defaults from the real environment.
pub fn resolve(home: Option<&Path>) -> Result<AppPaths, String> {
    resolve_with(home, Platform::current(), &|name| std::env::var(name).ok())
}

/// Resolve against an explicit environment lookup (unit-testable on any host).
pub fn resolve_with(
    home: Option<&Path>,
    platform: Platform,
    env: &dyn Fn(&str) -> Option<String>,
) -> Result<AppPaths, String> {
    let env_path = |name: &str| {
        env(name)
            .filter(|value| !value.is_empty())
            .map(PathBuf::from)
    };
    let home_override = home
        .map(Path::to_path_buf)
        .or_else(|| env_path("GCHAT_HOME"));
    let (data, config, runtime) = match home_override {
        Some(dir) => (dir.clone(), dir.clone(), dir),
        None => match platform {
            Platform::Unix => {
                let home = env_path("HOME").ok_or("HOME is not set")?;
                let data = env_path("XDG_DATA_HOME")
                    .unwrap_or_else(|| home.join(".local").join("share"))
                    .join(APP);
                let config = env_path("XDG_CONFIG_HOME")
                    .unwrap_or_else(|| home.join(".config"))
                    .join(APP);
                // Termux and iSH have no runtime dir; a socket beside the
                // profile stays well under the sun_path limit.
                let runtime =
                    env_path("XDG_RUNTIME_DIR").map_or_else(|| data.clone(), |dir| dir.join(APP));
                (data, config, runtime)
            }
            Platform::MacOs => {
                let home = env_path("HOME").ok_or("HOME is not set")?;
                let data = home.join("Library").join("Application Support").join(APP);
                let runtime = env_path("TMPDIR").map_or_else(|| data.clone(), |dir| dir.join(APP));
                (data.clone(), data, runtime)
            }
            Platform::Windows => {
                let base = env_path("LOCALAPPDATA")
                    .ok_or("LOCALAPPDATA is not set")?
                    .join(APP);
                (base.clone(), base.clone(), base.join("runtime"))
            }
        },
    };
    Ok(AppPaths::from_dirs(data, config, runtime, platform))
}

impl AppPaths {
    fn from_dirs(
        data_dir: PathBuf,
        config_dir: PathBuf,
        runtime_dir: PathBuf,
        platform: Platform,
    ) -> Self {
        let socket = runtime_dir.join(if platform == Platform::Windows {
            "gcd.pipe"
        } else {
            "gcd.sock"
        });
        AppPaths {
            profile: data_dir.join("profile.gcprotocol"),
            archive: data_dir.join("chat.gcarchive"),
            outbox: data_dir.join("outbox"),
            passphrase_file: config_dir.join("passphrase"),
            socket,
            data_dir,
            config_dir,
            runtime_dir,
        }
    }

    /// Directories that must exist and be private before the client runs.
    pub fn private_dirs(&self) -> Vec<(&Path, &'static str)> {
        let mut dirs = vec![(self.data_dir.as_path(), "data directory")];
        if self.runtime_dir != self.data_dir {
            dirs.push((self.runtime_dir.as_path(), "runtime directory"));
        }
        dirs.push((self.outbox.as_path(), "outbox"));
        dirs
    }
}

/// Create `dir` (mode 0700) if missing, then require it to be private to the
/// current user. Failures carry the exact command that fixes them.
pub fn ensure_private_dir(dir: &Path, label: &str) -> Result<(), String> {
    if std::fs::symlink_metadata(dir).is_err() {
        std::fs::create_dir_all(dir)
            .map_err(|error| format!("create {label} {}: {error}", dir.display()))?;
        crate::private_fs::make_private(dir, true)?;
    }
    crate::private_fs::validate_private_dir(dir, label).map_err(|error| remediation(dir, &error))
}

/// Human remediation for a directory that is not private.
pub fn remediation(dir: &Path, error: &str) -> String {
    let shown = dir.display();
    if cfg!(windows) {
        format!(
            "{error}. {shown} must be private to you. Fix with:  icacls \"{shown}\" /setowner \"%USERNAME%\" && icacls \"{shown}\" /inheritance:r /grant:r \"%USERNAME%:(OI)(CI)F\"  then retry"
        )
    } else {
        format!(
            "{error}. {shown} must be private to you. Fix with:  chmod 700 \"{shown}\"  (and chmod 600 \"{shown}\"/*.gc*)  then retry"
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    fn env(pairs: &[(&str, &str)]) -> HashMap<String, String> {
        pairs
            .iter()
            .map(|(k, v)| (k.to_string(), v.to_string()))
            .collect()
    }

    fn resolve_env(platform: Platform, vars: &HashMap<String, String>) -> AppPaths {
        resolve_with(None, platform, &|name| vars.get(name).cloned()).unwrap()
    }

    #[test]
    fn xdg_defaults() {
        let vars = env(&[("HOME", "/home/u"), ("XDG_RUNTIME_DIR", "/run/user/1")]);
        let paths = resolve_env(Platform::Unix, &vars);
        assert_eq!(paths.data_dir, PathBuf::from("/home/u/.local/share/gchat"));
        assert_eq!(paths.config_dir, PathBuf::from("/home/u/.config/gchat"));
        assert_eq!(paths.socket, PathBuf::from("/run/user/1/gchat/gcd.sock"));
        assert_eq!(
            paths.profile,
            PathBuf::from("/home/u/.local/share/gchat/profile.gcprotocol")
        );
        assert_eq!(
            paths.archive,
            PathBuf::from("/home/u/.local/share/gchat/chat.gcarchive")
        );
        assert_eq!(
            paths.outbox,
            PathBuf::from("/home/u/.local/share/gchat/outbox")
        );
        assert_eq!(
            paths.passphrase_file,
            PathBuf::from("/home/u/.config/gchat/passphrase")
        );
        let vars = env(&[("HOME", "/home/u"), ("XDG_DATA_HOME", "/data")]);
        assert_eq!(
            resolve_env(Platform::Unix, &vars).data_dir,
            PathBuf::from("/data/gchat")
        );
    }

    #[test]
    fn no_runtime_dir_falls_back_to_data_dir() {
        let vars = env(&[("HOME", "/data/data/com.termux/files/home")]);
        let paths = resolve_env(Platform::Unix, &vars);
        assert_eq!(paths.runtime_dir, paths.data_dir);
        assert_eq!(paths.socket, paths.data_dir.join("gcd.sock"));
        assert!(paths.socket.as_os_str().len() < 100, "{:?}", paths.socket);
        assert_eq!(paths.private_dirs().len(), 2);
    }

    #[test]
    fn home_override() {
        let flag = resolve_with(Some(Path::new("/tmp/one")), Platform::Unix, &|_| None).unwrap();
        assert_eq!(flag.data_dir, PathBuf::from("/tmp/one"));
        assert_eq!(flag.socket, PathBuf::from("/tmp/one/gcd.sock"));
        assert_eq!(flag.passphrase_file, PathBuf::from("/tmp/one/passphrase"));
        let vars = env(&[("GCHAT_HOME", "/tmp/two"), ("HOME", "/home/u")]);
        let env_var = resolve_env(Platform::Unix, &vars);
        assert_eq!(env_var.data_dir, PathBuf::from("/tmp/two"));
        assert_eq!(env_var.runtime_dir, PathBuf::from("/tmp/two"));
        let both = resolve_with(Some(Path::new("/tmp/one")), Platform::Unix, &|name| {
            vars.get(name).cloned()
        })
        .unwrap();
        assert_eq!(both.data_dir, PathBuf::from("/tmp/one"), "flag beats env");
    }

    #[test]
    fn macos_and_windows_layouts() {
        let vars = env(&[("HOME", "/Users/u"), ("TMPDIR", "/var/folders/ab/T")]);
        let mac = resolve_env(Platform::MacOs, &vars);
        assert_eq!(
            mac.data_dir,
            PathBuf::from("/Users/u/Library/Application Support/gchat")
        );
        assert_eq!(
            mac.socket,
            PathBuf::from("/var/folders/ab/T/gchat/gcd.sock")
        );
        let vars = env(&[("LOCALAPPDATA", "/Users/u/AppData/Local")]);
        let win = resolve_env(Platform::Windows, &vars);
        assert_eq!(win.data_dir, PathBuf::from("/Users/u/AppData/Local/gchat"));
        assert_eq!(
            win.socket,
            PathBuf::from("/Users/u/AppData/Local/gchat/runtime/gcd.pipe")
        );
        assert!(resolve_with(None, Platform::Windows, &|_| None).is_err());
        assert!(resolve_with(None, Platform::Unix, &|_| None).is_err());
    }

    #[test]
    fn remediation_message_names_the_fix() {
        let message = remediation(Path::new("/home/u/.local/share/gchat"), "mode 0755");
        assert!(message.starts_with("mode 0755. "));
        if cfg!(windows) {
            assert!(message.contains("icacls"));
        } else {
            assert!(message.contains("chmod 700 \"/home/u/.local/share/gchat\""));
        }
    }

    #[cfg(unix)]
    #[test]
    fn ensure_private_dir_creates_0700_and_rejects_shared() {
        use std::os::unix::fs::PermissionsExt;

        let temp = tempfile::tempdir().unwrap();
        let fresh = temp.path().join("fresh").join("nested");
        ensure_private_dir(&fresh, "data directory").unwrap();
        let mode = std::fs::metadata(&fresh).unwrap().permissions().mode() & 0o777;
        assert_eq!(mode, 0o700);
        ensure_private_dir(&fresh, "data directory").unwrap();
        let shared = temp.path().join("shared");
        std::fs::create_dir(&shared).unwrap();
        std::fs::set_permissions(&shared, std::fs::Permissions::from_mode(0o755)).unwrap();
        let error = ensure_private_dir(&shared, "data directory").unwrap_err();
        assert!(error.contains("chmod 700"), "{error}");
    }
}
