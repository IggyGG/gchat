//! Native attachment driver for isolated fleet qualification. JSON on stdin/stdout;
//! file bytes stay on the host and cross the ordinary owner-authenticated IPC.
use gchat_api::{ChatClient, Request};
use rand::{rngs::StdRng, RngCore, SeedableRng};
use serde::Deserialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    io::{Read, Write},
    path::{Path, PathBuf},
    time::Instant,
};
#[cfg(unix)]
use tokio::io::{AsyncReadExt, AsyncWriteExt};

#[derive(Deserialize)]
#[serde(tag = "action", rename_all = "snake_case", deny_unknown_fields)]
enum Action {
    Request {
        request: Request,
    },
    Generate {
        name: String,
        size: u64,
        seed: u64,
    },
    Import {
        id: String,
        conversation: String,
        name: String,
    },
    PartialImport {
        id: String,
        conversation: String,
        name: String,
    },
    Export {
        id: String,
        name: String,
        size: u64,
        sha256: String,
    },
    Verify {
        name: String,
        size: u64,
        sha256: String,
    },
}

fn path(root: &Path, name: &str) -> Result<PathBuf, String> {
    if name.is_empty()
        || name.len() > 255
        || name == "."
        || name == ".."
        || name.contains(['/', '\\', '\0'])
    {
        return Err("file name must be one ordinary path component".into());
    }
    Ok(root.join(name))
}

fn digest(path: &Path) -> Result<(u64, String), String> {
    let mut file = std::fs::File::open(path).map_err(|e| e.to_string())?;
    let mut hash = Sha256::new();
    let mut size = 0;
    let mut buffer = [0; 65536];
    loop {
        let n = file.read(&mut buffer).map_err(|e| e.to_string())?;
        if n == 0 {
            break;
        }
        hash.update(&buffer[..n]);
        size += n as u64;
    }
    Ok((size, format!("{:x}", hash.finalize())))
}

fn verify(path: &Path, size: u64, sha256: &str) -> Result<Value, String> {
    let (actual_size, actual_sha256) = digest(path)?;
    if actual_size != size || actual_sha256 != sha256 {
        return Err(format!(
            "export mismatch: size={actual_size}, sha256={actual_sha256}"
        ));
    }
    Ok(json!({"size": actual_size, "sha256": actual_sha256, "verified": true}))
}

async fn run(endpoint: &Path, root: &Path, action: Action) -> Result<Value, String> {
    if let Action::Generate { name, size, seed } = action {
        if size > 10 * 1024 * 1024 * 1024 {
            return Err("fixture exceeds file limit".into());
        }
        let mut file = std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(path(root, &name)?)
            .map_err(|e| e.to_string())?;
        let mut rng = StdRng::seed_from_u64(seed);
        let mut buffer = [0; 65536];
        let mut hash = Sha256::new();
        let mut left = size;
        while left > 0 {
            let n = left.min(buffer.len() as u64) as usize;
            rng.fill_bytes(&mut buffer[..n]);
            hash.update(&buffer[..n]);
            file.write_all(&buffer[..n]).map_err(|e| e.to_string())?;
            left -= n as u64;
        }
        file.sync_all().map_err(|e| e.to_string())?;
        return Ok(json!({"size": size, "sha256": format!("{:x}", hash.finalize())}));
    }
    if let Action::Verify { name, size, sha256 } = action {
        return verify(&path(root, &name)?, size, &sha256);
    }
    let client = ChatClient::connect(endpoint, None).await?;
    match action {
        Action::Request { request } => {
            let detail_request = match &request {
                Request::Submit { .. } => Some(request.clone()),
                _ => None,
            };
            let result = match client.request_typed(request).await {
                Ok(result) => result,
                Err(error) => {
                    // The typed journal deliberately returns OutcomeUnknown without
                    // its original service error. The compatibility API returns the
                    // retained response for this SAME admitted operation identifier;
                    // it never starts a new submission or changes the verdict.
                    if error.code == "outcome_unknown" {
                        if let Some(request) = detail_request {
                            if let Err(detail) = client.request_v2(request).await {
                                return Err(format!("{error}; retained detail: {detail}"));
                            }
                        }
                    }
                    return Err(error.to_string());
                }
            };
            if let gchat_api::Response::Error { code, message } = result {
                return Err(format!("{code}: {message}"));
            }
            serde_json::to_value(result).map_err(|e| e.to_string())
        }
        Action::Import {
            id,
            conversation,
            name,
        } => {
            client
                .import_file(&id, &conversation, &path(root, &name)?)
                .await?;
            Ok(json!({"imported": true}))
        }
        Action::PartialImport {
            id,
            conversation,
            name,
        } => {
            let source = path(root, &name)?;
            let size = source.metadata().map_err(|e| e.to_string())?.len();
            client
                .files(gchat_api::FileRequest::Prepare {
                    id: id.clone(),
                    conversation,
                    name,
                    size_bytes: size.to_string(),
                })
                .await?;
            let mut data = Vec::new();
            std::fs::File::open(source)
                .map_err(|e| e.to_string())?
                .take(gchat_api::files::PIECE_BYTES as u64)
                .read_to_end(&mut data)
                .map_err(|e| e.to_string())?;
            client
                .file_io(gchat_api::files::encode_io(
                    &gchat_api::files::FileIo {
                        instance: client.instance_id().into(),
                        id,
                        piece: 0,
                        upload: true,
                    },
                    &data,
                )?)
                .await?;
            Ok(json!({"retained_bytes": data.len()}))
        }
        Action::Export {
            id,
            name,
            size,
            sha256,
        } => {
            let output = path(root, &name)?;
            client.save_file(&id, &output).await?;
            verify(&output, size, &sha256)
        }
        Action::Generate { .. } | Action::Verify { .. } => unreachable!(),
    }
}

#[tokio::main(flavor = "multi_thread", worker_threads = 2)]
async fn main() {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    #[cfg(unix)]
    if args.len() == 4 && args[0] == "--serve" {
        if let Err(error) = serve(
            Path::new(&args[1]),
            Path::new(&args[2]),
            Path::new(&args[3]),
        )
        .await
        {
            eprintln!("fleet probe: {error}");
            std::process::exit(1);
        }
        return;
    }
    let started = Instant::now();
    let result = async {
        if args.len() != 2 {
            return Err("usage: fleet_probe <owner-endpoint> <fixture-directory>".into());
        }
        let mut input = Vec::new();
        std::io::stdin()
            .take(65537)
            .read_to_end(&mut input)
            .map_err(|e| e.to_string())?;
        if input.len() > 65536 {
            return Err("request exceeds bound".into());
        }
        let action = serde_json::from_slice(&input).map_err(|e| format!("invalid request: {e}"))?;
        run(Path::new(&args[0]), Path::new(&args[1]), action).await
    }
    .await;
    let ok = result.is_ok();
    let output = match result {
        Ok(value) => {
            json!({"ok": true, "elapsed_ms": started.elapsed().as_millis(), "value": value})
        }
        Err(error) => {
            json!({"ok": false, "elapsed_ms": started.elapsed().as_millis(), "error": error})
        }
    };
    println!("{output}");
    if !ok {
        std::process::exit(1);
    }
}

#[cfg(unix)]
async fn serve(endpoint: &Path, root: &Path, socket: &Path) -> Result<(), String> {
    use std::os::unix::fs::PermissionsExt;
    let listener = tokio::net::UnixListener::bind(socket).map_err(|e| e.to_string())?;
    std::fs::set_permissions(socket, std::fs::Permissions::from_mode(0o600))
        .map_err(|e| e.to_string())?;
    let slots = std::sync::Arc::new(tokio::sync::Semaphore::new(16));
    let mut tasks = tokio::task::JoinSet::new();
    loop {
        let permit = slots
            .clone()
            .acquire_owned()
            .await
            .map_err(|e| e.to_string())?;
        let (mut stream, _) = listener.accept().await.map_err(|e| e.to_string())?;
        let endpoint = endpoint.to_path_buf();
        let root = root.to_path_buf();
        while tasks.try_join_next().is_some() {}
        tasks.spawn(async move {
            let _permit = permit;
            let started = Instant::now();
            let result = tokio::time::timeout(std::time::Duration::from_secs(900), async {
                let size = stream.read_u32().await.map_err(|e| e.to_string())? as usize;
                if size > 65536 {
                    return Err("request exceeds bound".to_string());
                }
                let mut data = vec![0; size];
                stream
                    .read_exact(&mut data)
                    .await
                    .map_err(|e| e.to_string())?;
                let action = serde_json::from_slice(&data).map_err(|e| e.to_string())?;
                run(&endpoint, &root, action).await
            })
            .await
            .unwrap_or_else(|_| Err("probe deadline exceeded".into()));
            let output = match result {
                Ok(value) => {
                    json!({"ok":true,"elapsed_ms":started.elapsed().as_millis(),"value":value})
                }
                Err(error) => {
                    json!({"ok":false,"elapsed_ms":started.elapsed().as_millis(),"error":error})
                }
            };
            let bytes = serde_json::to_vec(&output).unwrap();
            if bytes.len() <= 1024 * 1024 {
                let _ = stream.write_u32(bytes.len() as u32).await;
                let _ = stream.write_all(&bytes).await;
            }
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn verification_requires_bytes_not_completion_claims() {
        let dir = tempfile::tempdir().unwrap();
        let file = dir.path().join("file");
        std::fs::write(&file, b"actual").unwrap();
        let (_, hash) = digest(&file).unwrap();
        assert!(verify(&file, 6, &hash).is_ok());
        assert!(verify(&file, 5, &hash).is_err());
        assert!(verify(&file, 6, &"0".repeat(64)).is_err());
        for name in ["../other", "/absolute", "a/b", "a\\b", ".."] {
            assert!(path(dir.path(), name).is_err());
        }
    }
}
