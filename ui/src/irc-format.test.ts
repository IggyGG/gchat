import { describe, expect, it } from 'vitest';
import { ircFormat, formatStyle } from './irc-format';
describe('classic IRC formatting', () => {
  it('toggles combined styles and resets without changing text', () => {
    const parts = ircFormat('plain \x02bold\x1ditalic\x1funder\x0f reset');
    expect(parts.map(p => p.text).join('')).toBe('plain bolditalicunder reset');
    expect(parts[3].format).toMatchObject({ bold: true, italic: true, underline: true });
    expect(parts[4].format).toEqual({ bold: false, italic: false, underline: false, inverse: false });
  });
  it('bounds colour codes and preserves literal HTML as text', () => {
    const parts = ircFormat('\x0304,02<script>x</script>\x0399out\x03,comma');
    expect(formatStyle(parts[0].format)).toBe('color:#ff0000;background-color:#00007f;');
    expect(parts[0].text).toBe('<script>x</script>');
    expect(parts[1].format.foreground).toBeUndefined();
    expect(parts[2].text).toBe(',comma');
    expect(parts[2].format.background).toBeUndefined();
  });
  it('does not pass control bytes to renderers', () => {
    expect(ircFormat('a\x1bb\x00c').map(p => p.text).join('')).toBe('abc');
    expect(formatStyle(ircFormat('\x16inverse')[0].format)).toContain('var(--bg)');
  });
});
