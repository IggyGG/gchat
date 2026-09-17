#![cfg(unix)]
use gchat_api::{ChatClient, Request, Response};
use portable_pty::{native_pty_system, CommandBuilder, PtySize};
use std::{
    io::{Read, Write},
    sync::{Arc, Mutex},
    time::Duration,
};
use tokio::io::{AsyncReadExt, AsyncWriteExt};

#[tokio::test(flavor = "multi_thread")]
async fn real_tui_and_second_ui_share_one_live_instance_after_tui_closes() {
    let home = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(home.path(), true).unwrap();
    let mut daemon = std::process::Command::new(env!("CARGO_BIN_EXE_gchat"))
        .args([
            "daemon",
            "--interactive",
            "--local-fixture",
            "--listen",
            "127.0.0.1:0",
            "--home",
        ])
        .arg(home.path())
        .env_remove("GC_RELAY_BOOTSTRAP_URLS")
        .env_remove("GCHAT_HOME")
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn()
        .unwrap();
    struct Stop(std::process::Child);
    impl Drop for Stop {
        fn drop(&mut self) {
            let _ = self.0.kill();
            let _ = self.0.wait();
        }
    }
    let endpoint = home.path().join("gcd.chat");
    let deadline = tokio::time::Instant::now() + Duration::from_secs(10);
    let client = loop {
        if let Ok(client) = ChatClient::connect(&endpoint, None).await {
            break client;
        }
        assert!(
            daemon.try_wait().unwrap().is_none(),
            "selected daemon stopped"
        );
        assert!(
            tokio::time::Instant::now() < deadline,
            "selected daemon startup"
        );
        tokio::time::sleep(Duration::from_millis(20)).await;
    };
    let _daemon = Stop(daemon);
    client
        .request(Request::Unlock {
            passphrase: "pty-shared-passphrase".into(),
            create: true,
        })
        .await
        .unwrap();
    // Forward both protocol endpoints and drop one typed admission reply. F2
    // must read the original operation's status without another submission.
    let proxy_path = home.path().join("ui.chat");
    let listener = tokio::net::UnixListener::bind(&proxy_path).unwrap();
    gchat_core::private_fs::make_private(&proxy_path, false).unwrap();
    let rpc_path = gchat_api::rpc::endpoint_for(&proxy_path);
    let rpc_listener = tokio::net::UnixListener::bind(&rpc_path).unwrap();
    gchat_core::private_fs::make_private(&rpc_path, false).unwrap();
    let operation_ids = Arc::new(Mutex::new(Vec::new()));
    let status_ids = Arc::new(Mutex::new(Vec::new()));
    let mut proxies = Vec::new();
    for (listener, target, typed) in [
        (listener, endpoint.clone(), false),
        (rpc_listener, gchat_api::rpc::endpoint_for(&endpoint), true),
    ] {
        let seen = operation_ids.clone();
        let statuses = status_ids.clone();
        proxies.push(tokio::spawn(async move {
            while let Ok((mut incoming, _)) = listener.accept().await {
                let target = target.clone();
                let seen = seen.clone();
                let statuses = statuses.clone();
                tokio::spawn(async move {
                    let length = incoming.read_u32().await.unwrap() as usize;
                    assert!(length <= gchat_api::MAX_FRAME_BYTES);
                    let mut body = vec![0; length];
                    incoming.read_exact(&mut body).await.unwrap();
                    let envelope: serde_json::Value = serde_json::from_slice(&body).unwrap();
                    let drop_reply = if typed && envelope["method"] == "submit" {
                        let invocation = &envelope["invocation"];
                        if invocation["action"] == "status" {
                            statuses
                                .lock()
                                .unwrap()
                                .push(invocation["operation_id"].as_str().unwrap().to_owned());
                        }
                        if invocation["action"] == "call"
                            && invocation["args"]["text"] == "exact text from TUI"
                        {
                            let mut seen = seen.lock().unwrap();
                            seen.push(invocation["operation"]["id"].as_str().unwrap().to_owned());
                            seen.len() == 1
                        } else {
                            false
                        }
                    } else {
                        false
                    };
                    let mut upstream = tokio::net::UnixStream::connect(target).await.unwrap();
                    upstream.write_u32(length as u32).await.unwrap();
                    upstream.write_all(&body).await.unwrap();
                    let length = upstream.read_u32().await.unwrap() as usize;
                    assert!(length <= gchat_api::MAX_FRAME_BYTES);
                    let mut reply = vec![0; length];
                    upstream.read_exact(&mut reply).await.unwrap();
                    if !drop_reply {
                        let _ = incoming.write_u32(length as u32).await;
                        let _ = incoming.write_all(&reply).await;
                    }
                });
            }
        }));
    }
    let pair = native_pty_system()
        .openpty(PtySize {
            rows: 30,
            cols: 100,
            pixel_width: 0,
            pixel_height: 0,
        })
        .unwrap();
    let mut command = CommandBuilder::new(env!("CARGO_BIN_EXE_gchat"));
    command.arg("--chat-socket");
    command.arg(&proxy_path);
    let mut child = pair.slave.spawn_command(command).unwrap();
    drop(pair.slave);
    let output = Arc::new(Mutex::new(Vec::new()));
    let mut reader = pair.master.try_clone_reader().unwrap();
    let collected = output.clone();
    let reader = std::thread::spawn(move || {
        let mut bytes = [0; 4096];
        while let Ok(count) = reader.read(&mut bytes) {
            if count == 0 {
                break;
            }
            collected.lock().unwrap().extend_from_slice(&bytes[..count]);
        }
    });
    let mut writer = pair.master.take_writer().unwrap();
    // Sending before the first frame can put the command into cooked terminal
    // input before the UI enters raw mode. Observe readiness, as in the service
    // lifetime test below, instead of assuming a fixed startup duration.
    let deadline = tokio::time::Instant::now() + Duration::from_secs(15);
    while !String::from_utf8_lossy(&output.lock().unwrap()).contains("Ctrl+Q") {
        assert!(
            child.try_wait().unwrap().is_none(),
            "TUI stopped before rendering its input: {}",
            String::from_utf8_lossy(&output.lock().unwrap())
        );
        assert!(
            tokio::time::Instant::now() < deadline,
            "terminal ready: {}",
            String::from_utf8_lossy(&output.lock().unwrap())
        );
        tokio::time::sleep(Duration::from_millis(25)).await;
    }
    writer.write_all(b"/create #shared participant\r").unwrap();
    writer.flush().unwrap();
    let deadline = tokio::time::Instant::now() + Duration::from_secs(15);
    let channel = loop {
        if let Response::Snapshot { snapshot } = client.request(Request::Snapshot).await.unwrap() {
            if let Some(channel) = snapshot.conversations.first() {
                break channel.id.clone();
            }
        }
        assert!(
            tokio::time::Instant::now() < deadline,
            "TUI create command did not reach shared service: {}",
            String::from_utf8_lossy(&output.lock().unwrap()).into_owned()
        );
        tokio::time::sleep(Duration::from_millis(50)).await;
    };
    tokio::time::sleep(Duration::from_millis(250)).await;
    writer.write_all(b"exact text from TUI\r").unwrap();
    writer.flush().unwrap();
    let deadline = tokio::time::Instant::now() + Duration::from_secs(10);
    loop {
        if let Response::History { page } = client
            .request(Request::History {
                conversation: channel.clone(),
                before: None,
                limit: 20,
            })
            .await
            .unwrap()
        {
            if page
                .messages
                .iter()
                .any(|m| m.body == "exact text from TUI")
            {
                break;
            }
        }
        assert!(
            tokio::time::Instant::now() < deadline,
            "TUI message did not reach shared archive"
        );
        tokio::time::sleep(Duration::from_millis(50)).await;
    }
    let deadline = tokio::time::Instant::now() + Duration::from_secs(5);
    while !String::from_utf8_lossy(&output.lock().unwrap()).contains("F2") {
        assert!(
            tokio::time::Instant::now() < deadline,
            "missing retained request notice"
        );
        tokio::time::sleep(Duration::from_millis(25)).await;
    }
    let submitted_id = operation_ids.lock().unwrap()[0].clone();
    assert!(!status_ids.lock().unwrap().contains(&submitted_id));
    writer.write_all(b"\x1bOQ").unwrap(); // xterm F2
    writer.flush().unwrap();
    let deadline = tokio::time::Instant::now() + Duration::from_secs(5);
    while !status_ids.lock().unwrap().contains(&submitted_id) {
        assert!(
            tokio::time::Instant::now() < deadline,
            "F2 did not check the original operation"
        );
        tokio::time::sleep(Duration::from_millis(25)).await;
    }
    {
        let ids = operation_ids.lock().unwrap();
        assert_eq!(&*ids, &[submitted_id], "F2 resubmitted an operation");
    }
    let Response::History { page } = client
        .request(Request::History {
            conversation: channel,
            before: None,
            limit: 20,
        })
        .await
        .unwrap()
    else {
        panic!()
    };
    assert_eq!(
        page.messages
            .iter()
            .filter(|m| m.body == "exact text from TUI")
            .count(),
        1
    );
    writer.write_all(&[17]).unwrap();
    writer.flush().unwrap();
    let deadline = tokio::time::Instant::now() + Duration::from_secs(5);
    while child.try_wait().unwrap().is_none() {
        assert!(tokio::time::Instant::now() < deadline);
        tokio::time::sleep(Duration::from_millis(20)).await;
    }
    reader.join().unwrap();
    assert!(
        matches!(client.request(Request::Snapshot).await.unwrap(), Response::Snapshot { snapshot } if !snapshot.instance.locked)
    );
    assert!(String::from_utf8_lossy(&output.lock().unwrap()).contains("shared"));
    client.request(Request::Disconnect).await.unwrap();
    for proxy in proxies {
        proxy.abort();
    }
}

#[tokio::test(flavor = "multi_thread")]
async fn automatically_started_instance_survives_its_terminal_session() {
    let home = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(home.path(), true).unwrap();
    let pair = native_pty_system()
        .openpty(PtySize {
            rows: 24,
            cols: 100,
            pixel_width: 0,
            pixel_height: 0,
        })
        .unwrap();
    let mut command = CommandBuilder::new(env!("CARGO_BIN_EXE_gchat"));
    command.arg("--home");
    command.arg(home.path());
    command.arg("--listen");
    command.arg("127.0.0.1:0");
    command.env("TERM", "xterm-256color");
    command.env_remove("GC_RELAY_BOOTSTRAP_URLS");
    command.env_remove("GCHAT_HOME");
    struct Stop {
        ui: Box<dyn portable_pty::Child + Send + Sync>,
        daemon: Option<u32>,
    }
    impl Drop for Stop {
        fn drop(&mut self) {
            let _ = self.ui.kill();
            if let Some(pid) = self.daemon {
                let _ = std::process::Command::new("kill")
                    .args(["-TERM", &pid.to_string()])
                    .stdout(std::process::Stdio::null())
                    .stderr(std::process::Stdio::null())
                    .status();
            }
        }
    }
    let mut processes = Stop {
        ui: pair.slave.spawn_command(command).unwrap(),
        daemon: None,
    };
    let ui_pid = processes.ui.process_id().unwrap();
    drop(pair.slave);
    let mut reader = pair.master.try_clone_reader().unwrap();
    let output = Arc::new(Mutex::new(Vec::new()));
    let collected = output.clone();
    let reading = std::thread::spawn(move || {
        let mut bytes = [0; 4096];
        while let Ok(count) = reader.read(&mut bytes) {
            if count == 0 {
                break;
            }
            let mut out = collected.lock().unwrap();
            if out.len() < 65536 {
                out.extend_from_slice(&bytes[..count]);
            }
        }
    });
    let endpoint = home.path().join("gcd.chat");
    let deadline = tokio::time::Instant::now() + Duration::from_secs(15);
    let client = loop {
        // Record only this TUI's own child for cleanup, on Linux and macOS.
        let output = std::process::Command::new("ps")
            .args(["-axo", "pid=,ppid=,comm="])
            .output()
            .unwrap();
        for row in String::from_utf8_lossy(&output.stdout).lines() {
            let mut fields = row.split_whitespace();
            let pid = fields.next().and_then(|v| v.parse::<u32>().ok());
            let parent = fields.next().and_then(|v| v.parse::<u32>().ok());
            if parent == Some(ui_pid) {
                processes.daemon = pid;
            }
        }
        if let (Some(_), Ok(client)) =
            (processes.daemon, ChatClient::connect(&endpoint, None).await)
        {
            break client;
        }
        assert!(
            tokio::time::Instant::now() < deadline,
            "automatic service startup"
        );
        tokio::time::sleep(Duration::from_millis(50)).await;
    };
    assert!(processes.daemon.is_some(), "tracked spawned service");
    client
        .request(Request::Unlock {
            passphrase: "terminal-lifetime-fixture".into(),
            create: true,
        })
        .await
        .unwrap();
    // The service can answer before the terminal has entered raw mode. Wait
    // for its first frame so Ctrl+Q is not consumed by terminal flow control.
    let deadline = tokio::time::Instant::now() + Duration::from_secs(15);
    while !String::from_utf8_lossy(&output.lock().unwrap()).contains("Ctrl+Q") {
        assert!(
            tokio::time::Instant::now() < deadline,
            "terminal ready: {}",
            String::from_utf8_lossy(&output.lock().unwrap())
        );
        tokio::time::sleep(Duration::from_millis(25)).await;
    }
    let mut writer = pair.master.take_writer().unwrap();
    writer.write_all(b"\x11").unwrap();
    writer.flush().unwrap();
    let deadline = tokio::time::Instant::now() + Duration::from_secs(5);
    while processes.ui.try_wait().unwrap().is_none() {
        assert!(
            tokio::time::Instant::now() < deadline,
            "TUI closes on Ctrl+Q"
        );
        tokio::time::sleep(Duration::from_millis(25)).await;
    }
    drop(writer);
    drop(pair.master);
    reading.join().unwrap();
    tokio::time::sleep(Duration::from_millis(200)).await;
    let Response::Snapshot { snapshot } = client
        .request(Request::Snapshot)
        .await
        .expect("closing the terminal must leave the same service available")
    else {
        panic!("snapshot")
    };
    assert!(!snapshot.instance.locked);
    assert!(!snapshot.instance.protocol_locked);
}
