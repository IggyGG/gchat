/** Classic IRC presentation codes, rendered as text and bounded styles, never HTML. */
export interface Format { bold: boolean; italic: boolean; underline: boolean; inverse: boolean; foreground?: string; background?: string }
export interface Segment { text: string; format: Format }
const palette = ['#ffffff','#000000','#00007f','#009300','#ff0000','#7f0000','#9c009c','#fc7f00','#ffff00','#00fc00','#009393','#00ffff','#0000fc','#ff00ff','#7f7f7f','#d2d2d2'];
const plain = (): Format => ({ bold: false, italic: false, underline: false, inverse: false });
export function ircFormat(text: string): Segment[] {
  const result: Segment[] = []; let format = plain(); let buffer = '';
  const flush = () => { if (buffer) { result.push({ text: buffer, format: { ...format } }); buffer = ''; } };
  for (let i = 0; i < text.length; i++) {
    const code = text.charCodeAt(i);
    if ([2,3,15,22,29,31].includes(code)) {
      flush();
      if (code === 2) format.bold = !format.bold;
      else if (code === 29) format.italic = !format.italic;
      else if (code === 31) format.underline = !format.underline;
      else if (code === 22) format.inverse = !format.inverse;
      else if (code === 15) format = plain();
      else {
        const match = /^(\d{1,2})(?:,(\d{1,2}))?/.exec(text.slice(i + 1));
        if (match) { format.foreground = palette[Number(match[1])]; if (match[2] !== undefined) format.background = palette[Number(match[2])]; i += match[0].length; }
        else { delete format.foreground; delete format.background; }
      }
    } else if ((code >= 32 && (code < 127 || code > 159)) || code === 9 || code === 10) buffer += text[i];
    // Unsupported control bytes, including terminal escapes, are not displayed.
  }
  flush(); return result;
}
export function formatStyle(format: Format): string {
  const foreground = format.inverse ? (format.background ?? 'var(--bg)') : format.foreground;
  const background = format.inverse ? (format.foreground ?? 'var(--text)') : format.background;
  return `${foreground ? `color:${foreground};` : ''}${background ? `background-color:${background};` : ''}`;
}
