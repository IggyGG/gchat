import { mount } from 'svelte';
import type { OperationHandle } from '@gcoms/rpc';
import { ChatError } from '../src/transport';
import Workspace from '../src/Workspace.svelte';
import type { DeviceUnlock } from '../src/device-unlock';
import type { CommandSpec, Conversation, FileInfo, NetworkState, Request, Response, Snapshot } from '../src/api';
const parameters = new URLSearchParams(location.search);
const primaryNetwork = 'a'.repeat(64), otherNetwork = 'b'.repeat(64);
let joinedNetwork = false;
const instance = { id: 'ui-test-instance', label: 'gchat-production', bootId: 'fixture-boot', locked: false, protocolLocked: false, profileExists: true, archiveExists: true, safetyNumber: 'fixture', capabilities: ['ChannelAdmin', 'files.v1'] };
if (parameters.has('device-unlock')) { instance.locked = true; instance.protocolLocked = true; }
const unlockChoices: boolean[] = [];
if (parameters.has('networks')) instance.capabilities.push('networks.v1');
const members = [{ id: 'self', nickname: 'Iggy', isSelf: true, capabilities: [] }, { id: 'peer', nickname: 'Ada', isSelf: false, capabilities: [] }];
const conversations: Conversation[] = ['general', 'design', 'archive'].map((name, index) => ({ provider: null, id: `channel/${name}`, channelId: name, kind: index === 2 ? 'archive' : 'channel', name: `#${name}`, topic: index === 0 ? 'A little more room to talk.' : '', active: true, owner: !parameters.has('member'), members, unread: index === 1 ? 2 : 0, lastMessageId: null, inputLimitBytes: 12000, commands: [] }));
const commands: CommandSpec[] = ['help', 'lock', 'disconnect', 'quit', 'join', 'create', 'query'].map(name => ({ name: `/${name}`, usage: `/${name}`, description: `Fixture ${name}`, scope: 'instance', capability: null, available: true }));
let state: NetworkState = parameters.has('fresh') ? 'invitation_required' : 'connected';
let revision = 1;
let files: FileInfo[] = parameters.has('empty') ? [] : [{ id: 'existing-file', conversation: 'channel/general', name: 'notes.txt', size_bytes: '4096', verified_bytes: '4096', state: 'complete', sources: 1, verified_sources: 1, completed_by: 1, error: null }];
const requests: Request[] = [];
let hold = false, release: (() => void) | undefined;
let holdSnapshots = false;
const heldSnapshots: (() => void)[] = [];
let savedId: string | undefined;
let savedReply: Response | undefined;
let checks = 0;
const recovered = parameters.has('saved-operation') ? [{ id: 'saved-operation-001', instance: instance.id, conversation: 'channel/general', action: '/create', started: 1789910000, state: 'unknown', output: null, message: 'Interrupted after admission.' }] : [];
const snapshot = (): Snapshot => ({ instance: { ...instance }, revision: String(revision), conversations: instance.locked ? [] : conversations, commandHistory: [], inputHistory: [], providerErrors: [], operations: instance.locked ? [] : recovered });
const fileSnapshot = () => ({ files: [...files], quota_bytes: '10737418240', used_bytes: '4096', retention_days: 7 });
const status = () => ({ state, message: state === 'connected' ? 'Connected to the GChat network.' : state === 'invitation_required' ? 'Enter a network invitation.' : state === 'reconnecting' ? 'Reconnecting; history is preserved.' : state });
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
Object.assign(window, { fixture: {
  requests, unlockChoices, checks: () => checks, setNetwork(value: NetworkState) { state = value; revision++; },
  holdUpload() { hold = true; }, releaseUpload() { hold = false; release?.(); },
  getFiles: () => files, setLocked(value: boolean) { instance.locked = value; revision++; },
  suspend() { instance.locked = true; instance.protocolLocked = true; revision++; },
  replaceProfile(id: string) { instance.id = id; instance.bootId += '-replacement'; revision++; },
  removeConversation(id: string) { const index = conversations.findIndex(c => c.id === id); if (index >= 0) conversations.splice(index, 1); revision++; },
  holdSnapshots() { holdSnapshots = true; }, pendingSnapshots: () => heldSnapshots.length,
  releaseSupersededSnapshots() { for (const finish of heldSnapshots.splice(0, heldSnapshots.length - 1)) finish(); },
  releaseSnapshots() { holdSnapshots = false; for (const finish of heldSnapshots.splice(0)) finish(); },
} });
async function request(req: Request): Promise<Response> {
  if (req.kind !== 'events' && req.kind !== 'snapshot') requests.push(req);
  switch (req.kind) {
    case 'networks': {
      const r = req.request;
      const network = (id: string) => ({ id, name: id === primaryNetwork ? 'home.example' : 'other.example', fingerprint: id, primary: id === primaryNetwork, status: { state: 'connected' as const, message: 'Connected' } });
      if (r.kind === 'list') return { kind: 'networks', response: { kind: 'list', networks: [network(primaryNetwork), ...(joinedNetwork ? [network(otherNetwork)] : [])] } };
      if (r.kind === 'inspect') {
        if (!['GCI1-valid-fixture', 'gcoms://join#GCI1-valid-fixture'].includes(r.code)) throw new Error('Invitation signature rejected');
        return { kind: 'networks', response: { kind: 'preview', preview: { network: network(otherNetwork), channel: 'general', expires: 2000000000, newNetwork: !joinedNetwork } } };
      }
      if (r.kind === 'join') {
        if (r.accepted_network !== otherNetwork) throw new Error('Network was not confirmed');
        joinedNetwork = true; revision++;
        return { kind: 'networks', response: { kind: 'result', network: otherNetwork, response: { kind: 'applied', conversation: 'channel/general', notice: null } } };
      }
      if (r.kind === 'call') return { kind: 'networks', response: { kind: 'result', network: r.network, response: await request(r.request) } };
      throw new Error('Unknown network operation');
    }
    case 'snapshot': {
      const current = snapshot();
      if (holdSnapshots) await new Promise<void>(resolve => heldSnapshots.push(resolve));
      return { kind: 'snapshot', snapshot: current };
    }
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
      if (req.text === '/invite') {
        savedId = req.operation_id;
        savedReply = { kind: 'output', conversation: req.conversation, output: { kind: 'invitation', channel: 'general', link: 'GCI1-fixture-secret', expires: 2000000000, localOnly: false } };
        const result = savedReply;
        await delay(350); savedId = undefined; return result;
      }
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
const deviceUnlock: DeviceUnlock | undefined = parameters.has('device-unlock') ? {
  async unlock(passphrase, create, remember) {
    unlockChoices.push(remember);
    return { response: await request({ kind: 'unlock', passphrase, create }), warning: parameters.has('vault-failure') ? 'Secure device storage unavailable; enter your passphrase after suspension.' : undefined };
  },
} : undefined;
mount(Workspace, { target: document.getElementById('app')!, props: { transport: { request,
  pendingOperations: () => savedId ? [{ operation: { id: savedId } } as OperationHandle] : [],
  async checkOperation() { checks++; if (savedReply) return savedReply; throw new ChatError('outcome_unknown', 'Interrupted after admission. No new result is available.'); },
}, deviceUnlock, nativeShell: parameters.has('native-shell') ? {
  mac: parameters.has('mac'), minimize: async () => { window.dispatchEvent(new Event('fixture-minimize')); },
  maximize: async () => { window.dispatchEvent(new Event('fixture-maximize')); }, close: async () => { window.dispatchEvent(new Event('fixture-close')); },
  drag: async () => {}, resize: async () => {},
} : undefined, pendingInvitation: parameters.has('app-link') ? 'gcoms://join#GCI1-valid-fixture' : undefined, fileAccess: {
  async exchange() { if (hold) await new Promise<void>(resolve => release = resolve); return new Uint8Array(); },
  async save() { return '/Downloads/notes.txt'; },
  async saveInvitation() { return parameters.has('cancel-save') ? null : '/chosen/gchat-invitation.txt'; },
} } });
