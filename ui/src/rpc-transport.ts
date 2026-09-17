import { BrowserHandles, MemoryHandles, RpcClient, RpcError, ServiceError, type HandleStore, type OperationHandle, type Transport as RpcTransport } from '@gcoms/rpc';
import { createChatClient, methods, SERVICE, SERVICE_VERSION, type ChatError as DomainError } from './rpc-api';
import { attach, ChatError, type Exchange, type Transport } from './transport';
import type { Request, Response } from './api';

export { httpTransport } from '@gcoms/rpc';
export type { Transport as RpcTransport } from '@gcoms/rpc';

function error(failure: unknown): ChatError {
  if (failure instanceof ServiceError) { const detail = failure.detail as DomainError; return new ChatError(detail.code, detail.message); }
  if (failure instanceof RpcError) return new ChatError(failure.code === 'unauthorized' ? 'locked' : failure.code, failure.message);
  return failure instanceof ChatError ? failure : new ChatError('transport', failure instanceof Error ? failure.message : String(failure));
}
function browserHandles(): HandleStore {
  if (typeof window === 'undefined') return new MemoryHandles();
  // Access storage only when retaining/recovering an operation; queries remain
  // usable if the browser blocks storage. Mutation retention must succeed.
  const store = () => new BrowserHandles(window.localStorage, 'gchat:rpc:handle:v1:');
  return { retain: h => store().retain(h), list: () => store().list(), forget: h => store().forget(h) };
}

/** v2 identify selects the instance; all subsequent calls use typed RPC. */
export async function attachRpc(legacy: Exchange, transport: RpcTransport, expectedInstance?: string, handles = browserHandles()): Promise<Transport> {
  const compatibility = await attach(legacy, expectedInstance);
  const hello = await compatibility.request({ kind: 'identify' });
  if (hello.kind !== 'instance') throw new ChatError('protocol', 'Invalid instance handshake');
  const rpc = new RpcClient(transport, hello.instance.id, SERVICE, SERVICE_VERSION, handles);
  const client = createChatClient(rpc);
  try {
    const instance = await client.identify({});
    if (instance.id !== hello.instance.id) throw new ChatError('instance', 'Selected instance changed');
  } catch (failure) { throw error(failure); }
  const pendingOperations = () => handles.list().filter(h => h.destination === transport.destination && h.instance === rpc.instance && h.service === SERVICE && h.version === SERVICE_VERSION);
  const find = (id: string) => pendingOperations().find(h => h.operation.id === id);
  const forget = (h: OperationHandle) => { try { handles.forget(h); } catch { /* A stale opaque handle is safe to check again. */ } };
  const checkOperation = async (id: string): Promise<Response> => {
    const h = find(id);
    if (!h) throw new ChatError('unavailable', 'No retained operation with this ID');
    try {
      if (h.method === 'submit') {
        const result = await rpc.resume(methods.submit, h); forget(h); return result;
      }
      if (h.method === 'mark_read') {
        const result = await rpc.resume(methods.mark_read, h); forget(h); return { kind: 'applied', ...result };
      }
      throw new ChatError('protocol', 'Unknown saved operation method');
    } catch (failure) { throw error(failure); }
  };
  const request = async (request: Request): Promise<Response> => {
    try {
      switch (request.kind) {
        case 'identify': return { kind: 'instance', instance: await client.identify({}) };
        case 'snapshot': return { kind: 'snapshot', snapshot: await client.snapshot({}) };
        case 'unlock': return { kind: 'snapshot', snapshot: await client.unlock({ passphrase: request.passphrase, create: request.create }) };
        case 'lock': return { kind: 'instance', instance: await client.lock({}) };
        case 'disconnect': return { kind: 'snapshot', snapshot: await client.disconnect({}) };
        case 'catalogue': return { kind: 'catalogue', commands: await client.catalogue({ conversation: request.conversation }) };
        case 'history': return { kind: 'history', page: await client.history({ conversation: request.conversation, before: request.before, limit: request.limit }) };
        case 'search': return { kind: 'history', page: await client.search({ conversation: request.conversation, text: request.text, before: request.before, limit: request.limit }) };
        case 'complete': return { kind: 'completed', items: await client.complete({ conversation: request.conversation, text: request.text }) };
        case 'events': return { kind: 'changed', revision: await client.events({ after: request.after, wait_ms: request.wait_ms }) };
        case 'mark_read': {
          const p = client.prepare_mark_read({ conversation: request.conversation, message_id: request.message_id });
          const result = await rpc.startAndWait(p); forget(p.handle); return { kind: 'applied', ...result };
        }
        case 'submit': {
          if (request.text.trim() === '/lock') return { kind: 'instance', instance: await client.lock({}) };
          if (['/disconnect', '/quit'].includes(request.text.trim())) return { kind: 'snapshot', snapshot: await client.disconnect({}) };
          const p = client.prepare_submit({ conversation: request.conversation, text: request.text });
          p.handle.operation.id = request.operation_id;
          const retained = find(request.operation_id);
          if (retained) p.handle = retained;
          const result = await rpc.startAndWait(p); forget(p.handle); return result;
        }
      }
    } catch (failure) { throw error(failure); }
  };
  return { request, pendingOperations, checkOperation, forgetOperation(id) { const h = find(id); if (h) forget(h); } };
}
