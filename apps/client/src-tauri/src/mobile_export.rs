//! User-selected mobile document export. Only verified, complete cache contents
//! reach the picker; neither JSON requests nor file names select filesystem paths.

const PIECE_BYTES: u64 = 256 * 1024;

fn network_id(id: &str) -> Result<Option<&str>, String> {
    let hexadecimal = |value: &str, size| {
        value.len() == size && value.bytes().all(|byte| byte.is_ascii_hexdigit())
    };
    match id.split_once(':') {
        Some((network, file)) if hexadecimal(network, 64) && hexadecimal(file, 32) => {
            Ok(Some(network))
        }
        None if hexadecimal(id, 32) => Ok(None),
        _ => Err("Invalid network file handle".into()),
    }
}

fn validate_name(name: &str) -> Result<(), String> {
    if name.is_empty()
        || matches!(name, "." | "..")
        || name.len() > 255
        || name
            .chars()
            .any(|c| c.is_control() || matches!(c, '/' | '\\' | ':'))
        || name.ends_with(['.', ' '])
    {
        return Err("Invalid export name".into());
    }
    Ok(())
}

fn validated_size(size: &str, verified: &str) -> Result<u64, String> {
    let parse = |value: &str| {
        if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
            return Err("Invalid exported file size".to_string());
        }
        value
            .parse::<u64>()
            .map_err(|_| "Invalid exported file size".to_string())
    };
    let size = parse(size)?;
    if size != parse(verified)? || size > (u64::from(u32::MAX) + 1) * PIECE_BYTES {
        return Err("File is not completely verified or exceeds piece addressing bounds".into());
    }
    Ok(size)
}

fn piece_size(total: u64, offset: u64) -> Result<(u32, usize), String> {
    if offset >= total || !offset.is_multiple_of(PIECE_BYTES) {
        return Err("Invalid export piece offset".into());
    }
    let index = u32::try_from(offset / PIECE_BYTES).map_err(|_| "Export piece index overflow")?;
    Ok((index, (total - offset).min(PIECE_BYTES) as usize))
}

#[cfg(any(target_os = "android", target_os = "ios"))]
mod native {
    use super::*;
    use gchat_api::{
        files::{encode_io, FileIo},
        FileInfo, FileRequest, FileState, NetworkRequest, NetworkResponse, Request,
        RequestEnvelope, Response, VERSION,
    };
    use gchat_core::chat_service::{host::InstanceHost, ChatEndpoint};
    use std::{
        io::{Read, Seek, SeekFrom, Write},
        sync::Arc,
    };
    use tauri::Manager;
    use tauri_plugin_dialog::DialogExt;
    use tauri_plugin_fs::{FilePath, FsExt, OpenOptions};
    use tokio::io::AsyncWriteExt;

    async fn completed_file(host: &InstanceHost, id: &str) -> Result<FileInfo, String> {
        let network = network_id(id)?;
        let request = Request::Files {
            request: FileRequest::List { conversation: None },
        };
        let response = host
            .dispatch(RequestEnvelope {
                version: VERSION,
                instance_id: Some(host.instance_id().into()),
                request: if let Some(network) = network {
                    Request::Networks {
                        request: NetworkRequest::Call {
                            network: network.into(),
                            request: Box::new(request),
                        },
                    }
                } else {
                    request
                },
            })
            .await
            .response;
        let response = match (network, response) {
            (
                Some(expected),
                Response::Networks {
                    response: NetworkResponse::Result { network, response },
                },
            ) if network == expected => *response,
            (None, response) => response,
            (_, Response::Error { message, .. }) => return Err(message),
            _ => return Err("File response belongs to another network".into()),
        };
        let snapshot = match response {
            Response::Files { snapshot } => snapshot,
            Response::Error { message, .. } => return Err(message),
            _ => return Err("Invalid file response".into()),
        };
        let file_id = id.rsplit(':').next().unwrap_or(id);
        let mut info = snapshot
            .files
            .into_iter()
            .find(|file| file.id == file_id && matches!(file.state, FileState::Complete))
            .ok_or("File is not complete")?;
        validate_name(&info.name)?;
        validated_size(&info.size_bytes, &info.verified_bytes)?;
        info.id = id.into();
        Ok(info)
    }

    async fn stage(
        app: &tauri::AppHandle,
        host: Arc<InstanceHost>,
        info: &FileInfo,
    ) -> Result<tempfile::NamedTempFile, String> {
        let directory = app
            .path()
            .app_cache_dir()
            .map_err(|e| e.to_string())?
            .join("private-exports");
        gchat_core::paths::ensure_private_dir(&directory, "private export staging")?;
        let staged = tempfile::NamedTempFile::new_in(directory).map_err(|e| e.to_string())?;
        let mut output = tokio::fs::File::from_std(staged.reopen().map_err(|e| e.to_string())?);
        let size = validated_size(&info.size_bytes, &info.verified_bytes)?;
        let mut offset = 0;
        while offset < size {
            let (piece, expected) = piece_size(size, offset)?;
            let bytes = host
                .clone()
                .file_io(encode_io(
                    &FileIo {
                        instance: host.instance_id().into(),
                        id: info.id.clone(),
                        piece,
                        upload: false,
                    },
                    &[],
                )?)
                .await?;
            if bytes.len() != expected {
                return Err("Invalid exported piece length".into());
            }
            output.write_all(&bytes).await.map_err(|e| e.to_string())?;
            offset += bytes.len() as u64;
        }
        output.flush().await.map_err(|e| e.to_string())?;
        output.sync_all().await.map_err(|e| e.to_string())?;
        drop(output);
        Ok(staged)
    }

    /// The iOS save dialog first exports Documents/<name>, before returning its
    /// selected URL. Supply our full staged bytes instead of an empty placeholder
    /// or an unrelated existing document. Never overwrite that source location.
    #[cfg(target_os = "ios")]
    struct DialogSource {
        path: std::path::PathBuf,
        identity: (u64, u64),
        remove: bool,
    }
    #[cfg(target_os = "ios")]
    impl DialogSource {
        fn prepare(
            app: &tauri::AppHandle,
            name: &str,
            mut input: std::fs::File,
        ) -> Result<Self, String> {
            use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
            let directory = app.path().document_dir().map_err(|e| e.to_string())?;
            std::fs::create_dir_all(&directory).map_err(|e| e.to_string())?;
            let path = directory.join(name);
            let mut output = std::fs::OpenOptions::new().write(true).create_new(true).mode(0o600)
                .open(&path).map_err(|e| format!("Cannot reserve temporary export document; existing files were preserved: {e}"))?;
            let metadata = match output.metadata() {
                Ok(metadata) => metadata,
                Err(error) => {
                    drop(output);
                    let _ = std::fs::remove_file(&path);
                    return Err(error.to_string());
                }
            };
            let owned = Self {
                path,
                identity: (metadata.dev(), metadata.ino()),
                remove: true,
            };
            std::io::copy(&mut input, &mut output).map_err(|e| e.to_string())?;
            output.sync_all().map_err(|e| e.to_string())?;
            Ok(owned)
        }
        fn retain_if_selected(&mut self, selected: &FilePath) {
            if let Ok(path) = selected.clone().into_path() {
                if let (Ok(a), Ok(b)) = (path.canonicalize(), self.path.canonicalize()) {
                    // The user explicitly selected our own Documents source as
                    // the final destination. Its completed contents now belong to them.
                    if a == b {
                        self.remove = false;
                    }
                }
            }
        }
    }
    #[cfg(target_os = "ios")]
    impl Drop for DialogSource {
        fn drop(&mut self) {
            use std::os::unix::fs::MetadataExt;
            if self.remove
                && std::fs::symlink_metadata(&self.path).is_ok_and(|metadata| {
                    metadata.is_file() && (metadata.dev(), metadata.ino()) == self.identity
                })
            {
                let _ = std::fs::remove_file(&self.path);
            }
        }
    }

    /// Fs::open starts access before attempting the file open on iOS. Arm the
    /// guard first, so error returns, cancellation and unwinding also stop it.
    struct ScopedAccess {
        #[cfg(target_os = "ios")]
        app: tauri::AppHandle,
        #[cfg(target_os = "ios")]
        path: Option<FilePath>,
    }
    impl ScopedAccess {
        fn new(_app: &tauri::AppHandle, _path: &FilePath) -> Self {
            Self {
                #[cfg(target_os = "ios")]
                app: _app.clone(),
                #[cfg(target_os = "ios")]
                path: matches!(_path, FilePath::Url(url) if url.scheme() == "file")
                    .then(|| _path.clone()),
            }
        }
        fn finish(&mut self) -> Result<(), String> {
            #[cfg(target_os = "ios")]
            if let Some(path) = self.path.as_ref() {
                self.app
                    .fs()
                    .stop_accessing_security_scoped_resource(path.clone())
                    .map_err(|e| e.to_string())?;
                self.path = None;
            }
            Ok(())
        }
    }
    impl Drop for ScopedAccess {
        fn drop(&mut self) {
            let _ = self.finish();
        }
    }

    fn copy_selected(
        app: &tauri::AppHandle,
        staged: tempfile::NamedTempFile,
        selected: FilePath,
        size: u64,
    ) -> Result<String, String> {
        // No bytes are obtained from the network after opening/truncating the
        // user-selected destination. Provider/write errors may leave a partial
        // document; they never produce a success response or an automatic retry.
        let mut source = staged.reopen().map_err(|e| e.to_string())?;
        source.seek(SeekFrom::Start(0)).map_err(|e| e.to_string())?;
        if source.metadata().map_err(|e| e.to_string())?.len() != size {
            return Err("Staged export size changed".into());
        }
        let mut access = ScopedAccess::new(app, &selected);
        let result: Result<String, String> = (|| {
            let mut options = OpenOptions::new();
            options.read(false).write(true).truncate(true).create(true);
            let mut destination = app
                .fs()
                .open(selected.clone(), options)
                .map_err(|e| e.to_string())?;
            let mut buffer = [0u8; 64 * 1024];
            let mut remaining = size;
            while remaining > 0 {
                let count = remaining.min(buffer.len() as u64) as usize;
                source
                    .read_exact(&mut buffer[..count])
                    .map_err(|e| e.to_string())?;
                destination
                    .write_all(&buffer[..count])
                    .map_err(|e| e.to_string())?;
                remaining -= count as u64;
            }
            destination.flush().map_err(|e| e.to_string())?;
            destination.sync_all().map_err(|e| e.to_string())?;
            Ok(selected.to_string())
        })();
        let released = access.finish();
        match (result, released) {
            (Ok(path), Ok(())) => Ok(path),
            (Err(error), _) => Err(format!("File export did not complete: {error}")),
            (Ok(_), Err(error)) => Err(format!(
                "File written, but document access could not be released: {error}"
            )),
        }
    }

    pub async fn save(
        app: &tauri::AppHandle,
        host: Arc<InstanceHost>,
        id: &str,
    ) -> Result<String, String> {
        let info = completed_file(&host, id).await?;
        let size = validated_size(&info.size_bytes, &info.verified_bytes)?;
        let staged = stage(app, host, &info).await?;
        save_staged(app, staged, &info.name, size).await
    }

    pub async fn save_invitation(
        app: &tauri::AppHandle,
        invitation: String,
    ) -> Result<Option<String>, String> {
        if invitation.is_empty() || invitation.len() > gchat_api::MAX_NETWORK_INVITATION_BYTES {
            return Err("Invalid invitation length".into());
        }
        let directory = app
            .path()
            .app_cache_dir()
            .map_err(|e| e.to_string())?
            .join("private-exports");
        gchat_core::paths::ensure_private_dir(&directory, "private export staging")?;
        let mut staged = tempfile::NamedTempFile::new_in(directory).map_err(|e| e.to_string())?;
        staged
            .write_all(invitation.as_bytes())
            .map_err(|e| e.to_string())?;
        staged.as_file().sync_all().map_err(|e| e.to_string())?;
        let path =
            save_staged(app, staged, "gchat-invitation.txt", invitation.len() as u64).await?;
        Ok((!path.is_empty()).then_some(path))
    }

    async fn save_staged(
        app: &tauri::AppHandle,
        staged: tempfile::NamedTempFile,
        name: &str,
        size: u64,
    ) -> Result<String, String> {
        #[cfg(target_os = "ios")]
        let mut dialog_source = {
            let app = app.clone();
            let name = name.to_string();
            let input = staged.reopen().map_err(|e| e.to_string())?;
            // Keep large disk copies off Tauri's async worker. The source is a
            // private complete file; passing its open handle never exposes a path to JS.
            tokio::task::spawn_blocking(move || DialogSource::prepare(&app, &name, input))
                .await
                .map_err(|e| e.to_string())??
        };
        let (sender, receiver) = tokio::sync::oneshot::channel();
        app.dialog()
            .file()
            .set_file_name(name)
            .save_file(move |selected| {
                #[cfg(target_os = "ios")]
                if let Some(path) = &selected {
                    dialog_source.retain_if_selected(path);
                }
                // Keep the iOS export source alive until the native picker resolves,
                // even if the caller's Rust future is cancelled meanwhile.
                #[cfg(target_os = "ios")]
                let _source = dialog_source;
                let _ = sender.send(selected);
            });
        let Some(selected) = receiver
            .await
            .map_err(|_| "Export destination dialog closed")?
        else {
            return Ok(String::new());
        };
        let app = app.clone();
        tokio::task::spawn_blocking(move || copy_selected(&app, staged, selected, size))
            .await
            .map_err(|e| e.to_string())?
    }
}

#[cfg(any(target_os = "android", target_os = "ios"))]
pub use native::{save, save_invitation};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validates_full_network_binding_not_just_the_file_suffix() {
        let file = "ab".repeat(16);
        let network = "cd".repeat(32);
        assert_eq!(network_id(&file).unwrap(), None);
        assert_eq!(
            network_id(&format!("{network}:{file}")).unwrap(),
            Some(network.as_str())
        );
        for invalid in [
            String::new(),
            format!("x:{file}"),
            format!("{network}:../{file}"),
            format!("{network}:{file}:extra"),
            "zz".repeat(16),
        ] {
            assert!(network_id(&invalid).is_err(), "{invalid}");
        }
    }

    #[test]
    fn names_cannot_select_paths_or_invalid_native_destinations() {
        for valid in ["photo.jpg", "résumé.pdf", "a b.txt"] {
            validate_name(valid).unwrap();
        }
        for invalid in [
            "",
            ".",
            "..",
            "../secret",
            "a/b",
            r"a\b",
            "a:b",
            "name.",
            "name ",
            "a\0b",
            "a\nb",
        ] {
            assert!(validate_name(invalid).is_err(), "{invalid:?}");
        }
        assert!(validate_name(&"x".repeat(256)).is_err());
    }

    #[test]
    fn requires_verified_size_and_addressable_pieces() {
        assert_eq!(validated_size("0", "0").unwrap(), 0);
        assert_eq!(validated_size("262145", "262145").unwrap(), 262145);
        for (size, verified) in [
            ("9", "8"),
            ("+9", "9"),
            ("-1", "-1"),
            ("", ""),
            ("18446744073709551616", "0"),
        ] {
            assert!(validated_size(size, verified).is_err());
        }
        let maximum = (u64::from(u32::MAX) + 1) * PIECE_BYTES;
        assert_eq!(
            validated_size(&maximum.to_string(), &maximum.to_string()).unwrap(),
            maximum
        );
        assert!(validated_size(&(maximum + 1).to_string(), &(maximum + 1).to_string()).is_err());
    }

    #[test]
    fn final_piece_length_and_index_are_exact() {
        assert_eq!(
            piece_size(PIECE_BYTES + 17, 0).unwrap(),
            (0, PIECE_BYTES as usize)
        );
        assert_eq!(piece_size(PIECE_BYTES + 17, PIECE_BYTES).unwrap(), (1, 17));
        assert!(piece_size(17, 17).is_err());
        assert!(piece_size(PIECE_BYTES + 17, 1).is_err());
        assert!(piece_size(u64::MAX, (u64::from(u32::MAX) + 1) * PIECE_BYTES).is_err());
    }
}
