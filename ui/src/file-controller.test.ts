import { describe, expect, it } from 'vitest';
import type { FileRequest, FileSnapshot, Request } from './api';
import { FileController, emptyFiles } from './file-controller';
import type { FileAccess } from './files';
import type { Transport } from './transport';
const empty: FileSnapshot = { files: [], quota_bytes: '1000000', used_bytes: '0', retention_days: 7 };
function deferred() { let release!: () => void; const promise = new Promise<void>(resolve => release = resolve); return { promise, release }; }
function setup(exchange: FileAccess['exchange']) {
  const requests: FileRequest[] = [];
  const transport: Transport = { async request(request: Request) {
    if (request.kind !== 'files') throw new Error('Unexpected request');
    requests.push(request.request);
    return { kind: 'files', snapshot: empty };
  } };
  let view = emptyFiles();
  const controller = new FileController(transport, 'instance', { exchange, save: async () => '/Downloads/test' }, value => view = value);
  return { controller, requests, view: () => view };
}
const file = () => new File([new Uint8Array(524288)], 'example.bin');
describe('attachment-owned file work', () => {
  it('retains original conversation and one import while presentation changes', async () => {
    const gate = deferred(), entered = deferred(); let pieces = 0;
    const { controller, requests, view } = setup(async () => { pieces++; entered.release(); await gate.promise; return new Uint8Array(); });
    const transfer = controller.upload(file(), 'channel/original');
    await entered.promise;
    // A second presentation cannot start concurrent work or change its destination.
    await controller.upload(file(), 'channel/other');
    expect(view().busy).toBe(true);
    gate.release(); await transfer;
    expect(requests.filter(r => r.action === 'prepare')).toMatchObject([{ conversation: 'channel/original' }]);
    expect(requests.filter(r => r.action === 'commit')).toHaveLength(1);
    expect(pieces).toBe(2); expect(view().busy).toBe(false); controller.stop();
  });
  it('clears private view on lock and never commits an interrupted import', async () => {
    const gate = deferred(), entered = deferred(); let pieces = 0;
    const { controller, requests, view } = setup(async () => { pieces++; entered.release(); await gate.promise; return new Uint8Array(); });
    const transfer = controller.upload(file(), 'channel/original');
    await entered.promise; controller.stop(); gate.release(); await transfer;
    expect(pieces).toBe(1); expect(requests.some(r => r.action === 'commit')).toBe(false);
    expect(view()).toEqual(emptyFiles());
  });
  it('retains failed import identity for explicit resume instead of silently retrying', async () => {
    const { controller, requests, view } = setup(async () => { throw new Error('disk full'); });
    await controller.upload(file(), 'channel/a', 'retained-id');
    expect(requests[0]).toMatchObject({ action: 'prepare', id: 'retained-id' });
    expect(requests.some(r => r.action === 'commit')).toBe(false);
    expect(view().error).toContain('disk full'); expect(view().busy).toBe(false); controller.stop();
  });
});
