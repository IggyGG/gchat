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
