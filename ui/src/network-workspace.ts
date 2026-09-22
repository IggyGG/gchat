import { SvelteMap } from 'svelte/reactivity';
import type { JoinedNetwork, Request, Response, Snapshot } from './api';
import type { Transport } from './transport';
import { ChatError } from './transport';
import { encodeFileIo, type FileAccess } from './files';

const prefix = (network: string) => `network/${network}/`;
export function splitConversation(id: string | null | undefined): { network?: string; local: string | null } {
  if (id?.startsWith('network/')) {
    const match = /^network\/([a-f0-9]{64})\/(.+)$/.exec(id);
    if (!match) throw new Error('Invalid network conversation');
    return { network: match[1], local: match[2] };
  }
  return { local: id ?? null };
}

/** A view over isolated services. Network scope is captured before awaiting I/O. */
export class NetworkWorkspace implements Transport {
  networks: JoinedNetwork[] = [];
  active?: string;
  private enabled = false;
  private instances = new Map<string, string>();
  private presence = new SvelteMap<string, boolean>();
  private presenceRevision = 0;
  confirmPresence(network: string | undefined, enabled: boolean) { this.presenceRevision++; this.presence.set(network ?? this.primary() ?? '', enabled); }
  instanceFor(network: string | undefined) { return this.instances.get(network ?? ''); }
  presenceFor(network: string | undefined) { return this.presence.get(network ?? ''); }
  private lifecycle = 0;
  constructor(private base: () => Transport, private changed: (networks: JoinedNetwork[]) => void) {}
  primary() { return this.networks.find(n => n.primary)?.id; }
  networkFor(conversation: string | null) { return splitConversation(conversation).network ?? this.primary(); }
  qualify(network: string, id: string) { return network === this.primary() ? id : prefix(network) + id; }
  select(network: string | undefined) { this.active = network; }
  private publish(networks: JoinedNetwork[]) { this.networks = networks; this.changed(networks); }
  private mapResponse(network: string, response: Response): Response {
    if (network === this.primary()) return response;
    const qualify = (id: string) => this.qualify(network, id);
    switch (response.kind) {
      case 'snapshot': return { ...response, snapshot: { ...response.snapshot, conversations: response.snapshot.conversations.map(c => ({ ...c, id: qualify(c.id) })) } };
      case 'history': return { ...response, page: { ...response.page, messages: response.page.messages.map(m => ({ ...m, conversationId: qualify(m.conversationId) })) } };
      case 'files': return { ...response, snapshot: { ...response.snapshot, files: response.snapshot.files.map(f => ({ ...f, conversation: qualify(f.conversation) })) } };
      case 'applied': return { ...response, conversation: response.conversation ? qualify(response.conversation) : null };
      case 'output': {
        const output = response.output.kind === 'close' ? { ...response.output, conversation: qualify(response.output.conversation) }
          : response.output.kind === 'directory' ? { ...response.output, channels: response.output.channels.map(c => ({ ...c, conversation: c.conversation ? qualify(c.conversation) : null })) }
          : response.output;
        return { ...response, conversation: response.conversation ? qualify(response.conversation) : null, output };
      }
      default: return response;
    }
  }
  private localRequest(request: Request): Request {
    if ('conversation' in request) return { ...request, conversation: splitConversation(request.conversation).local } as Request;
    if (request.kind === 'files' && 'conversation' in request.request) {
      return { ...request, request: { ...request.request, conversation: splitConversation(request.request.conversation).local } } as Request;
    }
    return request;
  }
  async scoped(network: string | undefined, request: Request): Promise<Response> {
    const conversation = 'conversation' in request ? request.conversation : request.kind === 'files' && 'conversation' in request.request ? request.request.conversation : undefined;
    const bound = splitConversation(conversation).network;
    if (bound && bound !== network) throw new ChatError('instance', 'Conversation belongs to another network');
    if (!network || network === this.primary()) return this.base().request(this.localRequest(request));
    if (!this.enabled) throw new ChatError('unavailable', 'Selected network is unavailable');
    const result = await this.base().request({ kind: 'networks', request: { kind: 'call', network, request: this.localRequest(request) } });
    if (result.kind !== 'networks' || result.response.kind !== 'result' || result.response.network !== network) throw new ChatError('protocol', 'Network response binding changed');
    if (result.response.response.kind === 'error') throw new ChatError(result.response.response.code, result.response.response.message);
    return this.mapResponse(network, result.response.response);
  }
  forNetwork(network: string | undefined): Transport { return { request: request => this.scoped(network, request) }; }
  fileAccess(network: string | undefined, access?: FileAccess): FileAccess | undefined {
    if (!access || !network || network === this.primary()) return access;
    return {
      save: id => access.save(`${network}:${id}`),
      exchange: frame => {
        const bytes = new Uint8Array(frame), length = new DataView(frame).getUint16(6);
        const header = JSON.parse(new TextDecoder().decode(bytes.slice(8, 8 + length)));
        return access.exchange(encodeFileIo({ ...header, id: `${network}:${header.id}` }, bytes.slice(8 + length)));
      }
    };
  }
  private async aggregate(snapshot: Snapshot, presenceRevision: number): Promise<Snapshot> {
    const lifecycle = this.lifecycle;
    this.enabled = snapshot.instance.capabilities.includes('networks.v1');
    if (snapshot.instance.locked) { this.publish([]); this.instances.clear(); this.presence.clear(); this.active = undefined; return snapshot; }
    if (!this.enabled) { if (presenceRevision === this.presenceRevision) this.presence.set('', snapshot.presenceEnabled ?? false); return snapshot; }
    const result = await this.base().request({ kind: 'networks', request: { kind: 'list' } });
    if (lifecycle !== this.lifecycle) throw new ChatError('locked', 'Workspace changed during refresh');
    if (result.kind !== 'networks' || result.response.kind !== 'list') throw new ChatError('protocol', 'Invalid network list');
    this.publish(result.response.networks);
    this.active ??= this.primary();
    this.instances.set(this.primary() ?? '', snapshot.instance.id);
    if (presenceRevision === this.presenceRevision) this.presence.set(this.primary() ?? '', snapshot.presenceEnabled ?? false);
    const next = { ...snapshot, conversations: [...snapshot.conversations], operations: [...snapshot.operations ?? []], activity: [...snapshot.activity ?? []], inputHistory: [...snapshot.inputHistory], providerErrors: [...snapshot.providerErrors ?? []] };
    for (const network of this.networks.filter(n => !n.primary)) {
      try {
        const response = await this.scoped(network.id, { kind: 'snapshot' });
        if (lifecycle !== this.lifecycle) throw new ChatError('locked', 'Workspace changed during refresh');
        if (response.kind !== 'snapshot') throw new Error('Invalid network snapshot');
        this.instances.set(network.id, response.snapshot.instance.id);
        if (presenceRevision === this.presenceRevision) this.presence.set(network.id, response.snapshot.presenceEnabled ?? false);
        next.conversations.push(...response.snapshot.conversations);
        next.activity.push(...(response.snapshot.activity ?? []).map(a => ({ ...a, conversation: this.qualify(network.id, a.conversation) })));
        next.operations.push(...(response.snapshot.operations ?? []).map(r => ({ ...r, network: network.id,
          conversation: r.conversation ? this.qualify(network.id, r.conversation) : null })));

        next.inputHistory.push(...response.snapshot.inputHistory.map(h => ({ ...h, conversation: h.conversation ? this.qualify(network.id, h.conversation) : null })));
        next.revision += `:${network.id}:${response.snapshot.revision}`;
      } catch (error) {
        next.providerErrors.push({ id: network.id, code: 'unavailable', message: `${network.name}: ${String(error)}`, retryable: true });
      }
    }
    return next;
  }
  async request(request: Request): Promise<Response> {
    if (request.kind === 'lock' || request.kind === 'disconnect' || (request.kind === 'submit' && ['/lock', '/disconnect', '/quit'].includes(request.text.trim()))) {
      this.lifecycle++; this.publish([]); this.instances.clear(); this.presence.clear(); this.active = undefined; this.enabled = false;
      return this.base().request(request);
    }
    if (request.kind === 'snapshot' || request.kind === 'unlock') {
      const lifecycle = this.lifecycle, presenceRevision = this.presenceRevision;
      const response = await this.base().request(request);
      if (lifecycle !== this.lifecycle) throw new ChatError('locked', 'Workspace changed during refresh');
      // Authenticate locally first; the next independent snapshot aggregates networks.
      if (request.kind === 'unlock') return response;
      return response.kind === 'snapshot' ? { ...response, snapshot: await this.aggregate(response.snapshot, presenceRevision) } : response;
    }
    if (request.kind === 'events' && this.networks.length > 1) {
      // Root changes do not describe child journals; refresh the aggregate on a bounded cadence.
      await new Promise(resolve => setTimeout(resolve, Math.min(request.wait_ms, 1000)));
      return { kind: 'changed', revision: request.after };
    }
    if (request.kind === 'networks') {
      const response = await this.base().request(request);
      if (response.kind === 'networks' && response.response.kind === 'result') {
        this.active = response.response.network;
        if (response.response.response.kind === 'error') throw new ChatError(response.response.response.code, response.response.response.message);
        return this.mapResponse(response.response.network, response.response.response);
      }
      return response;
    }
    if (['identify', 'lock', 'disconnect', 'events'].includes(request.kind)
      || (request.kind === 'submit' && ['/lock', '/disconnect', '/quit'].includes(request.text.trim()))) return this.base().request(request);
    const conversation = 'conversation' in request ? request.conversation : request.kind === 'files' && 'conversation' in request.request ? request.request.conversation : undefined;
    const network = conversation ? this.networkFor(conversation) : this.active;
    return this.scoped(network, request);
  }
  pendingOperations() { return this.base().pendingOperations?.() ?? []; }
  async checkOperation(id: string): Promise<Response> {
    const response = await (this.base().checkOperation?.(id) ?? Promise.reject(new Error('Operation unavailable')));
    if (response.kind === 'networks' && response.response.kind === 'result') {
      return this.mapResponse(response.response.network, response.response.response);
    }
    return response;
  }
  forgetOperation(id: string) { this.base().forgetOperation?.(id); }
}
