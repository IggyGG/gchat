import { expect, it } from 'vitest';
import type { Conversation, JoinedNetwork, Request, Response, Snapshot } from './api';
import { NetworkWorkspace } from './network-workspace';
import { encodeFileIo } from './files';
import type { Transport } from './transport';

const primary = 'a'.repeat(64), secondary = 'b'.repeat(64);
const networks: JoinedNetwork[] = [primary, secondary].map((id, i) => ({ id, name: `network-${i}`, fingerprint: id, primary: !i, status: { state: 'connected', message: 'Connected' } }));
const conversation: Conversation = { id: 'channel/same', channelId: 'same', provider: null, kind: 'channel', name: '#same', topic: '', active: true, owner: false, members: [], unread: 0, lastMessageId: null, inputLimitBytes: 12000, commands: [] };
const snapshot: Snapshot = { instance: { id: 'instance', label: 'test', bootId: 'boot', locked: false, protocolLocked: false, profileExists: true, archiveExists: true, safetyNumber: 'test', capabilities: ['networks.v1'] }, revision: '1', conversations: [conversation], commandHistory: [], inputHistory: [], providerErrors: [] };
function setup() {
  const calls: Request[] = [];
  const base: Transport = { async request(request): Promise<Response> {
    calls.push(request);
    if (request.kind === 'snapshot') return { kind: 'snapshot', snapshot };
    if (request.kind === 'lock') return { kind: 'instance', instance: { ...snapshot.instance, locked: true } };
    if (request.kind === 'networks') {
      if (request.request.kind === 'list') return { kind: 'networks', response: { kind: 'list', networks } };
      if (request.request.kind === 'call') {
        const inner = request.request.request;
        const response: Response = inner.kind === 'snapshot' ? { kind: 'snapshot', snapshot }
          : { kind: 'applied', conversation: 'conversation' in inner ? inner.conversation : null, notice: null };
        return { kind: 'networks', response: { kind: 'result', network: request.request.network, response } };
      }
    }
    return { kind: 'applied', conversation: 'conversation' in request ? request.conversation : null, notice: null };
  } };
  const workspace = new NetworkWorkspace(() => base, () => {});
  return { workspace, calls, base };
}

it('keeps identical channel IDs and captured sends distinct while switching networks', async () => {
  const { workspace, calls } = setup();
  const result = await workspace.request({ kind: 'snapshot' });
  expect(result.kind === 'snapshot' && result.snapshot.conversations.map(c => c.id)).toEqual(['channel/same', `network/${secondary}/channel/same`]);
  workspace.select(secondary);
  const captured = workspace.forNetwork(secondary);
  workspace.select(primary);
  await captured.request({ kind: 'submit', operation_id: 'original-operation', conversation: `network/${secondary}/channel/same`, text: 'on the second network' });
  expect(calls.at(-1)).toEqual({ kind: 'networks', request: { kind: 'call', network: secondary, request: { kind: 'submit', operation_id: 'original-operation', conversation: 'channel/same', text: 'on the second network' } } });
  await workspace.request({ kind: 'submit', operation_id: 'other-operation', conversation: 'channel/same', text: 'on the first network' });
  expect(calls.at(-1)?.kind).toBe('submit');
  const before = calls.length;
  await expect(workspace.forNetwork(primary).request({ kind: 'history', conversation: `network/${secondary}/channel/same`, before: null, limit: 20 })).rejects.toThrow('another network');
  expect(calls).toHaveLength(before);
});

it('captures network in binary file IO and export, preserving instance, piece and bytes', async () => {
  const { workspace } = setup(); await workspace.request({ kind: 'snapshot' });
  let frame: ArrayBuffer | undefined, saved = '';
  const access = workspace.fileAccess(secondary, { exchange: async data => { frame = data; return new Uint8Array(); }, save: async id => { saved = id; return '/download/file'; } })!;
  workspace.select(primary);
  const data = new Uint8Array([1, 0, 255]);
  await access.exchange(encodeFileIo({ instance: 'instance', id: 'c'.repeat(32), piece: 7, upload: true }, data));
  const size = new DataView(frame!).getUint16(6), bytes = new Uint8Array(frame!);
  expect(JSON.parse(new TextDecoder().decode(bytes.slice(8, 8 + size)))).toEqual({ instance: 'instance', id: `${secondary}:${'c'.repeat(32)}`, piece: 7, upload: true });
  expect(bytes.slice(8 + size)).toEqual(data);
  await access.save('c'.repeat(32)); expect(saved).toBe(`${secondary}:${'c'.repeat(32)}`);
});

it('never falls back to primary when a previously bound network is locked/unavailable', async () => {
  const { workspace, calls } = setup(); await workspace.request({ kind: 'snapshot' });
  const captured = workspace.forNetwork(secondary);
  await workspace.request({ kind: 'lock' });
  const before = calls.length;
  await expect(captured.request({ kind: 'submit', operation_id: 'never-send', conversation: `network/${secondary}/channel/same`, text: 'secret' })).rejects.toThrow('unavailable');
  expect(calls).toHaveLength(before); expect(workspace.networks).toEqual([]);
});

it('qualifies recovered operation results using the receipt network, not the active selection', async () => {
  const { workspace, base } = setup(); await workspace.request({ kind: 'snapshot' });
  base.checkOperation = async () => ({ kind: 'networks', response: { kind: 'result', network: secondary, response: { kind: 'applied', conversation: 'channel/same', notice: null } } });
  workspace.select(primary);
  await expect(workspace.checkOperation('original')).resolves.toMatchObject({ conversation: `network/${secondary}/channel/same` });
});
