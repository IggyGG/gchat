import { describe, expect, it } from 'vitest';
import { MemoryHandles, type Request as RpcRequest, type Transport as RpcTransport } from '@gcoms/rpc';
import { attachRpc } from './rpc-transport';
import { methods } from './rpc-api';
import { API_VERSION, type InstanceInfo } from './api';
const instance: InstanceInfo = { id: 'selected', label: 'selected', bootId: 'boot', locked: false, protocolLocked: false, profileExists: true, archiveExists: true, safetyNumber: 'safety', capabilities: [] };
const legacy = async () => ({ version: API_VERSION, instance_id: instance.id, response: { kind: 'instance' as const, instance } });
function reply(r: RpcRequest, value: unknown) { const { invocation: _, ...binding } = r; return { ...binding, body: { state: 'done', outcome: { kind: 'ok', value } } }; }

describe('chat typed attachment', () => {
  it('recovers a network join without retaining its invitation or issuing another join', async () => {
    const calls: RpcRequest[] = [], handles = new MemoryHandles();
    const network = 'b'.repeat(64);
    const transport: RpcTransport = { destination: '/rpc', limit: 262144, async exchange(r) {
      calls.push(r);
      if (r.method === 'identify') return reply(r, instance);
      if (r.invocation.action === 'call') throw new Error('reply lost');
      return reply(r, { kind: 'result', network, response: { kind: 'applied', conversation: 'channel/a', notice: null } });
    } };
    const client = await attachRpc(legacy, transport, instance.id, handles);
    await expect(client.request({ kind: 'networks', request: { kind: 'join', code: 'GCI1-private-token', nickname: 'private-name', accepted_network: network, operation_id: 'network-join-123456789' } })).rejects.toThrow('reply lost');
    expect(JSON.stringify(handles.list())).not.toMatch(/private-token|private-name/);
    const reopened = await attachRpc(legacy, transport, instance.id, handles);
    await expect(reopened.checkOperation?.('network-join-123456789')).resolves.toMatchObject({ kind: 'networks', response: { network } });
    expect(calls.filter(r => r.method === 'network_operation').map(r => r.invocation.action)).toEqual(['call', 'status']);
    expect(handles.list()).toHaveLength(0);
  });
  it('recovers original handles after reload without retaining text or resubmitting', async () => {
    const calls: RpcRequest[] = []; const handles = new MemoryHandles();
    const transport: RpcTransport = { destination: '/api/gchat-rpc', limit: 16000, async exchange(r) {
      calls.push(r);
      if (r.method === 'identify') return reply(r, instance);
      if (r.invocation.action === 'call') throw new Error('connection lost');
      return reply(r, { kind: 'applied', conversation: 'channel/a', notice: null });
    } };
    const client = await attachRpc(legacy, transport, instance.id, handles);
    const id = 'submission-123456789';
    await expect(client.request({ kind: 'submit', operation_id: id, conversation: 'channel/a', text: 'private message' })).rejects.toThrow('connection lost');
    expect(JSON.stringify(handles.list())).not.toContain('private message');
    const reopened = await attachRpc(legacy, transport, instance.id, handles);
    expect(reopened.pendingOperations?.()[0].operation.id).toBe(id);
    await expect(reopened.checkOperation?.(id)).resolves.toEqual({ kind: 'applied', conversation: 'channel/a', notice: null });
    expect(calls.filter(r => r.method === 'submit').map(r => r.invocation.action)).toEqual(['call', 'status']);
    expect(handles.list()).toHaveLength(0);
  });
  it('uses transient session methods for lifecycle slash commands', async () => {
    const calls: RpcRequest[] = []; const handles = new MemoryHandles();
    const transport: RpcTransport = { destination: '/rpc', limit: 16000, async exchange(r) { calls.push(r); return reply(r, instance); } };
    const client = await attachRpc(legacy, transport, instance.id, handles);
    await client.request({ kind: 'submit', operation_id: 'lock-operation-12345', conversation: null, text: '/lock' });
    expect(calls.at(-1)?.method).toBe('lock');
    expect(calls.at(-1)?.invocation).toEqual({ action: 'call', args: {}, operation: null });
    expect(handles.list()).toHaveLength(0);
  });
  it('generated contracts validate every error and reject wrong result shapes', () => {
    expect(Object.keys(methods)).toHaveLength(17);
    expect(methods.files.args({ request: { action: "list", conversation: null } })).toBe(true);
    expect(methods.files.args({ request: { action: "prepare", id: "share", conversation: "channel", name: "file", size_bytes: "1", path: "/remote/path" } })).toBe(false);
    for (const method of Object.values(methods)) {
      expect(method.error({ code: 'locked', message: 'Unlock this archive' })).toBe(true);
      expect(method.error({ code: 12, message: 'wrong' })).toBe(false);
      expect(method.output(123)).toBe(false);
    }
    expect(methods.history.args({ conversation: 'channel/a', before: null, limit: 65536 })).toBe(false);
    expect(methods.submit.args({ conversation: null, text: 'hello', operation_id: 'injected' })).toBe(false);
    expect(methods.submit.output({ kind: 'applied', conversation: null, notice: null })).toBe(true);
    expect(methods.submit.output({ kind: 'history', page: { messages: [] } })).toBe(false);
  });
  it('rejects a changed service instance and malformed typed response', async () => {
    const changed: RpcTransport = { destination: '/rpc', limit: 16000, async exchange(r) { return { ...reply(r, instance), instance: 'other' }; } };
    await expect(attachRpc(legacy, changed, instance.id)).rejects.toMatchObject({ code: 'protocol' });
    const malformed: RpcTransport = { destination: '/rpc', limit: 16000, async exchange(r) { return reply(r, { id: instance.id }); } };
    await expect(attachRpc(legacy, malformed, instance.id)).rejects.toMatchObject({ code: 'protocol' });
  });
});

it('imports network invitations through a transient session without operation handles', async () => {
  const calls: RpcRequest[] = []; const handles = new MemoryHandles();
  const status = { state: 'connecting', message: 'Connecting' };
  const transport: RpcTransport = { destination: '/rpc', limit: 262144, async exchange(r) {
    calls.push(r); return reply(r, r.method === 'identify' ? instance : status);
  } };
  const client = await attachRpc(legacy, transport, instance.id, handles);
  await client.request({ kind: 'import_network_invitation', code: 'GCNI1-private-fixture' });
  expect(calls.at(-1)?.method).toBe('import_network_invitation');
  expect(calls.at(-1)?.invocation).toMatchObject({ action: 'call', operation: null });
  await client.request({ kind: 'submit', operation_id: 'invite-operation-12345', conversation: 'extension/cmd/remote', text: '/NETWORK join GCNI1-private-fixture' });
  expect(calls.at(-1)?.method).toBe('import_network_invitation');
  expect(handles.list()).toHaveLength(0);
  expect(calls.some(r => r.method === 'submit')).toBe(false);
});

it('keeps simultaneous live sends out of interrupted-operation recovery', async () => {
  let release!: () => void;
  const gate = new Promise<void>(resolve => release = resolve);
  const handles = new MemoryHandles();
  const calls: RpcRequest[] = [];
  const wire: RpcTransport = { destination: '/rpc', limit: 262144, async exchange(r) {
    calls.push(r);
    if (r.method === 'identify') return reply(r, instance);
    await gate;
    return reply(r, { kind: 'applied', conversation: 'channel/a', notice: null });
  } };
  const client = await attachRpc(legacy, wire, instance.id, handles);
  const send = (id: string) => client.request({ kind: 'submit', conversation: 'channel/a', operation_id: id, text: 'same text' });
  const first = send('live-operation-0001'), second = send('live-operation-0002');
  await new Promise(resolve => setTimeout(resolve, 0));
  expect(handles.list()).toHaveLength(2);
  expect(client.pendingOperations?.()).toEqual([]);
  release(); await Promise.all([first, second]);
  expect(handles.list()).toEqual([]);
  expect(calls.filter(r => r.method === 'submit')).toHaveLength(2);
});


it('never coalesces different payloads under the same live operation ID', async () => {
  let release!: () => void;
  const gate = new Promise<void>(resolve => release = resolve);
  const calls: RpcRequest[] = [];
  const transport: RpcTransport = { destination: '/rpc', limit: 262144, async exchange(r) {
    calls.push(r);
    if (r.method === 'identify') return reply(r, instance);
    await gate;
    return reply(r, { kind: 'applied', conversation: 'channel/a', notice: null });
  } };
  const client = await attachRpc(legacy, transport, instance.id, new MemoryHandles());
  const first = client.request({ kind: 'submit', operation_id: 'bound-operation-001', conversation: 'channel/a', text: 'original' });
  await expect(client.request({ kind: 'submit', operation_id: 'bound-operation-001', conversation: 'channel/a', text: 'different' })).rejects.toMatchObject({ code: 'conflict' });
  release(); await first;
  expect(calls.filter(r => r.method === 'submit')).toHaveLength(1);
});
