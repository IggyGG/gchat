//! Pure text helpers: timestamps, display width and line wrapping.

use unicode_width::{UnicodeWidthChar, UnicodeWidthStr};

/// HH:MM (UTC) from a unix timestamp. Local time would need a timezone
/// database; UTC keeps the client dependency-free.
pub fn hhmm(ts_unix: u64) -> String {
    let s = ts_unix % 86_400;
    format!("{:02}:{:02}", s / 3600, (s % 3600) / 60)
}

/// YYYY-MM-DD (UTC) from a unix timestamp (civil-from-days, Howard Hinnant).
pub fn ymd(ts_unix: u64) -> String {
    let days = (ts_unix / 86_400) as i64;
    let z = days + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y };
    format!("{y:04}-{m:02}-{d:02}")
}

/// Terminal columns a string occupies (wide CJK and emoji count as two).
pub fn display_width(s: &str) -> usize {
    UnicodeWidthStr::width(s)
}

fn char_width(c: char) -> usize {
    UnicodeWidthChar::width(c).unwrap_or(0)
}

/// Greedy word wrap by display width; hard-breaks words wider than `width`.
/// Always returns at least one line.
pub fn wrap_line(s: &str, width: usize) -> Vec<String> {
    if width == 0 {
        return vec![String::new()];
    }
    let mut out = Vec::new();
    let mut cur = String::new();
    let mut cur_width = 0usize;
    for word in s.split(' ') {
        let mut w = word;
        loop {
            let wlen = display_width(w);
            let sep = usize::from(!cur.is_empty());
            if cur_width + sep + wlen <= width {
                if sep == 1 {
                    cur.push(' ');
                }
                cur.push_str(w);
                cur_width += sep + wlen;
                break;
            }
            if !cur.is_empty() {
                out.push(std::mem::take(&mut cur));
                cur_width = 0;
            }
            if wlen <= width {
                cur.push_str(w);
                cur_width = wlen;
                break;
            }
            // Take as many chars as fit in `width` columns.
            let mut taken = 0usize;
            let mut bytes = 0usize;
            for c in w.chars() {
                let cw = char_width(c);
                if taken + cw > width && taken > 0 {
                    break;
                }
                taken += cw;
                bytes += c.len_utf8();
            }
            out.push(w[..bytes].to_string());
            w = &w[bytes..];
            if w.is_empty() {
                break;
            }
        }
    }
    out.push(cur);
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hhmm_formats_utc() {
        assert_eq!(hhmm(0), "00:00");
        assert_eq!(hhmm(3_661), "01:01");
        assert_eq!(hhmm(86_399), "23:59");
        assert_eq!(hhmm(86_400 + 3_661), "01:01");
    }

    #[test]
    fn ymd_formats_dates() {
        assert_eq!(ymd(0), "1970-01-01");
        assert_eq!(ymd(951_782_400), "2000-02-29");
        assert_eq!(ymd(1_772_236_800), "2026-02-28");
    }

    #[test]
    fn wrap_basic() {
        assert_eq!(wrap_line("hello world", 11), vec!["hello world"]);
        assert_eq!(wrap_line("hello world", 5), vec!["hello", "world"]);
        assert_eq!(wrap_line("a bb ccc", 3), vec!["a", "bb", "ccc"]);
    }

    #[test]
    fn wrap_hard_breaks_long_words() {
        assert_eq!(wrap_line("abcdefghij", 4), vec!["abcd", "efgh", "ij"]);
        assert_eq!(
            wrap_line("x abcdefghij", 4),
            vec!["x", "abcd", "efgh", "ij"]
        );
    }

    #[test]
    fn wrap_edge_cases() {
        assert_eq!(wrap_line("", 5), vec![""]);
        assert_eq!(wrap_line("abc", 0), vec![""]);
    }

    #[test]
    fn wrap_uses_display_width() {
        // Four CJK chars are eight columns wide.
        assert_eq!(wrap_line("日本語字", 4), vec!["日本", "語字"]);
        assert_eq!(wrap_line("ab 日本", 5), vec!["ab", "日本"]);
        assert_eq!(display_width("🙂x"), 3);
        assert_eq!(wrap_line("🙂🙂🙂", 4), vec!["🙂🙂", "🙂"]);
    }
}

/// IRC styles become terminal spans; incoming escape sequences are never emitted.
pub fn irc_spans(text: &str) -> Vec<ratatui::text::Span<'static>> {
    use ratatui::{
        style::{Color, Modifier, Style},
        text::Span,
    };
    const COLORS: [Color; 16] = [
        Color::White,
        Color::Black,
        Color::Blue,
        Color::Green,
        Color::LightRed,
        Color::Red,
        Color::Magenta,
        Color::Rgb(252, 127, 0),
        Color::Yellow,
        Color::LightGreen,
        Color::Cyan,
        Color::LightCyan,
        Color::LightBlue,
        Color::LightMagenta,
        Color::DarkGray,
        Color::Gray,
    ];
    let mut result = Vec::new();
    let mut style = Style::default();
    let mut buffer = String::new();
    let mut chars = text.chars().peekable();
    fn number(chars: &mut std::iter::Peekable<std::str::Chars<'_>>) -> Option<usize> {
        let mut value = None;
        for _ in 0..2 {
            match chars.peek().and_then(|c| c.to_digit(10)) {
                Some(n) if chars.peek().is_some_and(char::is_ascii_digit) => {
                    value = Some(value.unwrap_or(0) * 10 + n as usize);
                    chars.next();
                }
                _ => break,
            }
        }
        value
    }
    while let Some(c) = chars.next() {
        if matches!(
            c,
            '\u{2}' | '\u{3}' | '\u{f}' | '\u{16}' | '\u{1d}' | '\u{1f}'
        ) {
            if !buffer.is_empty() {
                result.push(Span::styled(std::mem::take(&mut buffer), style));
            }
            match c {
                '\u{f}' => style = Style::default(),
                '\u{3}' => match number(&mut chars) {
                    Some(n) => {
                        style.fg = COLORS.get(n).copied();
                        if chars.peek() == Some(&',') {
                            let mut lookahead = chars.clone();
                            lookahead.next();
                            if lookahead.peek().is_some_and(char::is_ascii_digit) {
                                chars.next();
                                style.bg = number(&mut chars).and_then(|n| COLORS.get(n).copied());
                            }
                        }
                    }
                    None => {
                        style.fg = None;
                        style.bg = None;
                    }
                },
                c => {
                    let flag = match c {
                        '\u{2}' => Modifier::BOLD,
                        '\u{16}' => Modifier::REVERSED,
                        '\u{1d}' => Modifier::ITALIC,
                        _ => Modifier::UNDERLINED,
                    };
                    style = if style.add_modifier.contains(flag) {
                        style.remove_modifier(flag)
                    } else {
                        style.add_modifier(flag)
                    };
                }
            }
        } else if !c.is_control() || matches!(c, '\n' | '\t') {
            buffer.push(c);
        }
    }
    if !buffer.is_empty() {
        result.push(Span::styled(buffer, style));
    }
    result
}

#[cfg(test)]
mod irc_tests {
    use super::*;
    #[test]
    fn styles_are_bounded_and_escapes_removed() {
        use ratatui::style::{Color, Modifier};
        let spans = irc_spans("a\u{2}bold\u{3}04,02red\u{f}plain\u{1b}safe");
        assert_eq!(
            spans.iter().map(|s| s.content.as_ref()).collect::<String>(),
            "aboldredplainsafe"
        );
        assert!(spans[1].style.add_modifier.contains(Modifier::BOLD));
        assert_eq!(spans[2].style.fg, Some(Color::LightRed));
        assert!(spans[3].style.add_modifier.is_empty());
        assert_eq!(
            irc_spans("\u{3}99x\u{3},y")
                .iter()
                .map(|s| s.content.as_ref())
                .collect::<String>(),
            "x,y"
        );
    }
}
