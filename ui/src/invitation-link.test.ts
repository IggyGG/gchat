import { describe, expect, it } from 'vitest';
import { InvitationInbox, invitationLink, validInvitationLink } from './invitation-link';
describe('app invitations', () => {
  it('preserves the complete signed payload, falls back for large invites and rejects URL ambiguity', () => {
    expect(invitationLink('GCI1-test_123')).toBe('gcoms://join#GCI1-test_123');
    expect(invitationLink('GCI1-' + 'a'.repeat(8192))).toBeUndefined();
    for (const url of ['gcoms://evil#GCI1-a', 'gcoms://join?x=y#GCI1-a', 'gcoms://join#GCI1-%61', 'https://join#GCI1-a', 'gcoms://join#GCI1-']) expect(validInvitationLink(url)).toBe(false);
  });
  it('deduplicates cold and warm delivery, bounds pending work and clears on teardown', () => {
    const inbox = new InvitationInbox();
    const urls = Array.from({ length: 6 }, (_, i) => `gcoms://join#GCI1-${i}`);
    inbox.offer([urls[0], urls[0]]); inbox.offer(urls);
    expect(inbox.peek()).toBe(urls[0]);
    for (let i = 0; i < 4; i++) { expect(inbox.peek()).toBe(urls[i]); inbox.consume(); }
    expect(inbox.peek()).toBeUndefined();
    inbox.offer([urls[0]]); expect(inbox.peek()).toBeUndefined();
    inbox.offer([urls[4]]); inbox.clear(); expect(inbox.peek()).toBeUndefined();
  });
});
