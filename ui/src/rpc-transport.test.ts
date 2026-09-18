import { describe, expect, it } from 'vitest';
import { MemoryHandles, type Request as RpcRequest, type Transport as RpcTransport } from '@gcoms/rpc';
import { attachRpc } from './rpc-transport';
import { methods } from './rpc-api';
import { API_VERSION, type InstanceInfo } from './api';
const instance: InstanceInfo = { id: 'selected', label: 'selected', bootId: 'boot', locked: false, protocolLocked: false, profileExists: true, archiveExists: true, safetyNumber: 'safety', capabilities: [] };
const legacy = async () => ({ version: API_VERSION, instance_id: instance.id, response: { kind: 'instance' as const, instance } });
function reply(r: RpcRequest, value: unknown) { const { invocation: _, ...binding } = r; return { ...binding, body: { state: 'done', outcome: { kind: 'ok', value } } }; }

describe('chat typed attachment', () => {
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
    expect(Object.keys(methods)).toHaveLength(14);
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
