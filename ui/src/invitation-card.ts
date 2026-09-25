import { MAX_NETWORK_INVITATION_BYTES } from './api';

export const MAX_CARD_BYTES = 8 * 1024 * 1024;
const signature = new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10]);
const keyword = 'GChat.Invitation';
const encoder = new TextEncoder();
const decoder = new TextDecoder('utf-8', { fatal: true });
const missing = 'This picture has no invitation data. Ask for the original PNG, sent as a file.';

// PNG CRC covers the type and data. This is corruption detection, not authority;
// the service must still inspect and accept the unchanged invitation.
export function crc32(bytes: Uint8Array): number {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
  }
  return (crc ^ 0xffffffff) >>> 0;
}
function code(value: string): string {
  const trimmed = value.trim();
  if (!trimmed || encoder.encode(trimmed).length > MAX_NETWORK_INVITATION_BYTES) throw new Error('Use a complete invitation within the size limit.');
  return trimmed;
}
function chunks(bytes: Uint8Array): { start: number; end: number; type: string; data: Uint8Array }[] {
  if (bytes.length > MAX_CARD_BYTES) throw new Error('Invitation pictures must be smaller than 8 MB.');
  if (!signature.every((byte, i) => bytes[i] === byte)) throw new Error('Open the original PNG invitation card or a text invitation.');
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const result = [];
  let offset = 8, image = false, ended = false;
  while (offset < bytes.length) {
    if (bytes.length - offset < 12) throw new Error('The invitation picture is incomplete. Ask for the original file.');
    const size = view.getUint32(offset);
    if (size > bytes.length - offset - 12) throw new Error('The invitation picture is incomplete. Ask for the original file.');
    const end = offset + 12 + size;
    const type = decoder.decode(bytes.subarray(offset + 4, offset + 8));
    if (!/^[A-Za-z]{4}$/.test(type) || crc32(bytes.subarray(offset + 4, end - 4)) !== view.getUint32(end - 4)) throw new Error('The invitation picture is damaged. Ask for the original file.');
    const data = bytes.subarray(offset + 8, end - 4);
    if (!result.length) {
      if (type !== 'IHDR' || size !== 13) throw new Error('Invalid invitation picture header.');
      const width = view.getUint32(offset + 8), height = view.getUint32(offset + 12);
      if (!width || !height || width * height > 4 * 1024 * 1024) throw new Error('This invitation picture is too large.');
    } else if (type === 'IHDR') throw new Error('Duplicate picture header.');
    if (type === 'acTL') throw new Error('Use a still PNG invitation card.');
    if (type === 'IDAT') image = true;
    result.push({ start: offset, end, type, data });
    offset = end;
    if (type === 'IEND') { ended = size === 0 && offset === bytes.length; break; }
  }
  if (!ended || !image) throw new Error('The invitation picture is incomplete. Ask for the original file.');
  return result;
}
function payload(data: Uint8Array): string | undefined {
  const separator = data.indexOf(0);
  if (separator < 0 || decoder.decode(data.subarray(0, separator)) !== keyword) return;
  // No compressed data, language tag or translated keyword is emitted or accepted.
  if (data.length < separator + 5 || data.subarray(separator + 1, separator + 5).some(value => value !== 0)) throw new Error('Unsupported invitation picture data. Ask for the original card.');
  return code(decoder.decode(data.subarray(separator + 5)));
}
export function readInvitationCard(bytes: Uint8Array): string {
  let invitation: string | undefined;
  for (const chunk of chunks(bytes)) {
    if (chunk.type !== 'iTXt') continue;
    const found = payload(chunk.data);
    if (found === undefined) continue;
    if (invitation !== undefined) throw new Error('This picture contains more than one invitation.');
    invitation = found;
  }
  if (!invitation) throw new Error(missing);
  return invitation;
}
export function embedInvitationCard(png: Uint8Array, invitation: string): Uint8Array<ArrayBuffer> {
  const parsed = chunks(png);
  if (parsed.some(chunk => chunk.type === 'iTXt' && payload(chunk.data) !== undefined)) throw new Error('This picture already contains an invitation.');
  const text = encoder.encode(`${keyword}\0\0\0\0\0${code(invitation)}`);
  const chunk = new Uint8Array(text.length + 12);
  const view = new DataView(chunk.buffer);
  view.setUint32(0, text.length); chunk.set(encoder.encode('iTXt'), 4); chunk.set(text, 8);
  view.setUint32(chunk.length - 4, crc32(chunk.subarray(4, chunk.length - 4)));
  if (png.length + chunk.length > MAX_CARD_BYTES) throw new Error('Invitation picture exceeds the size limit.');
  const end = parsed.at(-1)!.start;
  const result = new Uint8Array(png.length + chunk.length);
  result.set(png.subarray(0, end)); result.set(chunk, end); result.set(png.subarray(end), end + chunk.length);
  return result;
}
export async function readInvitationFile(file: File): Promise<string> {
  if (file.size > MAX_CARD_BYTES) throw new Error('Invitation files must be smaller than 8 MB.');
  if (/\.txt$/i.test(file.name) && !file.type.startsWith('image/')) {
    if (file.size > MAX_NETWORK_INVITATION_BYTES) throw new Error('This invitation file is too large.');
    return code(await file.text());
  }
  const bytes = new Uint8Array(await file.arrayBuffer());
  if (signature.every((byte, i) => bytes[i] === byte)) return readInvitationCard(bytes);
  if (/\.png$/i.test(file.name) || file.type.startsWith('image/')) throw new Error(missing);
  return code(decoder.decode(bytes));
}

export async function renderInvitationCard(invitation: string, channel: string, expires: number, mark: SVGElement): Promise<Uint8Array<ArrayBuffer>> {
  const canvas = document.createElement('canvas'); canvas.width = 1200; canvas.height = 800;
  const ctx = canvas.getContext('2d'); if (!ctx) throw new Error('Picture export is unavailable. Save the text invitation instead.');
  ctx.fillStyle = '#1c1e22'; ctx.fillRect(0, 0, 1200, 800);
  ctx.strokeStyle = '#46534d'; ctx.lineWidth = 2; ctx.strokeRect(40, 40, 1120, 720);
  ctx.fillStyle = '#b8d9c4'; ctx.font = '24px monospace'; ctx.fillText('GChat.', 88, 116);
  const svg = mark.cloneNode(true) as SVGElement;
  svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg'); svg.setAttribute('width', '128'); svg.setAttribute('height', '128');
  const picture = new Image();
  picture.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(new XMLSerializer().serializeToString(svg))}`;
  await picture.decode(); ctx.imageSmoothingEnabled = false; ctx.drawImage(picture, 968, 76, 128, 128);
  ctx.fillStyle = '#eef0eb'; ctx.font = '52px sans-serif'; ctx.fillText('You’re invited.', 88, 290);
  ctx.fillStyle = '#b8d9c4'; ctx.font = '36px monospace';
  const name = `#${channel.replace(/^#/, '')}`;
  let visible = name;
  while (ctx.measureText(visible).width > 970 && visible.length > 1) visible = Array.from(visible).slice(0, -1).join('');
  if (visible !== name) visible = Array.from(visible).slice(0, -1).join('') + '…';
  ctx.fillText(visible, 88, 366);
  ctx.fillStyle = '#aeb7b1'; ctx.font = '24px sans-serif'; ctx.fillText('A place for your people.', 88, 426);
  ctx.strokeStyle = '#46534d'; ctx.beginPath(); ctx.moveTo(88, 536); ctx.lineTo(1112, 536); ctx.stroke();
  ctx.font = '21px sans-serif'; ctx.fillText('Open this original PNG in GChat to review and join.', 88, 591);
  ctx.fillText('Share privately as a file. Screenshots lose the invitation.', 88, 630);
  ctx.fillStyle = '#b8d9c4'; ctx.font = '19px monospace';
  ctx.fillText(`Channel invitation expires ${new Date(expires * 1000).toLocaleString()}`, 88, 709);
  const blob = await new Promise<Blob>((resolve, reject) => canvas.toBlob(value => value ? resolve(value) : reject(new Error('Could not create invitation picture.')), 'image/png'));
  return embedInvitationCard(new Uint8Array(await blob.arrayBuffer()), invitation);
}
