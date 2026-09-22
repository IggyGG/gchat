export interface FileAccess {
  exchange(frame: ArrayBuffer): Promise<Uint8Array>;
  save(id: string): Promise<string>;
  saveInvitation?(invitation: string): Promise<string | null>;
}
export function encodeFileIo(header: { instance: string; id: string; piece: number; upload: boolean }, bytes = new Uint8Array()): ArrayBuffer {
  const encoded = new TextEncoder().encode(JSON.stringify(header));
  if (encoded.length > 512 || bytes.length > 262144 || !Number.isInteger(header.piece) || header.piece < 0 || header.piece > 0xffffffff) throw new Error('File frame exceeds bounds');
  const frame = new Uint8Array(8 + encoded.length + bytes.length);
  frame.set(new TextEncoder().encode('GCFIO1'));
  new DataView(frame.buffer).setUint16(6, encoded.length);
  frame.set(encoded, 8); frame.set(bytes, 8 + encoded.length);
  return frame.buffer;
}
