import { describe, expect, it } from 'vitest';
import { MAX_INPUT_BYTES } from './api';
import { ConversationViews, inputError, shouldComplete } from './view-state';

describe('attachment-local conversation state', () => {
  it('keeps different destinations and attachments separate and clears on lock', () => {
    const a = new ConversationViews(), b = new ConversationViews();
    a.save('channel/a', { ...a.restore('channel/a'), draft: 'private draft A', scrollTop: 240, atBottom: false });
    a.save('channel/b', { ...a.restore('channel/b'), draft: 'draft B' });
    expect(a.restore('channel/a')).toMatchObject({ draft: 'private draft A', scrollTop: 240, atBottom: false });
    expect(a.restore('channel/b').draft).toBe('draft B');
    expect(b.restore('channel/a').draft).toBe('');
    a.clear();
    expect(a.restore('channel/a').draft).toBe('');
  });
});

describe('full input and keyboard escape', () => {
  it('accepts the observed invitation size and measures UTF-8 instead of UTF-16', () => {
    expect(inputError(`/join ${'x'.repeat(9106)} mac-test`, MAX_INPUT_BYTES)).toBe('');
    expect(inputError('🦀'.repeat(3000), MAX_INPUT_BYTES)).toBe('');
    expect(inputError('🦀'.repeat(3001), MAX_INPUT_BYTES)).toContain('12,004');
  });
  it('lets empty Tab, Shift+Tab and Tab with suggestions leave the composer', () => {
    const tab = { key: 'Tab', shiftKey: false, ctrlKey: false, altKey: false };
    expect(shouldComplete(tab, '', false)).toBe(false);
    expect(shouldComplete({ ...tab, shiftKey: true }, '/query', false)).toBe(false);
    expect(shouldComplete(tab, '/query', true)).toBe(false);
    expect(shouldComplete(tab, '/query', false)).toBe(true);
  });
});
