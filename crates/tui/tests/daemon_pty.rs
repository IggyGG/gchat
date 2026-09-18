#![cfg(unix)]

use gcoms::sdk::ipc::Capability;
use gcoms::sdk::EmbeddedClient;
use gcoms_node::node::{start, NodeConfig};
use portable_pty::{native_pty_system, CommandBuilder, PtySize};
use std::io::{Read, Write};
use std::path::Path;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

fn wait_for_path(path: &Path) {
    let deadline = Instant::now() + Duration::from_secs(20);
    while !path.exists() {
        assert!(Instant::now() < deadline, "path readiness timeout");
        std::thread::sleep(Duration::from_millis(20));
    }
}

/// The binary under test: cargo's build, or a prebuilt one from
/// `GHOST_TEST_BIN_DIR` (cross-compiled or release artifacts).
fn gchat_binary() -> std::path::PathBuf {
    match std::env::var_os("GHOST_TEST_BIN_DIR") {
        Some(dir) => Path::new(&dir).join("gchat"),
        None => env!("CARGO_BIN_EXE_gchat").into(),
    }
}

/// Drive the real binary through a PTY: wait for the passphrase prompt,
/// type `pass` (twice when creating), wait for the marker string that
/// proves the home screen rendered, quit, and return the raw stream.
fn drive_gchat(
    args: &[&std::ffi::OsStr],
    envs: &[(&str, &Path)],
    pass: &str,
    create: bool,
    ready: impl Fn() -> bool,
) -> String {
    let pair = native_pty_system()
        .openpty(PtySize {
            rows: 30,
            cols: 100,
            pixel_width: 0,
            pixel_height: 0,
        })
        .unwrap();
    let mut command = CommandBuilder::new(gchat_binary());
    command.arg("--legacy-ui");
    for arg in args {
        command.arg(arg);
    }
    for (name, value) in envs {
        command.env(name, value);
    }
    // Keep the host's own relay/catalog configuration out of the test.
    command.env_remove("GC_RELAY_BOOTSTRAP_URLS");
    command.env_remove("GC_CATALOG_URLS");
    command.env_remove("GC_CATALOG_CONFIG");
    let mut child = pair.slave.spawn_command(command).unwrap();
    drop(pair.slave);
    let mut reader = pair.master.try_clone_reader().unwrap();
    let output = Arc::new(Mutex::new(Vec::new()));
    let reader_output = output.clone();
    let reader_thread = std::thread::spawn(move || {
        let mut buffer = [0; 4096];
        while let Ok(read) = reader.read(&mut buffer) {
            if read == 0 {
                break;
            }
            reader_output
                .lock()
                .unwrap()
                .extend_from_slice(&buffer[..read]);
        }
    });
    let mut writer = pair.master.take_writer().unwrap();
    let prompt = b"passphrase:";
    let deadline = Instant::now() + Duration::from_secs(20);
    loop {
        if output
            .lock()
            .unwrap()
            .windows(prompt.len())
            .any(|window| window == prompt)
        {
            break;
        }
        assert!(Instant::now() < deadline, "gchat prompt timeout");
        std::thread::sleep(Duration::from_millis(20));
    }
    if create {
        writer
            .write_all(format!("{pass}\t{pass}\r").as_bytes())
            .unwrap();
    } else {
        writer.write_all(format!("{pass}\r").as_bytes()).unwrap();
    }
    writer.flush().unwrap();
    let deadline = Instant::now() + Duration::from_secs(60);
    while !ready() {
        assert!(
            Instant::now() < deadline,
            "readiness timeout: {:?}",
            String::from_utf8_lossy(&output.lock().unwrap())
        );
        std::thread::sleep(Duration::from_millis(20));
    }
    let deadline = Instant::now() + Duration::from_secs(60);
    loop {
        if output
            .lock()
            .unwrap()
            .windows(b"no joined or public channels".len())
            .any(|window| window == b"no joined or public channels")
        {
            break;
        }
        assert!(
            Instant::now() < deadline,
            "gchat unlock timeout: {:?}",
            String::from_utf8_lossy(&output.lock().unwrap())
        );
        std::thread::sleep(Duration::from_millis(20));
    }
    writer.write_all(b"q").unwrap();
    writer.flush().unwrap();
    let status = child.wait().unwrap();
    assert!(status.success());
    drop(writer);
    reader_thread.join().unwrap();
    let rendered = String::from_utf8_lossy(&output.lock().unwrap()).into_owned();
    rendered
}

fn run_gchat(socket: &Path, archive: &Path, create: bool) -> String {
    let args = [
        std::ffi::OsStr::new("--store"),
        archive.as_os_str(),
        std::ffi::OsStr::new("--daemon-socket"),
        socket.as_os_str(),
    ];
    drive_gchat(&args, &[], "archive-pass", create, || archive.exists())
}

#[cfg(unix)]
fn mode_of(path: &Path) -> u32 {
    use std::os::unix::fs::PermissionsExt;
    std::fs::metadata(path).unwrap().permissions().mode() & 0o777
}

/// Bare `gchat` with only GCHAT_HOME: creates the profile and archive in
/// the hosted runtime, restores the terminal, and reopens them.
#[test]
fn legacy_gchat_hosts_runtime_in_pty() {
    let temp = tempfile::tempdir().unwrap();
    let home = temp.path().join("gchat-home");
    let profile = home.join("profile.gcprotocol");
    let archive = home.join("chat.gcarchive");
    let envs = [("GCHAT_HOME", home.as_path())];
    let args = [std::ffi::OsStr::new("--no-relay")];

    let created = drive_gchat(&args, &envs, "pass-phrase-8", true, || {
        profile.exists() && archive.exists()
    });
    // ratatui positions the cursor between words, so match single words.
    assert!(created.contains("create") && created.contains("profile"));
    assert!(created.contains("NEW") && created.contains("identity"));
    assert!(
        created.contains("no joined or public channels"),
        "{created}"
    );
    assert!(created.contains("\x1b[?1049l"));
    assert!(created.contains("\x1b[?2004l"));
    assert!(created.contains("session saved"), "{created}");
    assert_eq!(mode_of(&home), 0o700);
    assert_eq!(mode_of(&profile), 0o600);
    assert_eq!(mode_of(&archive), 0o600);
    assert!(home.join("outbox").is_dir());
    assert_eq!(mode_of(&home.join("outbox")), 0o700);

    let reopened = drive_gchat(&args, &envs, "pass-phrase-8", false, || true);
    assert!(reopened.contains("unlock"), "{reopened}");
    assert!(
        reopened.contains("no joined or public channels"),
        "{reopened}"
    );
    assert!(reopened.contains("\x1b[?1049l"));
    assert!(reopened.contains("session saved"), "{reopened}");
}

/// The friends build must carry a relay bootstrap URL. A debug relink from
/// a shell without `GC_DEFAULT_RELAY_BOOTSTRAP` silently produces a binary
/// with no relay, which is exactly how the first phone test failed.
#[test]
fn friends_binary_has_a_compiled_in_relay_bootstrap() {
    if std::env::var_os("GC_DEFAULT_RELAY_BOOTSTRAP").is_none() {
        eprintln!("GC_DEFAULT_RELAY_BOOTSTRAP unset; skipping the compiled-in relay check");
        return;
    }
    let temp = tempfile::tempdir().unwrap();
    let home = temp.path().join("home");
    let output = std::process::Command::new(gchat_binary())
        .arg("paths")
        .env("GCHAT_HOME", &home)
        .env_remove("GC_RELAY_BOOTSTRAP_URLS")
        .output()
        .unwrap();
    let text = String::from_utf8_lossy(&output.stdout);
    let expected = std::env::var("GC_DEFAULT_RELAY_BOOTSTRAP").unwrap();
    assert!(
        text.lines()
            .any(|line| line.starts_with("relay") && line.contains(&expected)),
        "gchat paths did not report the compiled-in relay:\n{text}"
    );
}

/// Esc on the passphrase form exits cleanly without creating anything.
#[test]
fn legacy_esc_on_first_run_exits_without_a_profile() {
    let temp = tempfile::tempdir().unwrap();
    let home = temp.path().join("gchat-home");
    let pair = native_pty_system()
        .openpty(PtySize {
            rows: 24,
            cols: 80,
            pixel_width: 0,
            pixel_height: 0,
        })
        .unwrap();
    let mut command = CommandBuilder::new(gchat_binary());
    command.arg("--legacy-ui");
    command.arg("--no-relay");
    command.env("GCHAT_HOME", &home);
    command.env_remove("GC_RELAY_BOOTSTRAP_URLS");
    let mut child = pair.slave.spawn_command(command).unwrap();
    drop(pair.slave);
    let mut reader = pair.master.try_clone_reader().unwrap();
    let output = Arc::new(Mutex::new(Vec::new()));
    let reader_output = output.clone();
    let reader_thread = std::thread::spawn(move || {
        let mut buffer = [0; 4096];
        while let Ok(read) = reader.read(&mut buffer) {
            if read == 0 {
                break;
            }
            reader_output
                .lock()
                .unwrap()
                .extend_from_slice(&buffer[..read]);
        }
    });
    let mut writer = pair.master.take_writer().unwrap();
    let deadline = Instant::now() + Duration::from_secs(20);
    while !output
        .lock()
        .unwrap()
        .windows(b"passphrase:".len())
        .any(|window| window == b"passphrase:")
    {
        assert!(Instant::now() < deadline, "prompt timeout");
        std::thread::sleep(Duration::from_millis(20));
    }
    writer.write_all(b"\x1b").unwrap();
    writer.flush().unwrap();
    let status = child.wait().unwrap();
    assert!(status.success());
    drop(writer);
    reader_thread.join().unwrap();
    let rendered = String::from_utf8_lossy(&output.lock().unwrap()).into_owned();
    assert!(rendered.contains("nothing unlocked"), "{rendered}");
    assert!(!home.join("profile.gcprotocol").exists());
    assert!(rendered.contains("\x1b[?1049l"));
}

#[tokio::test(flavor = "multi_thread")]
async fn real_gchat_creates_and_reopens_a_daemon_archive_in_a_pty() {
    let temp = tempfile::tempdir().unwrap();
    let socket = temp.path().join("gcd.sock");
    let archive = temp.path().join("chat.gcarchive");
    let node = start(NodeConfig {
        seed: [0x51; 32],
        listen: "127.0.0.1:0".parse().unwrap(),
        control: None,
        advertise: None,
        inbox_relay: None,
        profile: gcoms_node::node::NodeProfile::fixture(),
        alias_lifecycle: Default::default(),
    })
    .await
    .unwrap();
    let server_node = node.clone();
    let server_socket = socket.clone();
    let server = tokio::spawn(async move {
        gcoms::sdk::serve_unix(
            server_socket,
            EmbeddedClient::new(server_node),
            vec![
                Capability::IdentityRead,
                Capability::DirectMessage,
                Capability::ChannelMember,
                Capability::ChannelAdmin,
                Capability::EventRead,
            ],
        )
        .await
    });
    wait_for_path(&socket);

    let created = run_gchat(&socket, &archive, true);
    assert!(created.contains("create") && created.contains("profile"));
    assert!(created.contains("no joined or public channels"));
    assert!(created.contains("\x1b[?1049l"));
    assert!(created.contains("\x1b[?2004l"));
    let reopened = run_gchat(&socket, &archive, false);
    assert!(reopened.contains("unlock"));
    assert!(reopened.contains("no joined or public channels"));
    assert!(reopened.contains("\x1b[?1049l"));
    assert!(reopened.contains("\x1b[?2004l"));

    server.abort();
    node.shutdown().await;
}
