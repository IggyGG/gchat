import { describe, expect, it } from 'vitest';
import { crc32, embedInvitationCard, readInvitationCard, readInvitationFile, MAX_CARD_BYTES } from './invitation-card';
import { MAX_NETWORK_INVITATION_BYTES } from './api';
const picture = () => new Uint8Array(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=', 'base64'));
const token = 'GCI1-private_fixture_not_a_real_invitation';
describe('original PNG invitation files', () => {
  it('preserves every byte of the invitation and original picture', () => {
    const png = picture(), card = embedInvitationCard(png, token);
    expect(readInvitationCard(card)).toBe(token);
    expect(card.slice(0, png.length - 12)).toEqual(png.slice(0, -12));
    expect(card.slice(-12)).toEqual(png.slice(-12));
  });
  it('detects corruption and truncation rather than extracting damaged credentials', () => {
    const card = embedInvitationCard(picture(), token);
    const altered = card.slice(); altered[altered.length - 18] ^= 1;
    expect(() => readInvitationCard(altered)).toThrow(/damaged/);
    for (const n of [0, 8, 14, 32, card.length - 1]) expect(() => readInvitationCard(card.slice(0, n))).toThrow();
    const length = card.slice(); new DataView(length.buffer).setUint32(8, 0xffffffff);
    expect(() => readInvitationCard(length)).toThrow(/incomplete/);
  });
  it('rejects pictures whose metadata was removed, and duplicate invitation entries', () => {
    expect(() => readInvitationCard(picture())).toThrow(/original PNG/);
    const card = embedInvitationCard(picture(), token);
    expect(() => embedInvitationCard(card, token)).toThrow(/already contains/);
    const start = picture().length - 12, chunk = card.slice(start, -12);
    const doubled = new Uint8Array(card.length + chunk.length);
    doubled.set(card.slice(0, -12)); doubled.set(chunk, card.length - 12); doubled.set(card.slice(-12), doubled.length - 12);
    expect(() => readInvitationCard(doubled)).toThrow(/more than one/);
  });
  it('enforces file, pixel and invitation limits before decoding artwork', () => {
    expect(() => readInvitationCard(new Uint8Array(MAX_CARD_BYTES + 1))).toThrow(/8 MB/);
    expect(() => embedInvitationCard(picture(), 'x'.repeat(MAX_NETWORK_INVITATION_BYTES + 1))).toThrow(/size limit/);
    const huge = picture(), view = new DataView(huge.buffer);
    view.setUint32(16, 0xffffffff); view.setUint32(29, crc32(huge.subarray(12, 29)));
    expect(() => readInvitationCard(huge)).toThrow(/too large/);
    expect(readInvitationCard(embedInvitationCard(picture(), 'x'.repeat(MAX_NETWORK_INVITATION_BYTES)))).toHaveLength(MAX_NETWORK_INVITATION_BYTES);
  });
  it('refuses trailing data and compressed invitation metadata', () => {
    const card = embedInvitationCard(picture(), token);
    const trailing = new Uint8Array(card.length + 1); trailing.set(card);
    expect(() => readInvitationCard(trailing)).toThrow(/incomplete/);
    const start = picture().length - 12, end = card.length - 12;
    card[start + 8 + 'GChat.Invitation'.length + 1] = 1;
    new DataView(card.buffer).setUint32(end - 4, crc32(card.subarray(start + 4, end - 4)));
    expect(() => readInvitationCard(card)).toThrow(/Unsupported/);
  });
  it('continues reading legacy text files and rejects flattened images', async () => {
    const textFile = { name: 'invitation.txt', type: 'text/plain', size: token.length, text: async () => token } as File;
    expect(await readInvitationFile(textFile)).toBe(token);
    const bytes = new TextEncoder().encode(token);
    const jpeg = { name: 'copy.jpg', type: 'image/jpeg', size: bytes.length, arrayBuffer: async () => bytes.buffer } as File;
    await expect(readInvitationFile(jpeg)).rejects.toThrow(/original PNG/);
  });
});
