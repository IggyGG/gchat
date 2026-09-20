import { mount } from 'svelte';
import Workspace from '../src/Workspace.svelte';
import type { CommandSpec, Conversation, FileInfo, NetworkState, Request, Response, Snapshot } from '../src/api';
const parameters = new URLSearchParams(location.search);
const instance = { id: 'ui-test-instance', label: 'gchat-production', bootId: 'fixture-boot', locked: false, protocolLocked: false, profileExists: true, archiveExists: true, safetyNumber: 'fixture', capabilities: ['ChannelAdmin', 'files.v1'] };
const members = [{ id: 'self', nickname: 'Iggy', isSelf: true, capabilities: [] }, { id: 'peer', nickname: 'Ada', isSelf: false, capabilities: [] }];
const conversations: Conversation[] = ['general', 'design', 'archive'].map((name, index) => ({ provider: null, id: `channel/${name}`, channelId: name, kind: index === 2 ? 'archive' : 'channel', name: `#${name}`, topic: index === 0 ? 'A little more room to talk.' : '', active: true, owner: true, members, unread: index === 1 ? 2 : 0, lastMessageId: null, inputLimitBytes: 12000, commands: [] }));
const commands: CommandSpec[] = ['help', 'lock', 'disconnect', 'quit', 'join', 'create', 'query'].map(name => ({ name: `/${name}`, usage: `/${name}`, description: `Fixture ${name}`, scope: 'instance', capability: null, available: true }));
let state: NetworkState = parameters.has('fresh') ? 'invitation_required' : 'connected';
let revision = 1;
let files: FileInfo[] = parameters.has('empty') ? [] : [{ id: 'existing-file', conversation: 'channel/general', name: 'notes.txt', size_bytes: '4096', verified_bytes: '4096', state: 'complete', sources: 1, verified_sources: 1, completed_by: 1, error: null }];
const requests: Request[] = [];
let hold = false, release: (() => void) | undefined;
const snapshot = (): Snapshot => ({ instance: { ...instance }, revision: String(revision), conversations: instance.locked ? [] : conversations, commandHistory: [], inputHistory: [], providerErrors: [] });
const fileSnapshot = () => ({ files: [...files], quota_bytes: '10737418240', used_bytes: '4096', retention_days: 7 });
const status = () => ({ state, message: state === 'connected' ? 'Connected to the GChat network.' : state === 'invitation_required' ? 'Enter a network invitation.' : state === 'reconnecting' ? 'Reconnecting; history is preserved.' : state });
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
Object.assign(window, { fixture: {
  requests, setNetwork(value: NetworkState) { state = value; revision++; },
  holdUpload() { hold = true; }, releaseUpload() { hold = false; release?.(); },
  getFiles: () => files, setLocked(value: boolean) { instance.locked = value; revision++; },
} });
async function request(req: Request): Promise<Response> {
  if (req.kind !== 'events' && req.kind !== 'snapshot') requests.push(req);
  switch (req.kind) {
    case 'snapshot': return { kind: 'snapshot', snapshot: snapshot() };
    case 'events': await delay(100); return { kind: 'changed', revision: String(revision) };
    case 'network_status': return { kind: 'network_status', status: status() };
    case 'import_network_invitation':
      if (req.code !== 'GCNI1-valid-fixture') throw new Error('Invitation signature rejected');
      state = 'connecting'; revision++; return { kind: 'network_status', status: status() };
    case 'catalogue': return { kind: 'catalogue', commands };
    case 'history': case 'search': return { kind: 'history', page: { messages: [{ id: `${req.conversation}/m1`, conversationId: req.conversation, memberId: 'peer', nickname: 'Ada', body: 'A clear space for the conversation.', timestamp: 1789910000, mine: false, delivery: null, result: null }], before: null } };
    case 'mark_read': return { kind: 'applied', conversation: req.conversation, notice: null };
    case 'complete': return { kind: 'completed', items: [] };
    case 'submit':
      if (req.text === '/lock' || req.text === '/disconnect') { instance.locked = true; instance.protocolLocked = req.text === '/disconnect'; revision++; }
      return { kind: 'applied', conversation: req.conversation, notice: null };
    case 'unlock': instance.locked = false; instance.protocolLocked = false; revision++; return { kind: 'snapshot', snapshot: snapshot() };
    case 'files': {
      const r = req.request;
      if (r.action === 'prepare') files.push({ id: r.id, conversation: r.conversation, name: r.name, size_bytes: r.size_bytes, verified_bytes: '0', state: 'importing', sources: 0, verified_sources: 0, completed_by: 0, error: null });
      if (r.action === 'commit') files = files.map(f => f.id === r.id ? { ...f, state: 'complete', verified_bytes: f.size_bytes } : f);
      if (r.action === 'pause' || r.action === 'resume' || r.action === 'cancel') files = files.map(f => f.id === r.id ? { ...f, state: r.action === 'pause' ? 'paused' : r.action === 'resume' ? 'downloading' : 'cancelled' } : f);
      return { kind: 'files', snapshot: fileSnapshot() };
    }
    default: throw new Error(`Unexpected fixture request: ${req.kind}`);
  }
}
mount(Workspace, { target: document.getElementById('app')!, props: { transport: { request }, fileAccess: {
  async exchange() { if (hold) await new Promise<void>(resolve => release = resolve); return new Uint8Array(); },
  async save() { return '/Downloads/notes.txt'; },
} } });
