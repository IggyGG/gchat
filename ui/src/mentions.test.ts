import { describe, expect, it } from 'vitest';
import { insertMention, mentionSuggestions } from './mentions';
describe('local mention suggestions', () => {
  it('opens on a bare @ and filters case-insensitively', () => {
    expect(mentionSuggestions('@', 1, ['Iggy', 'Ada'])?.items).toEqual(['Iggy', 'Ada']);
    expect(mentionSuggestions('Hi @a', 5, ['Iggy', 'Ada'])?.items).toEqual(['Ada']);
    expect(mentionSuggestions('name@domain', 11, ['domain'])).toBeNull();
    expect(mentionSuggestions('@nobody', 7, ['Ada'])).toBeNull();
  });
  it('inserts at the caret without losing the rest of the draft', () => {
    const options = mentionSuggestions('Hello @Ad, later', 8, ['Ada'])!;
    expect(insertMention('Hello @Ad, later', options.start, options.end, 'Ada')).toEqual({ text: 'Hello @Ada, later', caret: 10 });
    expect(insertMention('Hi @', 3, 4, 'Ada')).toEqual({ text: 'Hi @Ada ', caret: 8 });
  });
});
