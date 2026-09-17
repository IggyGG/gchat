import { API_VERSION, type Request, type RequestEnvelope, type Response, type ResponseEnvelope } from './api';
export interface Transport {
  request(request: Request): Promise<Response>;
  pendingOperations?(): import('@gcoms/rpc').OperationHandle[];
  checkOperation?(id: string): Promise<Response>;
  forgetOperation?(id: string): void;
}
export type Exchange = (envelope: RequestEnvelope) => Promise<ResponseEnvelope>;
export class ChatError extends Error {
  constructor(public readonly code: string, message: string) { super(message); this.name = 'ChatError'; }
  get retryable() { return ['transport', 'timeout', 'unavailable'].includes(this.code); }
  get action() {
    if (this.code === 'authentication') return 'Sign in again';
    if (this.code === 'version') return 'Update and reopen';
    if (this.code === 'instance') return 'Reopen selected instance';
    if (this.code === 'locked') return 'Unlock chat';
    if (this.code === 'disconnected') return 'Reconnect this instance';
    return this.retryable ? 'Reconnect' : 'Review request';
  }
}
export function chatError(error: unknown): ChatError {
  return error instanceof ChatError ? error : new ChatError('transport', error instanceof Error ? error.message : String(error));
}
/** An attachment never discovers another instance when its selected endpoint fails. */
export async function attach(exchange: Exchange, expectedInstance?: string): Promise<Transport> {
  const first = await exchange({ version: API_VERSION, instance_id: null, request: { kind: 'identify' } });
  if (first.version !== API_VERSION) throw new ChatError('version', 'Selected instance API version does not match this client');
  if (first.response.kind === 'error') throw new ChatError(first.response.code, first.response.message);
  if (first.response.kind !== 'instance' || first.instance_id !== first.response.instance.id || (expectedInstance && first.instance_id !== expectedInstance)) throw new ChatError('instance', 'Selected instance does not match this attachment');
  const instance_id = first.instance_id;
  return { async request(request) {
    const result = await exchange({ version: API_VERSION, instance_id, request });
    if (result.version !== API_VERSION) throw new ChatError('version', 'Selected instance API version does not match this client');
    if (result.instance_id !== instance_id) throw new ChatError('instance', 'Selected instance changed; reopen this attachment explicitly');
    if (result.response.kind === 'error') throw new ChatError(result.response.code, result.response.message);
    return result.response;
  } };
}
export function httpExchange(url: string): Exchange {
  return async envelope => {
    const result = await fetch(url, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(envelope), signal: AbortSignal.timeout(150_000) });
    if (!result.ok) {
      const code = result.status === 401 ? 'authentication' : result.status === 403 ? 'forbidden' : result.status >= 500 ? 'unavailable' : 'request';
      throw new ChatError(code, result.status === 401 ? 'Your login has expired. Sign in again to reopen this instance.' : result.status === 403 ? 'This attachment no longer has permission to access this instance.' : `Selected instance unavailable (${result.status})`);
    }
    return await result.json();
  };
}
