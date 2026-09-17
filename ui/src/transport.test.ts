import { describe, expect, it } from 'vitest';
import { attach, ChatError } from './transport';
import type { Exchange } from './transport';
import type { InstanceInfo, RequestEnvelope } from './api';
import { API_VERSION } from './api';
const instance: InstanceInfo = { id: 'selected', label: 'selected', bootId: 'boot', locked: false, protocolLocked: false, profileExists: true, archiveExists: true, safetyNumber: 'safety', capabilities: [] };
describe('instance attachment boundary', () => {
  it('preserves service codes and separates blocked states from transient recovery', async () => {
    const client = await attach(async envelope => ({ version: API_VERSION, instance_id: instance.id, response: envelope.request.kind === 'identify' ? { kind: 'instance', instance } : { kind: 'error', code: 'rejected', message: 'Invalid command' } }));
    await expect(client.request({ kind: 'snapshot' })).rejects.toMatchObject({ code: 'rejected', message: 'Invalid command', retryable: false });
    expect(new ChatError('authentication', 'expired').action).toBe('Sign in again');
    expect(new ChatError('instance', 'changed').retryable).toBe(false);
    expect(new ChatError('transport', 'offline').retryable).toBe(true);
  });
  it('pins every request and preserves exact Unicode, whitespace and operation identity', async () => {
    const received: RequestEnvelope[] = [];
    const exchange: Exchange = async envelope => { received.push(envelope); return { version: API_VERSION, instance_id: instance.id, response: envelope.request.kind === 'identify' ? { kind: 'instance', instance } : { kind: 'applied', conversation: null, notice: null } }; };
    const client = await attach(exchange, 'selected');
    const request = { kind: 'submit' as const, operation_id: 'same-operation', conversation: 'channel/scoped', text: '  λ\n@participant shell exec --script "echo $HOME"  ' };
    await client.request(request); await client.request(request);
    expect(received[1]).toEqual({ version: API_VERSION, instance_id: 'selected', request });
    expect(received[2]).toEqual(received[1]);
  });
  it('rejects a changed endpoint and never discovers another instance', async () => {
    let calls = 0;
    const client = await attach(async () => ({ version: API_VERSION, instance_id: calls++ ? 'other' : instance.id, response: { kind: 'instance', instance } }));
    await expect(client.request({ kind: 'snapshot' })).rejects.toThrow('Selected instance changed');
    expect(calls).toBe(2);
  });
  it('rejects incorrect launch pins and API versions', async () => {
    await expect(attach(async () => ({ version: API_VERSION, instance_id: instance.id, response: { kind: 'instance', instance } }), 'other')).rejects.toThrow('does not match');
    await expect(attach(async () => ({ version: API_VERSION + 1, instance_id: instance.id, response: { kind: 'instance', instance } }))).rejects.toThrow('does not match');
  });
});
