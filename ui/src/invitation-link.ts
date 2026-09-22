export const JOIN_LINK_PREFIX = 'gcoms://join#';
export const MAX_JOIN_LINK_BYTES = 8192;
export function invitationLink(code: string): string | undefined {
  const link = JOIN_LINK_PREFIX + code;
  return /^GCI1-[A-Za-z0-9_-]+$/.test(code) && link.length <= MAX_JOIN_LINK_BYTES ? link : undefined;
}
export function validInvitationLink(link: string): boolean {
  return link.length <= 174800 && /^gcoms:\/\/join#GCI1-[A-Za-z0-9_-]+$/.test(link);
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
