import { describe, expect, it } from 'vitest';
import { encodeFileIo } from './files';
describe('native file boundary', () => {
  it('keeps binary chunks outside the JSON header and pins the instance', () => {
    const payload = new Uint8Array([0, 255, 34, 10]);
    const frame = new Uint8Array(encodeFileIo({ instance: 'selected', id: 'handle', piece: 7, upload: true }, payload));
    expect(new TextDecoder().decode(frame.slice(0, 6))).toBe('GCFIO1');
    const n = new DataView(frame.buffer).getUint16(6);
    expect(JSON.parse(new TextDecoder().decode(frame.slice(8, 8 + n)))).toEqual({ instance: 'selected', id: 'handle', piece: 7, upload: true });
    expect(frame.slice(8 + n)).toEqual(payload);
  });
  it('refuses oversized chunks and invalid indices before native dispatch', () => {
    const header = { instance: 'selected', id: 'handle', piece: 0, upload: true };
    expect(() => encodeFileIo(header, new Uint8Array(262145))).toThrow();
    for (const piece of [-1, 0.5, 0x100000000]) expect(() => encodeFileIo({ ...header, piece })).toThrow();
    expect(() => encodeFileIo({ ...header, instance: 'x'.repeat(513) })).toThrow();
  });
});
