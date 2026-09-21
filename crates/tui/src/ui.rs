//! Rendering. Pure function of `App`; the snapshot tests call `render_to_lines`.

use crate::app::{App, ChannelFocus, RelayState, Screen, StatusKind};
use crate::form::{FieldKind, Form};
use crate::text::{display_width, hhmm, wrap_line, ymd};
use gchat_core::model::HomeItem;
use ratatui::layout::{Constraint, Layout, Position, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph, Wrap};
use ratatui::Frame;

/// Below this many columns panes stack instead of sitting side by side.
pub const NARROW: u16 = 70;

/// Styles, with a monochrome variant that uses only modifiers.
#[derive(Clone, Copy)]
struct Theme {
    mono: bool,
}

impl Theme {
    fn dim(self) -> Style {
        if self.mono {
            Style::default().add_modifier(Modifier::DIM)
        } else {
            Style::default().fg(Color::DarkGray)
        }
    }
    fn accent(self) -> Style {
        if self.mono {
            Style::default().add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::Cyan)
        }
    }
    fn status(self, kind: StatusKind) -> Style {
        match (self.mono, kind) {
            (true, StatusKind::Info) => Style::default(),
            (true, StatusKind::Ok) => Style::default().add_modifier(Modifier::BOLD),
            (true, StatusKind::Warn) => Style::default().add_modifier(Modifier::REVERSED),
            (true, StatusKind::Err) => Style::default()
                .add_modifier(Modifier::REVERSED)
                .add_modifier(Modifier::BOLD),
            (false, StatusKind::Info) => Style::default().fg(Color::Yellow),
            (false, StatusKind::Ok) => Style::default().fg(Color::Green),
            (false, StatusKind::Warn) => Style::default().fg(Color::Magenta),
            (false, StatusKind::Err) => {
                Style::default().fg(Color::Red).add_modifier(Modifier::BOLD)
            }
        }
    }
}

fn theme(app: &App) -> Theme {
    Theme { mono: app.mono }
}

/// Footer height for a hint line at this width (status + wrapped hints).
fn footer_height(hints: &str, width: u16) -> u16 {
    1 + wrap_line(hints, usize::from(width.max(1))).len() as u16
}

fn footer(app: &App, hints: &str, width: u16) -> Paragraph<'static> {
    let t = theme(app);
    // A long status (an error with a URL) is cut with an ellipsis rather
    // than silently clipped; `i` and the outbox carry the full text.
    let max = usize::from(width.max(4));
    let status = if display_width(&app.status) > max {
        let mut cut: String = app.status.chars().take(max.saturating_sub(1)).collect();
        while display_width(&cut) > max.saturating_sub(1) {
            cut.pop();
        }
        cut.push('…');
        cut
    } else {
        app.status.clone()
    };
    let mut lines = vec![Line::from(Span::styled(status, t.status(app.status_kind)))];
    for hint in wrap_line(hints, usize::from(width.max(1))) {
        lines.push(Line::from(Span::styled(hint, t.dim())));
    }
    Paragraph::new(lines)
}

/// Split `area` into a body and a footer sized for `hints`.
fn with_footer(area: Rect, hints: &str) -> (Rect, Rect) {
    let rows = Layout::vertical([
        Constraint::Min(3),
        Constraint::Length(footer_height(hints, area.width)),
    ])
    .split(area);
    (rows[0], rows[1])
}

fn narrow(area: Rect) -> bool {
    area.width < NARROW
}

pub fn draw(frame: &mut Frame, app: &App) {
    let area = frame.area();
    match &app.screen {
        Screen::Unlock(form) | Screen::Form(form) => draw_form(frame, app, form, area),
        Screen::Home => draw_home(frame, app, area),
        Screen::Help => draw_help(frame, app, area),
        Screen::Legacy => draw_legacy(frame, app, area),
        Screen::NewMenu { sel } => draw_menu(frame, app, *sel, area),
        Screen::Info {
            title, body, copy, ..
        } => draw_info(frame, app, title, body, copy.is_some(), area),
        Screen::Channel { id } => draw_channel(frame, app, *id, area),
        Screen::ScopedPm { id } => draw_pm(frame, app, *id, area),
        Screen::Public { descriptor } => draw_public(frame, app, descriptor, area),
    }
}

/// Render at a fixed size and return the rows as trimmed strings.
/// This is the snapshot format: symbols only, no colour.
pub fn render_to_lines(app: &App, width: u16, height: u16) -> Vec<String> {
    use ratatui::backend::TestBackend;
    use ratatui::Terminal;

    let backend = TestBackend::new(width, height);
    let mut terminal = Terminal::new(backend).expect("test backend");
    terminal.draw(|frame| draw(frame, app)).expect("draw");
    let buffer = terminal.backend().buffer();
    let width = usize::from(width);
    buffer
        .content()
        .chunks(width.max(1))
        .map(|row| {
            row.iter()
                .map(|cell| cell.symbol())
                .collect::<String>()
                .trim_end()
                .to_string()
        })
        .collect()
}

fn home_hints(app: &App) -> String {
    let mut hints = String::from("up/down select | enter open | n new | i identity | ? help");
    if app
        .client
        .as_ref()
        .is_some_and(|c| !c.catalog_urls().is_empty())
        || matches!(app.relay, RelayState::Failed(_))
    {
        hints.push_str(" | r refresh");
    }
    hints.push_str(" | q quit");
    hints
}

fn draw_home(frame: &mut Frame, app: &App, area: Rect) {
    let t = theme(app);
    let hints = home_hints(app);
    let (body, foot) = with_footer(area, &hints);
    let items = app.home_items();
    let lines = if items.is_empty() {
        let mut lines = vec![Line::from(Span::styled(
            "no joined or public channels",
            t.dim(),
        ))];
        lines.push(Line::from(""));
        lines.push(Line::from("Press n to create a channel or join one."));
        lines
    } else {
        items
            .iter()
            .enumerate()
            .map(|(index, item)| {
                let (icon, label, count) = match item {
                    HomeItem::Joined(channel) => {
                        ("#", channel.title.clone(), channel.messages.len())
                    }
                    HomeItem::Public(public) => {
                        ("+", format!("{} (public)", public.descriptor.title), 0)
                    }
                    HomeItem::ScopedPm(pm) => {
                        let channel = app
                            .client
                            .as_ref()
                            .and_then(|client| client.channel(pm.id.channel_id))
                            .map_or_else(|| "archived".into(), |channel| channel.title);
                        (
                            "@",
                            format!("{} in #{}", pm.remote_display_name, channel),
                            pm.messages.len(),
                        )
                    }
                };
                let unread = app.is_unread(item);
                let mut spans = vec![
                    Span::styled(format!("{icon} "), t.accent()),
                    Span::styled(
                        label,
                        if unread {
                            Style::default().add_modifier(Modifier::BOLD)
                        } else {
                            Style::default()
                        },
                    ),
                    Span::styled(format!("  {count}"), t.dim()),
                ];
                if unread {
                    spans.push(Span::styled(" ●", t.accent()));
                }
                let line = Line::from(spans);
                if index == app.home_sel {
                    line.style(Style::default().add_modifier(Modifier::REVERSED))
                } else {
                    line
                }
            })
            .collect()
    };
    let catalogs = app
        .client
        .as_ref()
        .map_or(0, |client| client.catalog_urls().len());
    let catalog_line = if catalogs == 0 {
        if narrow(body) {
            "catalogs: none (public channels hidden)".to_string()
        } else {
            "catalogs: none configured (public channels hidden)".to_string()
        }
    } else {
        format!("catalogs: {catalogs}  (r refreshes)")
    };
    let relay_line = match &app.relay {
        RelayState::None => "relay: none (local reachability only)".to_string(),
        RelayState::Ready(label) => format!("relay: {label}"),
        RelayState::Failed(_) => "relay: FAILED (i for details, r to retry)".to_string(),
        RelayState::Daemon => "relay: via daemon".to_string(),
    };
    let list = Paragraph::new(lines).block(Block::bordered().title(" channels and scoped PMs "));
    if narrow(body) {
        let rows = Layout::vertical([Constraint::Min(3), Constraint::Length(5)]).split(body);
        frame.render_widget(list, rows[0]);
        frame.render_widget(
            Paragraph::new(vec![Line::from(catalog_line), Line::from(relay_line)])
                .wrap(Wrap { trim: true })
                .block(Block::bordered().title(" gchat ")),
            rows[1],
        );
    } else {
        let cols = Layout::horizontal([Constraint::Percentage(58), Constraint::Percentage(42)])
            .split(body);
        frame.render_widget(list, cols[0]);
        frame.render_widget(
            Paragraph::new(vec![
                Line::from(Span::styled(
                    "CHANNEL-FIRST",
                    t.accent().add_modifier(Modifier::BOLD),
                )),
                Line::from("People and PMs exist only inside a channel."),
                Line::from(""),
                Line::from("Enter  open selected"),
                Line::from("n      create / join / let in"),
                Line::from("i      identity and safety number"),
                Line::from("?      how it works"),
                Line::from("l      read-only legacy archive"),
                Line::from("s      save now"),
                Line::from("q      quit"),
                Line::from(""),
                Line::from(catalog_line),
                Line::from(relay_line),
            ])
            .wrap(Wrap { trim: true })
            .block(Block::bordered().title(" gchat ")),
            cols[1],
        );
    }
    frame.render_widget(footer(app, &hints, foot.width), foot);
}

fn draw_channel(frame: &mut Frame, app: &App, id: gcoms::sdk::ChannelId, area: Rect) {
    let t = theme(app);
    let hints = if app.channel_focus == ChannelFocus::Members {
        "up/down member | enter PM | i invite | p publish | d remove | tab message | esc back"
    } else {
        "enter send | up/down scroll | tab members | esc back"
    };
    let (body, foot) = with_footer(area, hints);
    let rows = Layout::vertical([Constraint::Min(4), Constraint::Length(3)]).split(body);
    let channel = app.client.as_ref().and_then(|client| client.channel(id));
    let members = app
        .client
        .as_ref()
        .map_or_else(Vec::new, |client| client.members(id));
    let member_lines = if members.is_empty() {
        vec![
            Line::from(Span::styled("no other members yet", t.dim())),
            Line::from(Span::styled("press i to invite", t.dim())),
        ]
    } else {
        members
            .iter()
            .enumerate()
            .map(|(index, member)| {
                let line = Line::from(format!("@{}", member.display_name));
                if index == app.member_sel && app.channel_focus == ChannelFocus::Members {
                    line.style(Style::default().add_modifier(Modifier::REVERSED))
                } else {
                    line
                }
            })
            .collect()
    };
    let members_focused = app.channel_focus == ChannelFocus::Members;
    let members_widget = Paragraph::new(member_lines).block(Block::bordered().title(Span::styled(
        if members_focused {
            " members [FOCUS] "
        } else {
            " members "
        },
        if members_focused {
            t.accent().add_modifier(Modifier::BOLD)
        } else {
            t.dim()
        },
    )));
    let title = channel.as_ref().map_or_else(
        || " channel unavailable ".into(),
        |channel| {
            if narrow(body) {
                format!(" #{} ", channel.title)
            } else {
                format!(
                    " #{} ({}, {}) ",
                    channel.title,
                    visibility_word(channel.visibility),
                    role_word(channel.role)
                )
            }
        },
    );
    let transcript_area = if narrow(body) {
        rows[0]
    } else {
        Layout::horizontal([Constraint::Percentage(32), Constraint::Percentage(68)]).split(rows[0])
            [1]
    };
    if narrow(body) {
        // One pane at a time on phones: whichever has focus.
        if members_focused {
            frame.render_widget(members_widget, rows[0]);
        } else {
            draw_transcript(
                frame,
                app,
                channel.as_ref().map(|c| &c.messages[..]),
                &title,
                rows[0],
            );
        }
    } else {
        let cols = Layout::horizontal([Constraint::Percentage(32), Constraint::Percentage(68)])
            .split(rows[0]);
        frame.render_widget(members_widget, cols[0]);
        draw_transcript(
            frame,
            app,
            channel.as_ref().map(|c| &c.messages[..]),
            &title,
            transcript_area,
        );
    }
    let message_focused = app.channel_focus == ChannelFocus::Message;
    draw_input(
        frame,
        app,
        rows[1],
        if message_focused {
            " message [FOCUS] "
        } else {
            " message "
        },
        if message_focused {
            t.accent().add_modifier(Modifier::BOLD)
        } else {
            t.dim()
        },
        message_focused,
    );
    frame.render_widget(footer(app, hints, foot.width), foot);
}

fn visibility_word(visibility: gcoms::sdk::ChannelVisibility) -> &'static str {
    match visibility {
        gcoms::sdk::ChannelVisibility::Public => "public",
        gcoms::sdk::ChannelVisibility::Private => "private",
    }
}

fn role_word(role: gcoms::sdk::ChannelRole) -> String {
    format!("{role:?}").to_ascii_lowercase()
}

fn draw_transcript(
    frame: &mut Frame,
    app: &App,
    messages: Option<&[gchat_core::model::Message]>,
    title: &str,
    area: Rect,
) {
    let t = theme(app);
    let lines = messages.map_or_else(Vec::new, |messages| {
        message_lines(t, messages, area.width.saturating_sub(2) as usize)
    });
    let scroll = transcript_scroll(lines.len(), area.height, app.scroll);
    frame.render_widget(
        Paragraph::new(lines)
            .block(Block::bordered().title(title.to_string()))
            .scroll((scroll, 0)),
        area,
    );
}

/// A one-line input box with a visible cursor and horizontal scrolling.
fn draw_input(
    frame: &mut Frame,
    app: &App,
    area: Rect,
    title: &str,
    title_style: Style,
    focused: bool,
) {
    let inner_width = area.width.saturating_sub(2).max(1);
    let col = app.input.cursor_col();
    let hscroll = col.saturating_sub(inner_width.saturating_sub(1));
    let title = if app.paste_mode {
        format!("{title}[PASTE] ")
    } else {
        title.to_string()
    };
    frame.render_widget(
        Paragraph::new(app.input.display())
            .scroll((0, hscroll))
            .block(Block::bordered().title(Span::styled(title, title_style))),
        area,
    );
    if focused && area.height >= 3 {
        frame.set_cursor_position(Position::new(area.x + 1 + col - hscroll, area.y + 1));
    }
}

fn draw_pm(frame: &mut Frame, app: &App, id: gchat_core::model::ScopedPmId, area: Rect) {
    let hints = "enter send | up/down scroll | esc back to channel";
    let (body, foot) = with_footer(area, hints);
    let rows = Layout::vertical([Constraint::Min(4), Constraint::Length(3)]).split(body);
    let pm = app.client.as_ref().and_then(|client| client.scoped_pm(id));
    let channel = app
        .client
        .as_ref()
        .and_then(|client| client.channel(id.channel_id))
        .map_or_else(|| "archived channel".into(), |channel| channel.title);
    let title = pm.as_ref().map_or_else(
        || format!(" scoped PM in #{channel} "),
        |pm| format!(" @{} in #{} ", pm.remote_display_name, channel),
    );
    draw_transcript(
        frame,
        app,
        pm.as_ref().map(|pm| &pm.messages[..]),
        &title,
        rows[0],
    );
    let t = theme(app);
    draw_input(
        frame,
        app,
        rows[1],
        " channel-scoped private message ",
        t.accent(),
        true,
    );
    frame.render_widget(footer(app, hints, foot.width), foot);
}

fn message_lines(
    t: Theme,
    messages: &[gchat_core::model::Message],
    width: usize,
) -> Vec<Line<'static>> {
    if messages.is_empty() {
        return vec![Line::from(Span::styled("no messages yet", t.dim()))];
    }
    messages
        .iter()
        .flat_map(|message| {
            wrap_line(
                &format!(
                    "[{}] {}: {}",
                    hhmm(message.ts_unix),
                    if message.mine {
                        "you"
                    } else {
                        &message.sender_name
                    },
                    message.text
                ),
                width.max(1),
            )
            .into_iter()
            .map(move |line| {
                Line::from(Span::styled(
                    line,
                    if message.mine {
                        t.accent()
                    } else {
                        Style::default()
                    },
                ))
            })
        })
        .collect()
}

fn transcript_scroll(lines: usize, area_height: u16, from_bottom: u16) -> u16 {
    let visible = usize::from(area_height.saturating_sub(2));
    let bottom = lines.saturating_sub(visible);
    bottom.saturating_sub(usize::from(from_bottom).min(bottom)) as u16
}

fn activity_words(activity: gcoms::sdk::ActivityBucket) -> &'static str {
    match activity {
        gcoms::sdk::ActivityBucket::Today => "active today",
        gcoms::sdk::ActivityBucket::ThisWeek => "active this week",
        gcoms::sdk::ActivityBucket::Older => "quiet lately",
        gcoms::sdk::ActivityBucket::None => "no recent activity",
    }
}

fn draw_public(
    frame: &mut Frame,
    app: &App,
    descriptor: &gcoms::sdk::PublicChannelDescriptor,
    area: Rect,
) {
    let t = theme(app);
    let hints = "enter join (or retry) | esc back";
    let (body, foot) = with_footer(area, hints);
    let rows = Layout::vertical([Constraint::Min(4), Constraint::Length(3)]).split(body);
    let lines = vec![
        Line::from(Span::styled(
            format!("#{}", descriptor.title),
            t.accent().add_modifier(Modifier::BOLD),
        )),
        Line::from(descriptor.description.clone()),
        Line::from(""),
        Line::from(format!("capacity: {}", descriptor.capacity)),
        Line::from(activity_words(descriptor.activity).to_string()),
        Line::from(format!(
            "listing expires: {} (UTC)",
            ymd(descriptor.expires_at_unix)
        )),
        Line::from(""),
        Line::from("Choose a display name for this channel below and press Enter."),
        Line::from("The join is automatic: your app does the whole exchange for you."),
    ];
    frame.render_widget(
        Paragraph::new(lines)
            .wrap(Wrap { trim: true })
            .block(Block::bordered().title(" signed public channel listing ")),
        rows[0],
    );
    draw_input(frame, app, rows[1], " display name ", t.accent(), true);
    frame.render_widget(footer(app, hints, foot.width), foot);
}

const HELP: &[&str] = &[
    "FIRST CHANNEL",
    "Press n on Home. 'create channel' makes you the owner. To bring a friend in: open the \
     channel, press Tab to focus the member list, and press i to make a one-time invite link; \
     send it to them. They pick New > 'join with invite', paste the link, and their app joins \
     automatically. Keep gchat open until they join. (The 'advanced' New items do the same by \
     hand — a join request and invite code — for a LAN with no relay.)",
    "",
    "COPYING CODES",
    "On any screen that shows a join request or invite code, y copies it and e writes it to your \
     outbox folder (the path is shown). If your terminal cannot paste a long code, press \
     Ctrl-P for paste mode, or type the path of a file containing it.",
    "",
    "PUBLIC CHANNELS",
    "Configured catalogs are queried after unlock and with r. Open a + row, read the signed \
     listing, enter a display name, press Enter. Failed joins can be retried.",
    "",
    "MEMBERS AND PMS",
    "Inside a channel, Tab focuses the member list. Enter opens a PM scoped to that channel; \
     the same person in another channel is intentionally unrelated.",
    "",
    "IDENTITY",
    "i on Home shows your safety number, relay and file locations. Compare safety numbers \
     out-of-band to verify who you are talking to.",
];

fn draw_help(frame: &mut Frame, app: &App, area: Rect) {
    let hints = "up/down scroll | esc back";
    let (body, foot) = with_footer(area, hints);
    frame.render_widget(
        Paragraph::new(
            HELP.iter()
                .map(|line| Line::from(*line))
                .collect::<Vec<_>>(),
        )
        .wrap(Wrap { trim: true })
        .block(Block::bordered().title(" how it works "))
        .scroll((app.scroll, 0)),
        body,
    );
    frame.render_widget(footer(app, hints, foot.width), foot);
}

fn draw_legacy(frame: &mut Frame, app: &App, area: Rect) {
    let hints = "legacy data is never guessed into channels | up/down scroll | esc back";
    let (body, foot) = with_footer(area, hints);
    let legacy = app
        .client
        .as_ref()
        .map(ClientHandleExt::legacy_lines)
        .unwrap_or_default();
    frame.render_widget(
        Paragraph::new(legacy)
            .wrap(Wrap { trim: true })
            .block(Block::bordered().title(" read-only legacy global archive "))
            .scroll((app.scroll, 0)),
        body,
    );
    frame.render_widget(footer(app, hints, foot.width), foot);
}

trait ClientHandleExt {
    fn legacy_lines(&self) -> Vec<Line<'static>>;
}
impl ClientHandleExt for gchat_core::client::ClientHandle {
    fn legacy_lines(&self) -> Vec<Line<'static>> {
        let legacy = self.legacy_archive();
        let mut lines = vec![Line::from(format!(
            "{} contacts, {} conversations",
            legacy.contacts.contacts.len(),
            legacy.conversations.list.len()
        ))];
        for conversation in legacy.conversations.list {
            lines.push(Line::from(format!(
                "{} ({} messages)",
                conversation.key(),
                conversation.messages().len()
            )));
        }
        for channel in self.archived_channels() {
            lines.push(Line::from(format!(
                "archived #{} ({} messages, read-only)",
                channel.title,
                channel.messages.len()
            )));
            for message in channel.messages {
                lines.push(Line::from(format!(
                    "  [{}] {}: {}",
                    hhmm(message.ts_unix),
                    message.sender_name,
                    message.text
                )));
            }
        }
        lines
    }
}

fn draw_menu(frame: &mut Frame, app: &App, selected: usize, area: Rect) {
    let hints = "up/down choose | enter | esc back";
    let (body, foot) = with_footer(area, hints);
    let lines = app
        .new_menu()
        .into_iter()
        .enumerate()
        .map(|(index, (name, help, _))| {
            let line = Line::from(vec![
                Span::raw(format!("{name:<24}")),
                Span::styled(help, theme(app).dim()),
            ]);
            if index == selected {
                line.style(Style::default().add_modifier(Modifier::REVERSED))
            } else {
                line
            }
        })
        .collect::<Vec<_>>();
    frame.render_widget(
        Paragraph::new(lines).block(Block::bordered().title(" new ")),
        body,
    );
    frame.render_widget(footer(app, hints, foot.width), foot);
}

fn draw_form(frame: &mut Frame, app: &App, form: &Form, area: Rect) {
    let t = theme(app);
    let has_toggle = form.fields.iter().any(|field| field.is_toggle());
    let hints = if has_toggle {
        "tab next field | space toggles | enter submit | esc cancel"
    } else if form.back == crate::form::Back::Quit {
        "tab next field | enter submit | esc quit"
    } else {
        "tab next field | enter submit | esc cancel | ctrl-p paste mode"
    };
    let (body, foot) = with_footer(area, hints);
    let inner_width = usize::from(body.width.saturating_sub(2).max(1));
    let mut lines = Vec::new();
    for help in &form.help {
        for wrapped in wrap_line(help, inner_width) {
            lines.push(Line::from(wrapped));
        }
    }
    lines.push(Line::from(""));
    let mut cursor: Option<(u16, u16)> = None;
    for (index, field) in form.fields.iter().enumerate() {
        let focused = index == form.focus;
        let marker = if focused { "> " } else { "  " };
        let prefix = format!("{marker}{}: ", field.label);
        let row = lines.len() as u16;
        match &field.kind {
            FieldKind::Text => {
                let value = field.edit.display();
                let prefix_width = display_width(&prefix);
                let avail = inner_width.saturating_sub(prefix_width).max(1);
                let col = usize::from(field.edit.cursor_col());
                // Keep the cursor visible in long values.
                let start = col.saturating_sub(avail.saturating_sub(1));
                let shown: String = value.chars().skip(start).take(avail).collect();
                lines.push(Line::from(format!("{prefix}{shown}")));
                if focused {
                    cursor = Some(((prefix_width + col - start) as u16, row));
                }
            }
            FieldKind::Toggle { options, index: on } => {
                let mut spans = vec![Span::raw(prefix)];
                for (i, option) in options.iter().enumerate() {
                    if i == *on {
                        spans.push(Span::styled(
                            format!("[{option}]"),
                            t.accent().add_modifier(Modifier::BOLD),
                        ));
                    } else {
                        spans.push(Span::styled(format!(" {option} "), t.dim()));
                    }
                    spans.push(Span::raw(" "));
                }
                lines.push(Line::from(spans));
            }
        }
    }
    let title = if app.paste_mode {
        format!(" {} [PASTE] ", form.title)
    } else {
        format!(" {} ", form.title)
    };
    frame.render_widget(
        Paragraph::new(lines)
            .block(Block::bordered().title(title))
            .scroll((app.scroll, 0)),
        body,
    );
    if let Some((x, y)) = cursor {
        let y = y.saturating_sub(app.scroll);
        if y + 1 < body.height.saturating_sub(1) {
            frame.set_cursor_position(Position::new(
                body.x + 1 + x.min(body.width.saturating_sub(3)),
                body.y + 1 + y,
            ));
        }
    }
    frame.render_widget(footer(app, hints, foot.width), foot);
}

fn draw_info(
    frame: &mut Frame,
    app: &App,
    title: &str,
    body: &[String],
    copyable: bool,
    area: Rect,
) {
    let hints = if copyable {
        "y copy | e export to outbox | up/down scroll | enter continue"
    } else {
        "up/down scroll | enter continue"
    };
    let (area_body, foot) = with_footer(area, hints);
    let inner_width = usize::from(area_body.width.saturating_sub(2).max(1));
    let lines = body
        .iter()
        .flat_map(|line| wrap_line(line, inner_width))
        .map(Line::from)
        .collect::<Vec<_>>();
    let max_scroll = (lines.len() as u16).saturating_sub(area_body.height.saturating_sub(2));
    frame.render_widget(
        Paragraph::new(lines)
            .block(Block::bordered().title(format!(" {title} ")))
            .scroll((app.scroll.min(max_scroll), 0)),
        area_body,
    );
    frame.render_widget(footer(app, hints, foot.width), foot);
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::form::UnlockMode;
    use gchat_core::model::{MemberId, ScopedPmId};
    use std::path::Path;

    fn app() -> App {
        App::new(UnlockMode::UnlockProfile, Path::new("x"), "")
    }

    fn render(app: &App) -> String {
        render_to_lines(app, 110, 20).join("\n")
    }

    #[test]
    fn channel_focus_and_scoped_pm_context_are_visible() {
        let mut app = app();
        app.screen = Screen::Channel {
            id: gcoms::sdk::ChannelId([1; 32]),
        };
        assert!(render(&app).contains("message [FOCUS]"));
        app.channel_focus = ChannelFocus::Members;
        assert!(render(&app).contains("members [FOCUS]"));

        app.screen = Screen::ScopedPm {
            id: ScopedPmId {
                channel_id: gcoms::sdk::ChannelId([1; 32]),
                self_member_id: MemberId([2; 32]),
                remote_member_id: MemberId([3; 32]),
            },
        };
        let rendered = render(&app);
        assert!(rendered.contains("scoped PM in #archived channel"));
        assert!(rendered.contains("channel-scoped private message"));
        assert!(!rendered.contains(" contacts "));
    }

    #[test]
    fn info_wraps_long_base64_at_width() {
        let blob = "A".repeat(300);
        let mut app = app();
        app.screen = Screen::Info {
            title: "key package".into(),
            body: vec!["Send this.".into(), blob.clone()],
            copy: Some(blob),
            export_name: "kp",
            next: Box::new(Screen::Home),
        };
        let lines = render_to_lines(&app, 50, 20);
        let a_rows = lines.iter().filter(|line| line.contains("AAAA")).count();
        assert!(a_rows >= 6, "blob must wrap across rows: {lines:?}");
        assert!(lines.iter().all(|line| display_width(line) <= 50));
        assert!(lines.iter().any(|line| line.contains("e export")));
    }

    #[test]
    fn form_shows_cursor_toggle_and_wraps_help_when_narrow() {
        let mut app = app();
        app.screen = Screen::Form(Form::create_channel());
        let lines = render_to_lines(&app, 50, 20);
        assert!(lines.iter().any(|line| line.contains("[private]")));
        assert!(lines.iter().any(|line| line.contains("> channel:")));
        assert!(lines.iter().all(|line| display_width(line) <= 50));
        let wide = render_to_lines(&app, 100, 20);
        assert!(wide.iter().any(|line| line.contains("space toggles")));
    }

    #[test]
    fn unlock_form_keeps_the_pty_test_strings() {
        let app = App::new(UnlockMode::CreateProfile, Path::new("/tmp/p"), "");
        let rendered = render(&app);
        assert!(rendered.contains("create profile"));
        assert!(rendered.contains("passphrase:"));
        assert!(rendered.contains("NEW identity"));
    }

    #[test]
    fn home_is_readable_at_phone_width() {
        let mut app = app();
        app.screen = Screen::Home;
        app.relay = RelayState::Failed("dns".into());
        let lines = render_to_lines(&app, 50, 20);
        assert!(lines
            .iter()
            .any(|line| line.contains("no joined or public channels")));
        assert!(lines.iter().any(|line| line.contains("relay: FAILED")));
        assert!(lines.iter().all(|line| display_width(line) <= 50));
        assert!(lines.iter().any(|line| line.contains("r refresh")));
    }

    #[test]
    fn long_status_is_cut_with_an_ellipsis() {
        let mut app = app();
        app.screen = Screen::Home;
        app.err("x".repeat(200));
        let lines = render_to_lines(&app, 50, 20);
        let status = lines.iter().find(|line| line.starts_with('x')).unwrap();
        assert!(status.ends_with('…'), "{status}");
        assert!(display_width(status) <= 50);
    }

    #[test]
    fn mono_theme_renders_the_same_symbols() {
        let mut colour = app();
        colour.screen = Screen::Home;
        let mut mono = app();
        mono.screen = Screen::Home;
        mono.mono = true;
        assert_eq!(render(&colour), render(&mono));
    }
}
