export const JOIN_LINK_PREFIX = 'gcoms://join#';
export const MAX_JOIN_LINK_BYTES = 8192;
const MAX_COMPACT_LINK_BYTES = 2048;
export function invitationLink(code: string): string | undefined {
  const raw = code.startsWith(JOIN_LINK_PREFIX) ? code.slice(JOIN_LINK_PREFIX.length) : code;
  const link = JOIN_LINK_PREFIX + raw;
  const limit = raw.startsWith('GCIR1-') ? MAX_COMPACT_LINK_BYTES : MAX_JOIN_LINK_BYTES;
  return /^(GCI1|GCIR1)-[A-Za-z0-9_-]+$/.test(raw) && link.length <= limit ? link : undefined;
}
export function validInvitationLink(link: string): boolean {
  const limit = link.startsWith(JOIN_LINK_PREFIX+'GCIR1-') ? MAX_COMPACT_LINK_BYTES : 174800;
  return link.length <= limit && /^gcoms:\/\/join#(?:GCI1|GCIR1)-[A-Za-z0-9_-]+$/.test(link);
}
/** Memory only, bounded, and deduplicated across cold + warm OS notifications. */
export class InvitationInbox {
  private seen = new Set<string>();
  private pending: string[] = [];
  offer(urls: string[]) {
    for (const url of urls) {
      if (!validInvitationLink(url) || this.seen.has(url) || this.pending.length >= 4) continue;
      this.seen.add(url); this.pending.push(url);
      if (this.seen.size > 32) this.seen.delete(this.seen.values().next().value!);
    }
  }
  peek() { return this.pending[0]; }
  consume() { this.pending.shift(); }
  clear() { this.pending = []; }
}
