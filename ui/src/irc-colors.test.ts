import { expect, it } from 'vitest';
import { chatBackground, colorContrast, readableColor } from './irc-colors';

it('keeps explicit IRC text legible across every classic color pair', () => {
  const colors = ['#ffffff','#000000','#00007f','#009300','#ff0000','#7f0000','#9c009c','#fc7f00','#ffff00','#00fc00','#009393','#00ffff','#0000fc','#ff00ff','#7f7f7f','#d2d2d2'];
  for (const background of [...colors,chatBackground]) for (const foreground of colors) {
    expect(colorContrast(readableColor(foreground,background),background)).toBeGreaterThanOrEqual(4.5);
  }
  expect(readableColor('#ffffff','#000000')).toBe('#ffffff');
  expect(readableColor('#000000','#ffffff')).toBe('#000000');
  expect(readableColor('#000000',chatBackground)).toBe('#ffffff');
});
