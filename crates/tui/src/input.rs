//! Single-line text input with a cursor, paste sanitizing and a hard size cap.

use crate::text::display_width;

/// Hard cap on any single input field. Welcomes grow with the roster (a
/// three-member channel already produces ~11 KB of base64), so the cap is
/// well above what a large channel needs; it only guards against runaway
/// paste, not real payloads.
pub const MAX_INPUT_CHARS: usize = 256 * 1024;

#[derive(Clone, Debug, Default)]
pub struct LineEdit {
    pub value: String,
    /// Insertion point as a char index. Tests may set `value` directly, so
    /// every accessor clamps this to the current length.
    pub cursor: usize,
    /// Render as `*` (passphrases).
    pub secret: bool,
    /// Whitespace is never part of the value (base64 blobs); otherwise
    /// pasted newlines become spaces.
    pub compact: bool,
}

impl LineEdit {
    pub fn new(secret: bool, compact: bool) -> Self {
        LineEdit {
            value: String::new(),
            cursor: 0,
            secret,
            compact,
        }
    }

    fn len(&self) -> usize {
        self.value.chars().count()
    }

    /// Cursor as a char index, clamped to the value.
    pub fn cursor(&self) -> usize {
        self.cursor.min(self.len())
    }

    fn byte_at(&self, char_index: usize) -> usize {
        self.value
            .char_indices()
            .nth(char_index)
            .map_or(self.value.len(), |(index, _)| index)
    }

    fn insert_char(&mut self, c: char) -> bool {
        // Fast reject: each char is at least one byte, so once the byte length
        // reaches the cap the char length has too — this avoids an O(n) char
        // count on the hot path. Only near the cap do we count exactly.
        if self.value.len() >= MAX_INPUT_CHARS && self.len() >= MAX_INPUT_CHARS {
            return false;
        }
        // Append fast path: a char cursor at or past the byte length is at the
        // end of the string (char count <= byte count), so we can push without
        // an O(n) scan to the cursor or a recount. This keeps typing/pasting
        // into a large field O(1) per char instead of O(n). (cursor() clamps on
        // read, so an over-large cursor from a direct write stays harmless.)
        if self.cursor >= self.value.len() {
            self.value.push(c);
            self.cursor += 1;
            return true;
        }
        let at = self.cursor();
        let byte = self.byte_at(at);
        self.value.insert(byte, c);
        self.cursor = at + 1;
        true
    }

    pub fn push(&mut self, c: char) {
        if c.is_control() || (self.compact && c.is_whitespace()) {
            return;
        }
        self.insert_char(c);
    }

    pub fn paste(&mut self, raw: &str) {
        for c in raw.chars() {
            let c = if self.compact {
                if c.is_whitespace() || c.is_control() {
                    continue;
                }
                c
            } else if c == '\n' || c == '\r' {
                ' '
            } else if c.is_control() {
                continue;
            } else {
                c
            };
            if !self.insert_char(c) {
                return;
            }
        }
    }

    /// Service input preserves exact admitted text. The caller validates UTF-8 byte limits.
    pub fn insert_exact(&mut self, text: &str) {
        let at = self.cursor();
        self.value.insert_str(self.byte_at(at), text);
        self.cursor = at + text.chars().count();
    }

    /// Replace the whole value and put the cursor at the end.
    pub fn set(&mut self, value: String) {
        self.value = value;
        self.cursor = self.len();
    }

    /// Move the value out, leaving the field empty.
    pub fn take(&mut self) -> String {
        self.cursor = 0;
        std::mem::take(&mut self.value)
    }

    pub fn backspace(&mut self) {
        let at = self.cursor();
        if at == 0 {
            return;
        }
        let start = self.byte_at(at - 1);
        let end = self.byte_at(at);
        self.value.replace_range(start..end, "");
        self.cursor = at - 1;
    }

    pub fn delete(&mut self) {
        let at = self.cursor();
        if at >= self.len() {
            return;
        }
        let start = self.byte_at(at);
        let end = self.byte_at(at + 1);
        self.value.replace_range(start..end, "");
        self.cursor = at;
    }

    pub fn left(&mut self) {
        self.cursor = self.cursor().saturating_sub(1);
    }

    pub fn right(&mut self) {
        self.cursor = (self.cursor() + 1).min(self.len());
    }

    pub fn home(&mut self) {
        self.cursor = 0;
    }

    pub fn end(&mut self) {
        self.cursor = self.len();
    }

    pub fn clear(&mut self) {
        self.value.clear();
        self.cursor = 0;
    }

    /// Delete the word before the cursor (and the spaces after it).
    pub fn delete_word(&mut self) {
        let at = self.cursor();
        let head: String = self.value.chars().take(at).collect();
        let tail: String = self.value.chars().skip(at).collect();
        let mut head = head;
        while head.ends_with(' ') {
            head.pop();
        }
        while let Some(c) = head.chars().last() {
            if c == ' ' {
                break;
            }
            head.pop();
        }
        self.cursor = head.chars().count();
        self.value = head + &tail;
    }

    pub fn is_empty(&self) -> bool {
        self.value.trim().is_empty()
    }

    pub fn display(&self) -> String {
        if self.secret {
            "*".repeat(self.len())
        } else {
            self.value.clone()
        }
    }

    /// Column of the cursor inside `display()`.
    pub fn cursor_col(&self) -> u16 {
        let at = self.cursor();
        if self.secret {
            return at.min(u16::MAX as usize) as u16;
        }
        let head: String = self.value.chars().take(at).collect();
        display_width(&head).min(u16::MAX as usize) as u16
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn push_ignores_control_chars() {
        let mut e = LineEdit::default();
        e.push('a');
        e.push('\x07');
        e.push('b');
        assert_eq!(e.value, "ab");
    }

    #[test]
    fn cap_is_enforced() {
        let mut e = LineEdit::default();
        for _ in 0..MAX_INPUT_CHARS + 100 {
            e.push('x');
        }
        assert_eq!(e.value.chars().count(), MAX_INPUT_CHARS);
    }

    #[test]
    fn compact_paste_strips_whitespace() {
        let mut e = LineEdit::new(false, true);
        e.paste("QUJD\nREVG \tMTIz");
        assert_eq!(e.value, "QUJDREVGMTIz");
        e.push(' ');
        assert_eq!(e.value, "QUJDREVGMTIz");
    }

    #[test]
    fn normal_paste_turns_newlines_into_spaces() {
        let mut e = LineEdit::default();
        e.paste("hello\nworld\rs");
        assert_eq!(e.value, "hello world s");
    }

    #[test]
    fn paste_respects_cap() {
        let mut e = LineEdit::default();
        let big = "y".repeat(MAX_INPUT_CHARS * 2);
        e.paste(&big);
        assert_eq!(e.value.chars().count(), MAX_INPUT_CHARS);
    }

    #[test]
    fn multibyte_append_keeps_order_and_cursor() {
        // The O(1) append fast path keys off byte length vs char cursor; make
        // sure multibyte content still appends in order with a correct cursor.
        let mut e = LineEdit::default();
        for c in "aé本z".chars() {
            e.push(c);
        }
        assert_eq!(e.value, "aé本z");
        assert_eq!(e.cursor(), 4);
        // Inserting in the middle after multibyte content still lands right.
        e.home();
        e.right();
        e.push('X');
        assert_eq!(e.value, "aXé本z");
    }

    #[test]
    fn secret_display_masks() {
        let mut e = LineEdit::new(true, false);
        e.paste("hunter2");
        assert_eq!(e.display(), "*******");
        assert_eq!(e.value, "hunter2");
        assert_eq!(e.cursor_col(), 7);
    }

    #[test]
    fn delete_word_and_backspace() {
        let mut e = LineEdit::default();
        e.paste("foo bar  ");
        e.delete_word();
        assert_eq!(e.value, "foo ");
        e.backspace();
        e.delete_word();
        assert_eq!(e.value, "");
        e.backspace(); // no panic on empty
        assert_eq!(e.value, "");
    }

    #[test]
    fn cursor_insert_delete_home_end() {
        let mut e = LineEdit::default();
        e.paste("hllo");
        e.home();
        e.right();
        e.push('e');
        assert_eq!(e.value, "hello");
        assert_eq!(e.cursor_col(), 2);
        e.end();
        e.left();
        e.delete();
        assert_eq!(e.value, "hell");
        e.home();
        e.delete();
        assert_eq!(e.value, "ell");
        e.backspace(); // at start: no-op
        assert_eq!(e.value, "ell");
        // Tests may set the value directly; the cursor clamps.
        e.value = "ab".into();
        e.cursor = 99;
        e.push('c');
        assert_eq!(e.value, "abc");
        e.set("日本".into());
        assert_eq!(e.cursor_col(), 4);
        e.left();
        e.delete_word();
        assert_eq!(e.value, "本");
    }
}
