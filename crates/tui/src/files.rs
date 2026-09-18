use gchat_api::{ChatClient, ChatError, CommandOutput, FileRequest, Request, Response};
use std::path::Path;

/// Local paths are interpreted only by the terminal attachment.
pub async fn command(client: &ChatClient, request: &Request) -> Result<Response, ChatError> {
    let Request::Submit {
        operation_id,
        conversation,
        text,
        ..
    } = request
    else {
        unreachable!()
    };
    let result = run(
        client,
        operation_id,
        conversation.as_deref(),
        text.strip_prefix("/file").unwrap_or(""),
    )
    .await;
    result
        .map(|text| Response::Output {
            conversation: conversation.clone(),
            output: CommandOutput::Text {
                title: "Files".into(),
                text,
            },
        })
        .map_err(|message| ChatError {
            code: "files".into(),
            message,
        })
}
async fn run(
    client: &ChatClient,
    handle: &str,
    conversation: Option<&str>,
    text: &str,
) -> Result<String, String> {
    let (action, argument) = text
        .trim()
        .split_once(char::is_whitespace)
        .unwrap_or((text.trim(), ""));
    let argument = argument.trim();
    let filter = if action == "list" && argument == "all" {
        None
    } else {
        conversation
    };
    let control = match action {
        "send" => {
            let conversation = conversation.ok_or("Select a conversation first")?;
            if argument.is_empty() { return Err("Usage: /file send <local path>".into()); }
            client.import_file(handle, conversation, Path::new(argument)).await?;
            return Ok(format!("Shared file {handle}. Accepted copies seed while unlocked."));
        }
        "resume-import" => {
            let (id, path) = argument.split_once(char::is_whitespace).ok_or("Usage: /file resume-import <handle> <local path>")?;
            client.import_file(id, conversation.ok_or("Select the file's conversation first")?, Path::new(path.trim())).await?;
            return Ok(format!("Shared file {id}."));
        }
        "save" => {
            let (id, path) = argument.split_once(char::is_whitespace).ok_or("Usage: /file save <id> <local path>")?;
            client.save_file(id, Path::new(path.trim())).await?;
            return Ok(format!("Saved to {}", path.trim()));
        }
        "cache" => {
            let (mib, days) = argument.split_once(char::is_whitespace).ok_or("Usage: /file cache <MiB> <days>")?;
            let quota = mib.parse::<u64>().ok().and_then(|n| n.checked_mul(1024 * 1024)).ok_or("Invalid cache size")?;
            FileRequest::Configure { quota_bytes: quota.to_string(), retention_days: days.trim().parse().map_err(|_| "Invalid retention days")? }
        }
        "accept" => FileRequest::Accept { id: argument.into() },
        "pause" => FileRequest::Pause { id: argument.into() },
        "resume" => FileRequest::Resume { id: argument.into() },
        "cancel" => FileRequest::Cancel { id: argument.into() },
        "list" => FileRequest::List { conversation: filter.map(str::to_owned) },
        _ => return Ok("/file send <local path>\n/file resume-import <handle> <local path>\n/file list [all]\n/file cache <MiB> <days>\n/file accept|pause|resume|cancel <id>\n/file save <id> <local path>\nPaths may contain spaces; do not add quotes. Downloads require acceptance and share retained pieces with current participants while unlocked.".into()),
    };
    let snapshot = client.files(control).await?;
    let mut output = format!(
        "Cache: {} / {} bytes reserved, {} days retention\n",
        snapshot.used_bytes, snapshot.quota_bytes, snapshot.retention_days
    );
    for file in snapshot
        .files
        .iter()
        .filter(|f| filter.is_none_or(|c| f.conversation == c))
    {
        output.push_str(&format!(
            "{}  {}  {:?}  {}/{} bytes  {} peers\n",
            file.id, file.name, file.state, file.verified_bytes, file.size_bytes, file.sources
        ));
        if let Some(error) = &file.error {
            output.push_str(&format!("  {error}\n"));
        }
    }
    Ok(output)
}
