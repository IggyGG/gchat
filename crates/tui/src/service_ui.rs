//! Presentation-only terminal attachment to one gchat service instance.
use crossterm::{
    event::{self, Event, KeyCode, KeyEventKind, KeyModifiers},
    execute,
    terminal::{self, EnterAlternateScreen, LeaveAlternateScreen},
};
use gchat_api::{
    ChatClient, CommandOutput, Completion, Conversation, HistoryPage, Request, Response, Snapshot,
};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph, Wrap},
    Terminal,
};
use std::{collections::HashMap, io::stdout, time::Duration};
use tokio::sync::mpsc;
use zeroize::Zeroize;

enum Reply {
    State(Snapshot),
    Network(gchat_api::NetworkStatus),
    Operation(u64, Request, Result<Response, gchat_api::ChatError>),
    Search(u64, String, bool, Result<HistoryPage, String>),
    History(u64, String, bool, Result<HistoryPage, String>),
    Offline(gchat_api::ChatError),
}
struct Restore;
impl Drop for Restore {
    fn drop(&mut self) {
        let _ = terminal::disable_raw_mode();
        let _ = execute!(stdout(), LeaveAlternateScreen, event::DisableBracketedPaste);
    }
}

fn is_network_invitation(text: &str) -> bool {
    text.trim_start().starts_with("GCNI1-")
        || text
            .trim_start()
            .to_ascii_lowercase()
            .starts_with("/network join ")
}

fn input_limit(text: &str) -> usize {
    if is_network_invitation(text) {
        gchat_api::MAX_NETWORK_INVITATION_BYTES + "/network join ".len()
    } else {
        gchat_api::MAX_INPUT_BYTES
    }
}

pub async fn run(client: ChatClient, mono: bool) -> Result<(), String> {
    let Response::Snapshot { snapshot: initial } = client.request(Request::Snapshot).await? else {
        return Err("invalid instance snapshot".into());
    };
    let (tx, mut rx) = mpsc::unbounded_channel();
    let watch = tokio::spawn({
        let client = client.clone();
        let tx = tx.clone();
        async move {
            loop {
                let revision = match client.request_typed(Request::Snapshot).await {
                    Ok(Response::Snapshot { snapshot }) => {
                        let revision = snapshot.revision.clone();
                        if tx.send(Reply::State(snapshot)).is_err() {
                            break;
                        }
                        revision
                    }
                    Ok(_) => break,
                    Err(error) => {
                        let retryable = error.retryable();
                        if tx.send(Reply::Offline(error)).is_err() {
                            break;
                        }
                        if !retryable {
                            break;
                        }
                        tokio::time::sleep(Duration::from_secs(1)).await;
                        continue;
                    }
                };
                if let Ok(Response::NetworkStatus { status }) =
                    client.request(Request::NetworkStatus).await
                {
                    if tx.send(Reply::Network(status)).is_err() {
                        break;
                    }
                }
                let _ = client
                    .request(Request::Events {
                        after: revision,
                        wait_ms: 2_000,
                    })
                    .await;
            }
        }
    });
    let (keys, mut input) = mpsc::unbounded_channel();
    std::thread::spawn(move || {
        while !keys.is_closed() {
            if event::poll(Duration::from_millis(100)).unwrap_or(false) {
                match event::read() {
                    Ok(event) => {
                        if keys.send(event).is_err() {
                            break;
                        }
                    }
                    _ => break,
                }
            }
        }
    });
    terminal::enable_raw_mode().map_err(|e| e.to_string())?;
    execute!(stdout(), EnterAlternateScreen, event::EnableBracketedPaste)
        .map_err(|e| e.to_string())?;
    let _restore = Restore;
    let mut terminal = Terminal::new(CrosstermBackend::new(stdout())).map_err(|e| e.to_string())?;
    let mut state = initial;
    let mut network = gchat_api::NetworkStatus::new(gchat_api::NetworkState::Locked);
    let navigation_path = navigation_path(&client);
    let mut navigation = load_navigation(&navigation_path);
    let remembered = navigation
        .get("selected")
        .and_then(|v| v.as_str())
        .map(str::to_string);
    let mut restored_selection = !state.instance.locked;
    let mut selected = remembered
        .filter(|id| state.conversations.iter().any(|c| &c.id == id))
        .or_else(|| state.conversations.first().map(|c| c.id.clone()));
    let mut draft = crate::input::LineEdit::default();
    let mut drafts: HashMap<Option<String>, (crate::input::LineEdit, u16)> = HashMap::new();
    let mut saved_draft = String::new();
    let mut outputs: HashMap<Option<String>, Vec<String>> = HashMap::new();
    let mut invitations: HashMap<Option<String>, String> = HashMap::new();
    let mut hidden = std::collections::HashSet::new();
    let mut candidates: Vec<Completion> = Vec::new();
    let mut candidate_index = 0usize;
    let mut offline: Option<gchat_api::ChatError> = None;
    let mut notices = vec![
        "F1 help · F5 windows · F6 nicks · Alt+←/→ switch · Ctrl+F find · Ctrl+Q close UI".into(),
    ];
    let mut messages = Vec::new();
    let mut before = None;
    let mut scrollbacks = HashMap::new();
    let mut history_loading = false;
    let mut history_again = selected.is_some();
    let mut operations: HashMap<u64, Option<String>> = HashMap::new();
    let mut operation_sequence = 0u64;
    let mut unread_markers: HashMap<String, String> = HashMap::new();
    let mut search_open = false;
    let mut search_draft = crate::input::LineEdit::default();
    let mut search_messages: Vec<gchat_api::Message> = Vec::new();
    let mut search_before: Option<String> = None;
    let mut search_offset = 0u16;
    let mut search_generation = 0u64;
    let mut search_busy = false;
    let mut search_error = String::new();
    let mut failures = retained_submissions(&client);
    let mut history_position = None;
    let mut offset = selected
        .as_ref()
        .and_then(|id| navigation["positions"][id]["offset"].as_u64())
        .unwrap_or(0)
        .min(u16::MAX as u64) as u16;
    let mut history_generation = 0u64;
    let mut tick = tokio::time::interval(Duration::from_millis(100));
    loop {
        let pending = operations.values().any(|scope| scope == &selected);
        let old_selection = selected.clone();
        let mut search_request = None;
        let mut refresh = false;
        let mut older = false;
        let mut request = None;
        let mut check_operation = false;
        let mut edit_after_select = None;
        let history: Vec<String> = state
            .input_history
            .iter()
            .filter(|item| item.conversation == selected)
            .map(|item| item.text.clone())
            .collect();
        tokio::select! {
            Some(reply) = rx.recv() => match reply {
                Reply::Network(status) => { network = status; refresh = true; },
                Reply::State(snapshot) => {
                    offline = None;
                    refresh = snapshot.revision != state.revision;
                    if snapshot.instance.boot_id != state.instance.boot_id || snapshot.instance.locked {
                        history_generation += 1;
                        messages.clear();
                        scrollbacks.clear(); before = None; history_loading = false;
                    }
                    if snapshot.instance.locked && !state.instance.locked {
                        draft.value.zeroize(); draft.clear();
                        for (text, _) in drafts.values_mut() { text.value.zeroize(); }
                        drafts.clear(); saved_draft.zeroize(); saved_draft.clear();
                        outputs.clear(); invitations.clear(); candidates.clear(); unread_markers.clear(); search_open = false; search_draft.clear(); search_messages.clear(); search_generation += 1;
                        notices.clear(); failures.clear(); history_position = None; restored_selection = false;
                    }
                    if !snapshot.instance.locked && (state.instance.locked || snapshot.instance.boot_id != state.instance.boot_id) {
                        for (request, code) in retained_submissions(&client) {
                            let Request::Submit {operation_id, ..} = &request else { continue; };
                            if !failures.iter().any(|(r, _)| matches!(r, Request::Submit {operation_id: id, ..} if id == operation_id)) { failures.push((request, code)); }
                        }
                    }
                    let available: Vec<_> = snapshot.conversations.iter().map(|c| Some(c.id.clone())).chain(std::iter::once(None)).collect();
                    drafts.retain(|id, _| available.contains(id)); scrollbacks.retain(|id, _| available.contains(id)); outputs.retain(|id, _| available.contains(id)); invitations.retain(|id, _| available.contains(id));
                    state = snapshot;
                    if !state.instance.locked && !restored_selection {
                        restored_selection = true;
                        selected = navigation["selected"].as_str().filter(|id| state.conversations.iter().any(|c| c.id == *id)).map(str::to_string).or_else(|| state.conversations.first().map(|c| c.id.clone()));
                    }
                    if selected.as_ref().is_some_and(|id| !state.conversations.iter().any(|c| &c.id == id)) {
                        selected = None;
                    }
                }
                Reply::Operation(sequence, original, result) => {
                    operations.remove(&sequence);
                    let retry = matches!(original, Request::Submit { .. }).then(|| original.clone());
                    match result {
                        Ok(Response::Applied { conversation, notice }) if !state.instance.locked => {
                            let origin = retry.as_ref().and_then(|r| match r { Request::Submit { conversation, .. } => conversation.as_ref(), _ => None });
                            if selected.as_ref() == origin { if let Some(conversation) = conversation { hidden.remove(&conversation); selected = Some(conversation); } }
                            if let Some(notice) = notice { notices.push(notice); }
                            refresh = true;
                        }
                        Ok(Response::Completed { items }) if !state.instance.locked => {
                            if matches!(&original, Request::Complete { conversation, text } if conversation == &selected && text == &draft.value) { candidates = items; candidate_index = 0; }
                        }
                        Ok(Response::Output { conversation, output }) if !state.instance.locked => {
                            if let CommandOutput::Invitation { link, .. } = &output { invitations.insert(conversation.clone(), link.clone()); }
                            match output {
                                CommandOutput::Close { conversation } => { hidden.insert(conversation.clone()); if selected.as_ref() == Some(&conversation) { selected = None; } }
                                CommandOutput::Status { text } => { outputs.entry(None).or_default().push(text); selected = None; }
                                output => outputs.entry(conversation).or_default().push(format_output(&output)),
                            }
                            refresh = true;
                        }
                        Ok(Response::NetworkStatus { status }) => { network = status; notices.push("Network invitation saved. Connecting in the background.".into()); }
                        Ok(Response::Snapshot { snapshot }) => { let _ = tx.send(Reply::State(snapshot)); }
                        Ok(Response::Instance { instance }) => {
                            if instance.locked { scrollbacks.clear(); invitations.clear(); before = None; history_loading = false; history_generation += 1; unread_markers.clear(); search_open = false; search_draft.clear(); search_messages.clear(); search_generation += 1; saved_draft.zeroize(); draft.value.zeroize(); draft.clear(); for (text, _) in drafts.values_mut() { text.value.zeroize(); } drafts.clear(); outputs.clear(); candidates.clear(); notices.clear(); failures.clear(); history_position = None; messages.clear(); }
                            state.instance = instance; refresh = true;
                        }
                        Ok(_) => {}
                        Err(error) => {
                            let failure_code = error.code.clone();
                            let target = retry.as_ref().and_then(|r| match r { Request::Submit { conversation, .. } => conversation.as_ref(), _ => None }).and_then(|id| state.conversations.iter().find(|c| &c.id == id)).map_or("Status", |c| c.name.as_str());
                            notices.push(format!("{target}: {}", error.message));
                            if let Some(retry) = retry.filter(|_| !state.instance.locked) {
                                failures.push((retry, failure_code.clone()));
                                notices.push(if failure_code == "rejected" { "Command was not accepted. F3 edits the original destination." } else { "Request retained: F2 checks the same operation; F3 edits as a new request." }.into());
                            }
                        }
                    }
                }
                Reply::History(generation, conversation, is_older, result) if generation == history_generation && selected.as_ref() == Some(&conversation) && !state.instance.locked => {
                    history_loading = false;
                    match result {
                    Ok(page) => {
                        if !is_older && !unread_markers.contains_key(&conversation) {
                            let unread = state.conversations.iter().find(|c| c.id == conversation).map_or(0, |c| c.unread as usize);
                            let incoming: Vec<_> = page.messages.iter().filter(|m| !m.mine).collect();
                            if unread > 0 { if let Some(first) = incoming.get(incoming.len().saturating_sub(unread)) { unread_markers.insert(conversation.clone(), first.id.clone()); } }
                        }
                        if is_older {
                            let mut earlier = page.messages;
                            earlier.append(&mut messages); messages = earlier; before = page.before;
                        } else if let Some(overlap) = messages.iter().position(|m| page.messages.iter().any(|next| next.id == m.id)) {
                            messages.truncate(overlap); messages.extend(page.messages);
                        } else { messages = page.messages; before = page.before; }
                        if offset > 0 && before.is_some() && navigation["positions"][&conversation]["oldest"].as_str().is_some_and(|id| !messages.iter().any(|m| m.id == id)) { older = true; refresh = true; }
                        if offset == 0 {
                            if let Some(last) = messages.last() {
                                let client = client.clone();
                                let message_id = last.id.clone();
                                tokio::spawn(async move { let _ = client.request(Request::MarkRead { conversation, message_id }).await; });
                            }
                        }
                    }
                    Err(error) => notices.push(error),
                }},
                Reply::History(_, _, _, _) => {}
                Reply::Search(generation, conversation, earlier, result) if generation == search_generation && selected.as_ref() == Some(&conversation) && !state.instance.locked => {
                    search_busy = false;
                    match result {
                        Ok(page) => { search_before = page.before; if earlier { let mut incoming = page.messages; incoming.append(&mut search_messages); search_messages = incoming; } else { search_messages = page.messages; } }
                        Err(error) => search_error = error,
                    }
                }
                Reply::Search(_, _, _, _) => {}
                Reply::Offline(error) => offline = Some(error),
            },
            Some(event) = input.recv() => match event {
                Event::Key(key) if key.kind == KeyEventKind::Press => {
                    if key.modifiers.contains(KeyModifiers::CONTROL) && key.code == KeyCode::Char('q') { break; }
                    if !state.instance.locked && key.modifiers.contains(KeyModifiers::CONTROL) && key.code == KeyCode::Char('f') {
                        search_open = !search_open; search_offset = 0; search_generation += 1; search_busy = false;
                    } else if search_open {
                        match key.code {
                            KeyCode::Esc => { search_open = false; search_generation += 1; search_busy = false; }
                            KeyCode::Enter if !search_busy && !search_draft.value.trim().is_empty() => search_request = Some(false),
                            KeyCode::PageUp => { search_offset = search_offset.saturating_add(10); if !search_busy && search_before.is_some() { search_request = Some(true); } }
                            KeyCode::PageDown => search_offset = search_offset.saturating_sub(10),
                            KeyCode::Char(c) if !key.modifiers.contains(KeyModifiers::CONTROL) && search_draft.value.len() + c.len_utf8() <= 256 => search_draft.push(c),
                            KeyCode::Left => search_draft.left(), KeyCode::Right => search_draft.right(), KeyCode::Home => search_draft.home(), KeyCode::End => search_draft.end(),
                            KeyCode::Delete => search_draft.delete(), KeyCode::Backspace => search_draft.backspace(),
                            _ => {}
                        }
                    } else if key.modifiers.contains(KeyModifiers::ALT) && matches!(key.code, KeyCode::Left | KeyCode::Right) {
                        let visible: Vec<_> = state.conversations.iter().filter(|c| !hidden.contains(&c.id)).collect();
                        let count = visible.len() + 1;
                        let current = selected.as_ref().and_then(|id| visible.iter().position(|c| &c.id == id)).map_or(0, |i| i + 1);
                        let next = if key.code == KeyCode::Right { (current + 1) % count } else { (current + count - 1) % count };
                        selected = next.checked_sub(1).map(|i| visible[i].id.clone());
                    } else {
                        match key.code {
                            KeyCode::Enter if !candidates.is_empty() => { draft.set(format!("{} ", candidates[candidate_index].text)); candidates.clear(); }
                            KeyCode::Enter if !pending && offline.is_none() && !draft.value.is_empty() => {
                                let mut text = draft.take();
                                if state.instance.locked {
                                    let create = if state.instance.protocol_locked { !state.instance.profile_exists } else { !state.instance.archive_exists };
                                    request = Some(Request::Unlock { passphrase: text, create });
                                } else if text.trim().starts_with("GCNI1-") {
                                    request = Some(Request::ImportNetworkInvitation { code: text.trim().into() });
                                    text.zeroize();
                                } else { request = Some(submit(selected.clone(), text)); }
                                history_position = None;
                            }
                            KeyCode::Char(c) if !key.modifiers.contains(KeyModifiers::CONTROL) && draft.value.len() + c.len_utf8() <= input_limit(&draft.value) => { draft.push(c); history_position = None; candidates.clear(); },
                            KeyCode::Left => draft.left(),
                            KeyCode::Right => draft.right(),
                            KeyCode::Home => draft.home(),
                            KeyCode::End if !key.modifiers.contains(KeyModifiers::CONTROL) => draft.end(),
                            KeyCode::Delete => { draft.delete(); history_position = None; candidates.clear(); },
                            KeyCode::Backspace => { draft.backspace(); history_position = None; candidates.clear(); }
                            KeyCode::Tab if !state.instance.locked && !candidates.is_empty() => { candidate_index = (candidate_index + 1) % candidates.len(); }
                            KeyCode::BackTab if !candidates.is_empty() => { candidate_index = (candidate_index + candidates.len() - 1) % candidates.len(); }
                            KeyCode::Tab if !pending && !state.instance.locked && !is_network_invitation(&draft.value) => request = Some(Request::Complete { conversation: selected.clone(), text: draft.value.clone() }),
                            KeyCode::F(1) if !pending && !state.instance.locked => request = Some(submit(selected.clone(), "/help".into())),
                            KeyCode::F(2) if !pending && !state.instance.locked && failures.last().is_some_and(|(_, code)| code != "rejected") => { request = failures.pop().map(|(request, _)| request); check_operation = true; },
                            KeyCode::F(3) if !pending && !state.instance.locked => {
                                if let Some((Request::Submit { text, conversation, .. }, _)) = failures.pop() { edit_after_select = Some(text); selected = conversation; }
                            }
                            KeyCode::F(4) if !state.instance.locked => { if let Some(link) = invitations.get(&selected) { notices.push(crate::clipboard::copy(link).message()); } }
                            KeyCode::F(5) if !state.instance.locked => request = Some(submit(selected.clone(), "/list".into())),
                            KeyCode::F(6) if !state.instance.locked => request = Some(submit(selected.clone(), "/names".into())),
                            KeyCode::End if key.modifiers.contains(KeyModifiers::CONTROL) => { offset = 0; refresh = true; },
                            KeyCode::PageUp => { offset = offset.saturating_add(10); if before.is_some() && !history_loading { older = true; refresh = true; } },
                            KeyCode::PageDown => { offset = offset.saturating_sub(10); if offset == 0 { refresh = true; } }
                            KeyCode::Up if !state.instance.locked && !is_network_invitation(&draft.value) => {
                                let len = history.len();
                                if len > 0 {
                                    if history_position.is_none() { saved_draft = draft.value.clone(); }
                                    let next = history_position.unwrap_or(len).saturating_sub(1);
                                    draft.set(history[next].clone()); history_position = Some(next);
                                }
                            }
                            KeyCode::Down if !state.instance.locked => {
                                if let Some(current) = history_position {
                                    let next = current + 1;
                                    if next < history.len() { draft.set(history[next].clone()); history_position = Some(next); }
                                    else { draft.set(std::mem::take(&mut saved_draft)); history_position = None; }
                                }
                            }
                            KeyCode::Esc if !candidates.is_empty() => candidates.clear(),
                            KeyCode::Esc => { draft.value.zeroize(); draft.clear(); }
                            _ => {}
                        }
                    }
                }
                Event::Paste(text) if search_open => { if search_draft.value.len() + text.len() <= 256 { search_draft.insert_exact(&text); } else { search_error = "Search accepts at most 256 UTF-8 bytes. Input was not changed.".into(); } }
                Event::Paste(mut text) => {
                    let limit = if draft.value.is_empty() { input_limit(&text) } else { input_limit(&draft.value) };
                    if draft.value.len() + text.len() <= limit { draft.insert_exact(&text); history_position = None; candidates.clear(); }
                    else { notices.push(format!("Paste exceeds {limit} UTF-8 bytes; existing input kept unchanged.")); }
                    text.zeroize();
                }
                _ => {}
            },
            _ = tick.tick() => {}
        }
        if notices.len() > 100 {
            notices.drain(..notices.len() - 100);
        }
        if selected != old_selection {
            search_open = false;
            search_generation += 1;
            search_draft.clear();
            search_messages.clear();
            search_before = None;
            search_busy = false;
            search_error.clear();
            search_offset = 0;
            if offset == 0 {
                if let Some(id) = &old_selection {
                    unread_markers.remove(id);
                }
            }
            candidates.clear();
            if is_network_invitation(&draft.value) {
                draft.value.zeroize();
                draft.clear();
            }
            drafts.insert(old_selection.clone(), (std::mem::take(&mut draft), offset));
            let restored = drafts.remove(&selected).unwrap_or_else(|| {
                (
                    crate::input::LineEdit::default(),
                    selected
                        .as_ref()
                        .and_then(|id| navigation["positions"][id]["offset"].as_u64())
                        .unwrap_or(0)
                        .min(u16::MAX as u64) as u16,
                )
            });
            draft = restored.0;
            offset = restored.1;
            history_position = None;
            saved_draft.zeroize();
            saved_draft.clear();
            history_generation += 1;
            scrollbacks.insert(
                old_selection.clone(),
                (std::mem::take(&mut messages), before.take()),
            );
            let restored = scrollbacks.remove(&selected).unwrap_or_default();
            messages = restored.0;
            before = restored.1;
            history_loading = false;
            // A revoked provider or removed conversation must not be reinserted
            // into caches by the selection transition above.
            let available = |id: &Option<String>| {
                id.as_ref()
                    .is_none_or(|id| state.conversations.iter().any(|c| &c.id == id))
            };
            drafts.retain(|id, _| available(id));
            scrollbacks.retain(|id, _| available(id));
            refresh = true;
        }
        if let Some(text) = edit_after_select {
            draft.set(text);
        }
        if refresh {
            history_again = true;
        }
        if history_again && !history_loading && !state.instance.locked {
            if let Some(conversation) = selected.clone() {
                history_again = false;
                history_loading = true;
                history_generation += 1;
                let generation = history_generation;
                let client = client.clone();
                let tx = tx.clone();
                let cursor = if older { before.clone() } else { None };
                tokio::spawn(async move {
                    let result = match client
                        .request(Request::History {
                            conversation: conversation.clone(),
                            before: cursor,
                            limit: 200,
                        })
                        .await
                    {
                        Ok(Response::History { page }) => Ok(page),
                        Ok(_) => Err("invalid history response".into()),
                        Err(e) => Err(e),
                    };
                    let _ = tx.send(Reply::History(generation, conversation, older, result));
                });
            }
        }
        if let Some(request) = request {
            operation_sequence += 1;
            let sequence = operation_sequence;
            let scope = match &request {
                Request::Submit { conversation, .. } | Request::Complete { conversation, .. } => {
                    conversation.clone()
                }
                _ => None,
            };
            operations.insert(sequence, scope);
            let client = client.clone();
            let tx = tx.clone();
            let retry = matches!(request, Request::Submit { .. }).then(|| request.clone());
            if let Some(Request::Submit { operation_id, .. }) = &retry {
                failures.retain(|(request, _)| !matches!(request, Request::Submit { operation_id: prior, .. } if prior == operation_id));
            }
            tokio::spawn(async move {
                let result = if matches!(&request, Request::Submit { text, .. } if text == "/file" || text.starts_with("/file "))
                {
                    crate::files::command(&client, &request).await
                } else if check_operation {
                    if let Request::Submit { operation_id, .. } = &request {
                        client.resume_submit(operation_id).await
                    } else {
                        client.request_typed(request.clone()).await
                    }
                } else {
                    client.request_typed(request.clone()).await
                };
                let _ = tx.send(Reply::Operation(sequence, request, result));
            });
        }
        if let (Some(earlier), Some(conversation)) = (search_request, selected.clone()) {
            search_generation += 1;
            let generation = search_generation;
            search_busy = true;
            search_error.clear();
            let text = search_draft.value.trim().to_string();
            let cursor = if earlier {
                search_before.clone()
            } else {
                search_offset = 0;
                None
            };
            let client = client.clone();
            let tx = tx.clone();
            tokio::spawn(async move {
                let result = match client
                    .request(Request::Search {
                        conversation: conversation.clone(),
                        text,
                        before: cursor,
                        limit: 200,
                    })
                    .await
                {
                    Ok(Response::History { page }) => Ok(page),
                    Ok(_) => Err("Invalid search response".into()),
                    Err(error) => Err(error),
                };
                let _ = tx.send(Reply::Search(generation, conversation, earlier, result));
            });
        }
        if !state.instance.locked {
            let mut next = navigation.clone();
            next["selected"] = serde_json::json!(selected);
            if let Some(id) = &selected {
                if !history_loading {
                    next["positions"][id] = serde_json::json!({ "offset": offset, "oldest": messages.first().map(|m| &m.id) });
                }
            }
            if next != navigation {
                save_navigation(&navigation_path, &next);
                navigation = next;
            }
        }
        terminal
            .draw(|frame| {
                let area = frame.area();
                let accent = if mono { Color::White } else { Color::Cyan };
                let sections = Layout::default()
                    .direction(Direction::Vertical)
                    .constraints([
                        Constraint::Length(1),
                        Constraint::Min(1),
                        Constraint::Length(3),
                        Constraint::Length(1),
                    ])
                    .split(area);
                frame.render_widget(
                    Paragraph::new(format!(
                        "gchat · {} · {}",
                        state.instance.label,
                        &state.instance.id[..8]
                    ))
                    .style(Style::default().fg(accent).add_modifier(Modifier::BOLD)),
                    sections[0],
                );
                let columns = Layout::default()
                    .direction(Direction::Horizontal)
                    .constraints(if area.width >= 100 {
                        vec![
                            Constraint::Length(22),
                            Constraint::Min(20),
                            Constraint::Length(20),
                        ]
                    } else if area.width >= 70 {
                        vec![
                            Constraint::Length(20),
                            Constraint::Min(20),
                            Constraint::Length(0),
                        ]
                    } else {
                        vec![
                            Constraint::Length(0),
                            Constraint::Min(1),
                            Constraint::Length(0),
                        ]
                    })
                    .split(sections[1]);
                let active = selected
                    .as_ref()
                    .and_then(|id| state.conversations.iter().find(|c| &c.id == id));
                let mut rooms = vec![ListItem::new("Status").style(if selected.is_none() {
                    Style::default().fg(accent)
                } else {
                    Style::default()
                })];
                rooms.extend(
                    state
                        .conversations
                        .iter()
                        .filter(|c| !hidden.contains(&c.id))
                        .map(|c| {
                            ListItem::new(format!(
                                "{}{}",
                                c.name,
                                if c.unread > 0 {
                                    format!(" ({})", c.unread)
                                } else {
                                    String::new()
                                }
                            ))
                            .style(
                                if selected.as_ref() == Some(&c.id) {
                                    Style::default().fg(accent).add_modifier(Modifier::BOLD)
                                } else {
                                    Style::default()
                                },
                            )
                        }),
                );
                frame.render_widget(
                    List::new(rooms).block(Block::default().borders(Borders::ALL).title("Windows")),
                    columns[0],
                );
                let mut lines = if state.instance.locked {
                    vec![
                        Line::from(unlock_title(&state)),
                        Line::from(""),
                        Line::from("Enter the passphrase below. Ctrl+Q closes this UI."),
                        Line::from(notices.last().cloned().unwrap_or_default()),
                    ]
                } else if active.is_some() {
                    let mut lines = Vec::new();
                    let mut date = String::new();
                    for m in &messages {
                        if selected.as_ref().and_then(|id| unread_markers.get(id)) == Some(&m.id) {
                            lines.push(Line::from("── New messages ──"));
                        }
                        let next_date = local_datetime(m.timestamp, "%Y-%m-%d");
                        if next_date != date {
                            lines.push(Line::from(format!("── {next_date} ──")));
                            date = next_date;
                        }
                        let action = m
                            .body
                            .strip_prefix("\u{1}ACTION ")
                            .and_then(|s| s.strip_suffix('\u{1}'));
                        lines.push(Line::from(vec![
                            Span::styled(
                                format!("[{}] ", local_datetime(m.timestamp, "%H:%M")),
                                Style::default().fg(Color::DarkGray),
                            ),
                            Span::styled(
                                if action.is_some() {
                                    format!("* {} ", m.nickname)
                                } else {
                                    format!("<{}> ", m.nickname)
                                },
                                Style::default().fg(accent),
                            ),
                            Span::raw(action.unwrap_or(&m.body).to_string()),
                            Span::styled(
                                if m.mine { " · accepted locally" } else { "" },
                                Style::default().fg(Color::DarkGray),
                            ),
                        ]));
                        if let Some(result) = &m.result {
                            lines.push(Line::from(format!(
                                "  {}{}",
                                result.state,
                                if result.stderr { " · stderr" } else { "" }
                            )));
                            if let Some(message) = &result.message_id { lines.push(Line::from(format!("  Result for message {message}"))); }
                            if let Some(body) = &result.output_base64 {
                                use base64::Engine;
                                if let Ok(bytes) =
                                    base64::engine::general_purpose::STANDARD.decode(body)
                                {
                                    lines.extend(
                                        String::from_utf8_lossy(&bytes)
                                            .lines()
                                            .map(|line| Line::from(line.to_string())),
                                    );
                                }
                            }
                            lines
                                .extend(result.details.iter().map(|text| Line::from(text.clone())));
                            lines.extend(result.artifacts.iter().map(|artifact| {
                                Line::from(format!("{}: {}", artifact.name, artifact.url))
                            }));
                        }
                    }
                    lines
                } else {
                    notices
                        .iter()
                        .flat_map(|s| s.lines().map(|s| Line::from(s.to_string())))
                        .collect()
                };
                if !state.instance.locked {
                    if !matches!(network.state, gchat_api::NetworkState::LocalOnly | gchat_api::NetworkState::Locked) {
                        lines.push(Line::from(network.message.clone()));
                        if matches!(network.state, gchat_api::NetworkState::InvitationRequired | gchat_api::NetworkState::InvitationExpired) {
                            lines.push(Line::from("Paste your GCNI1- network invitation and press Enter. Relay settings are included."));
                            lines.push(Line::from("After connecting, use /join with a separate conversation invitation."));
                        }
                    }
                    for error in &state.provider_errors {
                        lines.push(Line::from(format!(
                            "Conversation provider {}: {} · /refresh reconnects",
                            if error.retryable {
                                "reconnecting"
                            } else {
                                "blocked"
                            },
                            error.message
                        )));
                    }
                    if let Some(results) = outputs.get(&selected) {
                        lines.extend(results.iter().flat_map(|text| {
                            text.lines().map(|line| Line::from(line.to_string()))
                        }));
                    }
                    if !candidates.is_empty() {
                        lines.push(Line::from(format!(
                            "Completion ({}/{}): {} · Tab cycles · Enter chooses · Esc closes",
                            candidate_index + 1,
                            candidates.len(),
                            candidates
                                .iter()
                                .map(|c| c.text.as_str())
                                .collect::<Vec<_>>()
                                .join(" | ")
                        )));
                    }
                }
                if let Some((Request::Submit { conversation, .. }, code)) = failures.last() {
                    let target = conversation.as_ref().and_then(|id| state.conversations.iter().find(|c| &c.id == id)).map_or("Status", |c| c.name.as_str());
                    lines.push(Line::from(format!("{} retained operation(s) · latest: {target} · {}F3 edits original destination", failures.len(), if code == "rejected" { "" } else { "F2 checks result · " })));
                }
                if search_open {
                    lines = vec![Line::from(format!(
                        "Find in {} · Enter searches · PageUp/Down scroll · Esc closes",
                        active.map_or("Status", |c| c.name.as_str())
                    ))];
                    lines.push(Line::from(if search_busy {
                        "Searching…".into()
                    } else {
                        format!("{} matches · {}", search_messages.len(), search_error)
                    }));
                    lines.extend(search_messages.iter().map(|m| {
                        Line::from(format!(
                            "[{}] <{}> {}",
                            local_datetime(m.timestamp, "%Y-%m-%d %H:%M"),
                            m.nickname,
                            m.body
                        ))
                    }));
                }
                let height = columns[1].height.saturating_sub(2);
                let rows: usize = lines
                    .iter()
                    .map(|line| {
                        line.to_string()
                            .split('\n')
                            .map(|part| {
                                crate::text::wrap_line(
                                    part,
                                    columns[1].width.saturating_sub(2) as usize,
                                )
                                .len()
                            })
                            .sum::<usize>()
                    })
                    .sum();
                let scroll = (rows.min(u16::MAX as usize) as u16)
                    .saturating_sub(height)
                    .saturating_sub(if search_open { search_offset } else { offset });
                frame.render_widget(
                    Paragraph::new(lines)
                        .wrap(Wrap { trim: false })
                        .scroll((scroll, 0))
                        .block(
                            Block::default()
                                .borders(Borders::ALL)
                                .title(active.map_or_else(
                                    || "Status".to_string(),
                                    |c| {
                                        if c.kind == gchat_api::ConversationKind::Query {
                                            format!("{} · {}", c.name, c.topic)
                                        } else {
                                            c.name.clone()
                                        }
                                    },
                                )),
                        ),
                    columns[1],
                );
                let members = channel_members(&state, active);
                frame.render_widget(
                    List::new(members.iter().map(|m| ListItem::new(m.nickname.clone())))
                        .block(Block::default().borders(Borders::ALL).title("Nicks")),
                    columns[2],
                );
                draft.secret = state.instance.locked || is_network_invitation(&draft.value);
                let editor = if search_open { &search_draft } else { &draft };
                let shown = editor.display().replace(['\r', '\n'], "↵");
                let prefix: String = shown.chars().take(editor.cursor()).collect();
                let cursor_column =
                    crate::text::display_width(&prefix).min(u16::MAX as usize) as u16;
                let input_scroll =
                    cursor_column.saturating_sub(sections[2].width.saturating_sub(3));
                frame.render_widget(
                    Paragraph::new(shown).scroll((0, input_scroll)).block(
                        Block::default()
                            .borders(Borders::ALL)
                            .title(if search_open {
                                "Find text (256 UTF-8 bytes)"
                            } else if state.instance.locked {
                                "Passphrase"
                            } else if matches!(network.state, gchat_api::NetworkState::InvitationRequired | gchat_api::NetworkState::InvitationExpired) {
                                "Network invitation · paste GCNI1- and press Enter"
                            } else {
                                "Message · Enter sends"
                            }),
                    ),
                    sections[2],
                );
                frame.set_cursor_position((
                    sections[2].x + 1 + cursor_column.saturating_sub(input_scroll),
                    sections[2].y + 1,
                ));
                frame.render_widget(
                    Paragraph::new(
                        if offline.as_ref().is_some_and(|error| !error.retryable()) {
                            "Attachment blocked: reopen/update the selected instance"
                        } else if offline.is_some() {
                            "Reconnecting to selected instance · drafts remain editable"
                        } else if operations.values().any(|scope| scope == &selected) {
                            "This conversation: waiting for instance · drafts remain editable"
                        } else if !operations.is_empty() {
                            "Another conversation is waiting · this input remains available"
                        } else if offset > 0 {
                            "Scrolled back · Ctrl+End latest · Ctrl+F find"
                        } else {
                            notices.last().map_or("", String::as_str)
                        },
                    ),
                    sections[3],
                );
            })
            .map_err(|e| e.to_string())?;
    }
    draft.value.zeroize();
    saved_draft.zeroize();
    for (text, _) in drafts.values_mut() {
        text.value.zeroize();
    }
    watch.abort();
    Ok(())
}
fn format_output(output: &CommandOutput) -> String {
    match output {
        CommandOutput::Help { commands } => commands
            .iter()
            .map(|c| {
                format!(
                    "{} — {}{}",
                    c.usage,
                    c.description,
                    if c.available { "" } else { " (unavailable)" }
                )
            })
            .collect::<Vec<_>>()
            .join("\n"),
        CommandOutput::Directory { channels } => channels
            .iter()
            .map(|c| {
                format!(
                    "{} — {} · /join {}",
                    c.name,
                    if c.joined { "joined" } else { "public" },
                    c.name
                )
            })
            .collect::<Vec<_>>()
            .join("\n"),
        CommandOutput::Invitation {
            channel,
            link,
            expires,
            local_only,
        } => format!(
            "Invitation to #{channel} · expires {} · F4 copies the complete link\n{}{link}",
            local_datetime(*expires, "%Y-%m-%d %H:%M"),
            if *local_only {
                "Reachable only on this computer. Configure a relay before sharing.\n"
            } else {
                ""
            }
        ),
        CommandOutput::Text { title, text } => format!("{title}\n{text}"),
        CommandOutput::Status { text } => text.clone(),
        CommandOutput::Close { .. } => String::new(),
    }
}
fn local_datetime(timestamp: u64, format: &str) -> String {
    i64::try_from(timestamp)
        .ok()
        .and_then(|value| chrono::DateTime::from_timestamp(value, 0))
        .map(|value| {
            value
                .with_timezone(&chrono::Local)
                .format(format)
                .to_string()
        })
        .unwrap_or_else(|| "Unknown time".into())
}
fn submit(conversation: Option<String>, mut text: String) -> Request {
    if let Some((command, arguments)) = text.trim().split_once(char::is_whitespace) {
        if let Some((action, code)) = arguments.trim().split_once(char::is_whitespace) {
            if command.eq_ignore_ascii_case("/network") && action.eq_ignore_ascii_case("join") {
                let code = code.trim().to_string();
                text.zeroize();
                return Request::ImportNetworkInvitation { code };
            }
        }
    }
    let id = rand::random::<[u8; 16]>()
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect();
    Request::Submit {
        operation_id: id,
        conversation,
        text,
    }
}
fn unlock_title(state: &Snapshot) -> &'static str {
    if state.instance.protocol_locked {
        if state.instance.profile_exists {
            "Unlock instance"
        } else {
            "Create instance · choose a passphrase of at least 8 characters"
        }
    } else if state.instance.archive_exists {
        "Unlock chat archive"
    } else {
        "Create chat archive · choose a passphrase of at least 8 characters"
    }
}
fn channel_members<'a>(
    state: &'a Snapshot,
    active: Option<&Conversation>,
) -> &'a [gchat_api::Member] {
    active
        .and_then(|active| {
            state
                .conversations
                .iter()
                .find(|c| c.channel_id == active.channel_id && !c.members.is_empty())
        })
        .map_or(&[], |c| &c.members)
}

fn navigation_path(client: &ChatClient) -> std::path::PathBuf {
    use std::hash::{Hash, Hasher};
    let mut hash = std::collections::hash_map::DefaultHasher::new();
    std::env::var_os("GCHAT_VIEW_ID")
        .or_else(|| std::env::var_os("KITTY_WINDOW_ID"))
        .hash(&mut hash);
    std::fs::read_link("/dev/fd/0").ok().hash(&mut hash);
    client.endpoint().with_file_name(format!(
        "gchat-view-{}-{:x}.json",
        client.instance_id(),
        hash.finish()
    ))
}
fn load_navigation(path: &std::path::Path) -> serde_json::Value {
    std::fs::read(path)
        .ok()
        .filter(|bytes| bytes.len() <= 65536)
        .and_then(|bytes| serde_json::from_slice::<serde_json::Value>(&bytes).ok())
        .filter(|value| value["positions"].is_object())
        .unwrap_or_else(|| serde_json::json!({ "selected": null, "positions": {} }))
}
fn save_navigation(path: &std::path::Path, value: &serde_json::Value) {
    use std::io::Write;
    let temporary = path.with_extension(format!("{}.tmp", rand::random::<u64>()));
    let mut options = std::fs::OpenOptions::new();
    options.write(true).create_new(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.mode(0o600);
    }
    if let Ok(mut file) = options.open(&temporary) {
        if file.write_all(value.to_string().as_bytes()).is_ok() {
            let _ = std::fs::rename(&temporary, path);
        }
    }
    let _ = std::fs::remove_file(temporary);
}

fn retained_submissions(client: &ChatClient) -> Vec<(Request, String)> {
    client
        .pending_operations()
        .unwrap_or_default()
        .into_iter()
        .filter(|h| h.method == "submit")
        .map(|h| {
            (
                Request::Submit {
                    operation_id: h.operation.id.as_str().into(),
                    conversation: None,
                    text: String::new(),
                },
                "outcome_unknown".into(),
            )
        })
        .collect()
}

#[cfg(test)]
mod network_onboarding_tests {
    use super::*;

    #[test]
    fn network_invitation_commands_are_transient_even_with_mixed_case() {
        assert!(
            matches!(submit(None, "/NETWORK  JOIN  GCNI1-fixture".into()),
            Request::ImportNetworkInvitation { code } if code == "GCNI1-fixture")
        );
        assert!(matches!(
            submit(None, "/network status".into()),
            Request::Submit { .. }
        ));
    }

    #[test]
    fn invitation_input_uses_the_network_bound() {
        assert!(input_limit("GCNI1-fixture") >= gchat_api::MAX_NETWORK_INVITATION_BYTES);
        assert_eq!(input_limit("ordinary chat"), gchat_api::MAX_INPUT_BYTES);
        assert!(is_network_invitation("/network join GCNI1-fixture"));
    }
}
