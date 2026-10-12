/** The chat theme is dark. Explicit IRC colors stay recognizable whenever they
 * meet text contrast; indistinguishable pairs get a readable foreground. */
export const chatBackground = '#1c1e22';
export const chatInk = '#eef0eb';
function luminance(hex: string): number {
  const channels = [1,3,5].map(offset => {
    const value = Number.parseInt(hex.slice(offset,offset + 2),16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}
export function colorContrast(first: string, second: string): number {
  const a = luminance(first), b = luminance(second);
  return (Math.max(a,b) + 0.05) / (Math.min(a,b) + 0.05);
}
export function readableColor(foreground: string, background: string): string {
  if (colorContrast(foreground,background) >= 4.5) return foreground;
  return colorContrast('#ffffff',background) >= colorContrast('#000000',background) ? '#ffffff' : '#000000';
}
