import type { Conversation, Message, Snapshot } from './api';
import type { Transport } from './transport';
import { ircFormat } from './irc-format';

export function callsAttention(message: Message, conversation: Conversation): boolean {
  if (message.mine) return false;
  if (message.highlighted) return true;
  const text = ircFormat(message.body).map(segment => segment.text).join('').toLocaleLowerCase();
  const mentions = [...text.matchAll(/(?:^|[\s([{])@([^\s@.,;:!?()[\]{}<>]+)/gu)].map(match => match[1]);
  return conversation.members.filter(member => member.isSelf).some(member => {
    const name = member.nickname.toLocaleLowerCase();
    return !!name && (mentions.includes(name) || text.startsWith(name + ':') || text.startsWith(name + ','));
  });
}

/** Read-only, sequential history inspection, triggered only by changed unread
 * metadata. Never marks read or retains message bodies. Superseded/profile-bound
 * responses cannot set badges in a different view. */
export class UnreadHighlights {
  private stamps = new Map<string, string>();
  private queue = new Map<string, { stamp:string; conversation:Conversation; transport:Transport }>();
  private badges = new Set<string>();
  private busy = false;
  private generation = 0;
  constructor(private changed: (ids: Set<string>) => void) {}
  clear() { this.generation++; this.stamps.clear(); this.queue.clear(); this.badges.clear(); this.changed(new Set()); }
  update(snapshot: Snapshot, transport: Transport) {
    if (snapshot.instance.locked) { this.clear(); return; }
    const available = new Set(snapshot.conversations.map(c => c.id));
    for (const id of this.stamps.keys()) if (!available.has(id)) { this.stamps.delete(id); this.queue.delete(id); this.badges.delete(id); }
    for (const conversation of snapshot.conversations) {
      const { id, unread, lastMessageId, muted } = conversation;
      if (!unread || muted) { this.stamps.delete(id); this.queue.delete(id); this.badges.delete(id); continue; }
      const stamp = JSON.stringify([snapshot.instance.id, snapshot.instance.bootId, lastMessageId, unread]);
      if (this.stamps.get(id) === stamp) continue;
      this.stamps.set(id,stamp); this.queue.set(id,{ stamp, conversation, transport });
    }
    this.changed(new Set(this.badges));
    void this.drain();
  }
  private async drain() {
    if (this.busy) return;
    this.busy = true;
    try {
      while (this.queue.size) {
        const [id, job] = this.queue.entries().next().value!;
        this.queue.delete(id);
        const generation = this.generation;
        const current = () => generation === this.generation && this.stamps.get(id) === job.stamp;
        let remaining = job.conversation.unread, before: string | null = null, found = false;
        const cursors = new Set<string>();
        try {
          while (remaining > 0 && current()) {
            const response = await job.transport.request({ kind:'history', conversation:id, before, limit:200 });
            if (!current()) break;
            if (response.kind !== 'history') throw new Error('History unavailable');
            const incoming = response.page.messages.filter(m => !m.mine).slice(-remaining);
            if (incoming.some(message => callsAttention(message, job.conversation))) { found = true; break; }
            remaining -= incoming.length;
            before = response.page.before;
            if (!before || cursors.has(before)) break;
            cursors.add(before);
          }
          if (current()) { if (found) this.badges.add(id); else this.badges.delete(id); this.changed(new Set(this.badges)); }
        } catch { /* Keep unread counts; a future changed snapshot can retry. */ }
      }
    } finally { this.busy = false; }
  }
}
