//! Native attachment-side paths never cross the service boundary.
use crate::{files::*, ChatClient, FileRequest, FileSnapshot, FileState, Request, Response};
use std::path::Path;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

impl ChatClient {
    /// File IDs passed to native export can explicitly select a joined network.
    pub async fn files_for(&self, id: &str) -> Result<FileSnapshot, String> {
        if let Some((network, handle)) = id.split_once(':') {
            if network.len() != 64
                || !network.bytes().all(|b| b.is_ascii_hexdigit())
                || handle.len() != 32
                || !handle.bytes().all(|b| b.is_ascii_hexdigit())
            {
                return Err("Invalid network file handle".into());
            }
            let response = self
                .request(Request::Networks {
                    request: crate::NetworkRequest::Call {
                        network: network.into(),
                        request: Box::new(Request::Files {
                            request: FileRequest::List { conversation: None },
                        }),
                    },
                })
                .await?;
            if let Response::Networks {
                response:
                    crate::NetworkResponse::Result {
                        network: actual,
                        response,
                    },
            } = response
            {
                if actual != network {
                    return Err("File response belongs to another network".into());
                }
                if let Response::Files { mut snapshot } = *response {
                    for file in &mut snapshot.files {
                        file.id = format!("{network}:{}", file.id);
                    }
                    return Ok(snapshot);
                }
            }
            return Err("Invalid network file response".into());
        }
        self.files(FileRequest::List { conversation: None }).await
    }
    pub async fn files(&self, request: FileRequest) -> Result<FileSnapshot, String> {
        match self.request(Request::Files { request }).await? {
            Response::Files { snapshot } => Ok(snapshot),
            _ => Err("Invalid file response".into()),
        }
    }
    /// A stable handle allows retrying an interrupted import of the same source.
    pub async fn import_file(
        &self,
        id: &str,
        conversation: &str,
        path: &Path,
    ) -> Result<(), String> {
        let mut source = tokio::fs::File::open(path)
            .await
            .map_err(|e| e.to_string())?;
        let metadata = source.metadata().await.map_err(|e| e.to_string())?;
        if !metadata.is_file() {
            return Err("Choose a regular file".into());
        }
        let name = path
            .file_name()
            .and_then(|s| s.to_str())
            .ok_or("Invalid file name")?;
        let snapshot = self
            .files(FileRequest::Prepare {
                id: id.into(),
                conversation: conversation.into(),
                name: name.into(),
                size_bytes: metadata.len().to_string(),
            })
            .await?;
        if snapshot
            .files
            .iter()
            .any(|f| f.id == id && matches!(f.state, FileState::Complete))
        {
            return Ok(());
        }
        let mut remaining = metadata.len();
        let mut buffer = vec![0; PIECE_BYTES];
        let mut piece = 0;
        while remaining > 0 {
            let n = remaining.min(PIECE_BYTES as u64) as usize;
            source
                .read_exact(&mut buffer[..n])
                .await
                .map_err(|e| e.to_string())?;
            self.file_io(encode_io(
                &FileIo {
                    instance: self.instance_id().into(),
                    id: id.into(),
                    piece,
                    upload: true,
                },
                &buffer[..n],
            )?)
            .await?;
            remaining -= n as u64;
            piece += 1;
        }
        if source
            .read(&mut buffer[..1])
            .await
            .map_err(|e| e.to_string())?
            != 0
        {
            return Err("Source grew during import; cancel and share again".into());
        }
        let after = source.metadata().await.map_err(|e| e.to_string())?;
        if after.len() != metadata.len() || after.modified().ok() != metadata.modified().ok() {
            return Err("Source changed during import; cancel and share again".into());
        }
        self.files(FileRequest::Commit { id: id.into() }).await?;
        Ok(())
    }
    /// Materialize a verified copy atomically; never overwrite an existing path.
    pub async fn save_file(&self, id: &str, path: &Path) -> Result<(), String> {
        let snapshot = self.files_for(id).await?;
        let info = snapshot
            .files
            .iter()
            .find(|f| f.id == id && matches!(f.state, FileState::Complete))
            .ok_or("File is not complete")?;
        let size: u64 = info.size_bytes.parse().map_err(|_| "Invalid file size")?;
        let parent = path
            .parent()
            .filter(|p| !p.as_os_str().is_empty())
            .unwrap_or(Path::new("."));
        let temp = tempfile::NamedTempFile::new_in(parent).map_err(|e| e.to_string())?;
        let mut output = tokio::fs::File::from_std(temp.reopen().map_err(|e| e.to_string())?);
        let mut remaining = size;
        let mut piece = 0;
        while remaining > 0 {
            let data = self
                .file_io(encode_io(
                    &FileIo {
                        instance: self.instance_id().into(),
                        id: id.into(),
                        piece,
                        upload: false,
                    },
                    &[],
                )?)
                .await?;
            let n = remaining.min(PIECE_BYTES as u64) as usize;
            if data.len() != n {
                return Err("Invalid exported piece length".into());
            }
            output.write_all(&data).await.map_err(|e| e.to_string())?;
            remaining -= n as u64;
            piece += 1;
        }
        output.flush().await.map_err(|e| e.to_string())?;
        output.sync_all().await.map_err(|e| e.to_string())?;
        drop(output);
        let destination = path.to_path_buf();
        tokio::task::spawn_blocking(move || {
            temp.persist_noclobber(destination)
                .map(|_| ())
                .map_err(|e| e.to_string())
        })
        .await
        .map_err(|e| e.to_string())?
    }
}
