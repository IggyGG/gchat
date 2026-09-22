import type { CommandOutput, OperationDetail, Response } from './api';

export type OperationResult = {
  key: string; id: string; instance: string; network: string;
  conversation: string | null; action: string; started: number;
  checked?: number; state: 'pending' | 'complete' | 'unknown' | 'rejected';
  output?: CommandOutput; message?: string;
};

/** In-memory projection of the encrypted service journal. Never browser storage. */
export class OperationResults {
  private records = new Map<string, OperationResult>();
  private delivered = new Set<string>();
  key(instance: string, network: string, id: string) { return JSON.stringify([instance, network, id]); }
  begin(instance: string, network: string, id: string, conversation: string | null, text?: string) {
    const key = this.key(instance, network, id);
    const old = this.records.get(key);
    if (old) return old;
    // Arguments may contain invitations, message contents or passwords.
    const action = text?.startsWith('/') ? text.split(/\s/, 1)[0] : text ? 'Send message' : 'Saved operation';
    const record: OperationResult = { key, instance, network, id, conversation, action, started: Date.now(), state: 'pending' };
    if (this.records.size >= 256) {
      const oldest = [...this.records.values()].find(r => r.state === 'complete');
      if (oldest) { this.records.delete(oldest.key); this.delivered.delete(oldest.key); }
    }
    this.records.set(key, record);
    return record;
  }
  complete(key: string, response: Response) {
    const old = this.records.get(key);
    if (!old) return false;
    const first = !this.delivered.has(key);
    this.delivered.add(key);
    this.records.set(key, { ...old, state: 'complete', checked: Date.now(),
      conversation: 'conversation' in response ? response.conversation : old.conversation,
      output: response.kind === 'output' ? response.output : undefined,
      message: response.kind === 'applied' ? response.notice ?? 'Completed.' : 'Completed.' });
    return first;
  }
  error(key: string, code: string, message: string) {
    const old = this.records.get(key);
    // A late failed poll must never replace a confirmed result.
    if (old && old.state !== 'complete') this.records.set(key, { ...old, state: code === 'rejected' ? 'rejected' : 'unknown', message, checked: Date.now() });
  }
  restore(details: OperationDetail[], networkFor: (conversation: string | null, instance: string) => string) {
    for (const detail of details) {
      const network = detail.network ?? networkFor(detail.conversation, detail.instance);
      const key = this.key(detail.instance, network, detail.id);
      const old = this.records.get(key);
      if (old?.state === 'complete') continue;
      // A durable terminal snapshot can finish an interrupted original request.
      if (old?.state === 'pending' && detail.state !== 'complete' && detail.state !== 'rejected') continue;
      this.records.set(key, { key, id: detail.id, instance: detail.instance, network,
        conversation: detail.conversation, action: detail.action, started: detail.started * 1000,
        state: detail.state === 'complete' ? 'complete' : detail.state === 'rejected' ? 'rejected' : 'unknown',
        output: detail.output ?? undefined, message: detail.message ?? undefined });
    }
  }
  values() { return [...this.records.values()]; }
  get(key: string) { return this.records.get(key); }
  clear() { this.records.clear(); this.delivered.clear(); }
}
