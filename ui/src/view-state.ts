import type { Message } from './api';

export interface ConversationView {
  draft: string;
  messages: Message[];
  before: string | null;
  scrollTop: number;
  atBottom: boolean;
}

/** Owned by one mounted attachment. Never writes private text to browser storage. */
export class ConversationViews {
  private views = new Map<string | null, ConversationView>();
  save(id: string | null, view: ConversationView) { this.views.set(id, view); }
  restore(id: string | null): ConversationView {
    return this.views.get(id) ?? { draft: '', messages: [], before: null, scrollTop: 0, atBottom: true };
  }
  clear() { this.views.clear(); }
  retain(ids: string[]) { for (const id of this.views.keys()) if (id && !ids.includes(id)) this.views.delete(id); }
  has(id: string | null) { return this.views.has(id); }
}

export interface NavigationMemory {
  selected: string | null;
  positions: Record<string, { top: number; atBottom: boolean; oldest: string | null }>;
}
/** Non-message viewport metadata only; sessionStorage scopes it to this browser tab. */
export function readNavigation(instance: string): NavigationMemory | undefined {
  try {
    const value = JSON.parse(sessionStorage.getItem(`gchat.navigation.${instance}`) ?? 'null');
    if (value && (typeof value.selected === 'string' || value.selected === null) && value.positions && typeof value.positions === 'object' && !Array.isArray(value.positions)) {
      const positions: NavigationMemory['positions'] = {};
      for (const [key, entry] of Object.entries(value.positions)) {
        const position = entry as NavigationMemory['positions'][string] | null;
        if (position && Number.isFinite(position.top) && position.top >= 0 && typeof position.atBottom === 'boolean' && (position.oldest === null || typeof position.oldest === 'string')) positions[key] = position;
      }
      return { selected: value.selected, positions };
    }
  } catch { /* Storage may be unavailable; in-memory navigation still works. */ }
}
export function writeNavigation(instance: string, value: NavigationMemory) {
  try { sessionStorage.setItem(`gchat.navigation.${instance}`, JSON.stringify(value)); } catch { /* Optional viewport persistence. */ }
}

export function inputError(text: string, limit: number): string {
  const bytes = new TextEncoder().encode(text).length;
  return bytes > limit ? `This input is ${bytes.toLocaleString()} UTF-8 bytes; the limit is ${limit.toLocaleString()}. Shorten it before sending. Nothing has been truncated.` : '';
}

/** Empty Tab and every Shift+Tab navigate normally. Escape dismisses completion. */
export function shouldComplete(event: Pick<KeyboardEvent, 'key' | 'shiftKey' | 'ctrlKey' | 'altKey'>, text: string, open: boolean): boolean {
  return event.key === 'Tab' && !event.shiftKey && !event.ctrlKey && !event.altKey && !!text.trim() && !open;
}
