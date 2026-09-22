import type { FileInfo, FileRequest, FileSnapshot } from './api';
import { encodeFileIo, type FileAccess } from './files';
import { chatError, type Transport } from './transport';
export interface TransferView { id: string; conversation: string; name: string; started: number; pending: boolean; error: string; }
export interface FileViewState { snapshot?: FileSnapshot; error: string; notice: string; busy: boolean; uploading: string; transfers: Record<string, TransferView>; }
export const emptyFiles = (): FileViewState => ({ error: '', notice: '', busy: false, uploading: '', transfers: {} });

/** One owner per unlocked attachment. Panel visibility never owns an upload. */
export class FileController {
  value = emptyFiles();
  private alive = true;
  private timer?: ReturnType<typeof setTimeout>;
  private refreshTask?: Promise<void>;
  private actions = new Map<string, { action: string; generation: number; task: Promise<void> }>();
  private revision = 0;
  private mutationRevision = 0;
  constructor(private transport: Transport, private instance: string, private access: FileAccess | undefined, private changed: (value: FileViewState) => void) {}
  private update(value: Partial<FileViewState>) { if (this.alive) { this.value = { ...this.value, ...value }; this.changed(this.value); } }
  private assertAlive() { if (!this.alive) throw new Error('Import stopped with this locked or closed view. Reopen Files to resume the retained import.'); }
  async command(request: FileRequest): Promise<FileSnapshot> {
    this.assertAlive();
    const revision = this.mutationRevision;
    const response = await this.transport.request({ kind: 'files', request });
    if (response.kind !== 'files') throw new Error('Unexpected file response');
    this.assertAlive();
    // Mutation responses may be filtered. A complete list is refreshed separately.
    if (request.action === 'list') {
      if (request.conversation === null && revision === this.mutationRevision) {
        const transfers = { ...this.value.transfers };
        for (const file of response.snapshot.files) {
          if (!transfers[file.id] && ['downloading', 'waiting_for_peers', 'paused'].includes(file.state)) {
            transfers[file.id] = { id: file.id, conversation: file.conversation, name: file.name, started: Date.now(), pending: false, error: '' };
          }
        }
        this.update({ snapshot: response.snapshot, transfers });
      }
    } else if (this.value.snapshot) {
      this.mutationRevision++;
      const changed = new Map(response.snapshot.files.map(f => [f.id, f]));
      const retained = this.value.snapshot.files.filter(f => !changed.has(f.id));
      this.update({ snapshot: { ...response.snapshot, files: [...retained, ...response.snapshot.files] } });
    }
    return response.snapshot;
  }
  async refresh(): Promise<void> {
    if (!this.alive) return;
    if (this.refreshTask) {
      const revision = this.mutationRevision;
      await this.refreshTask;
      if (this.alive && revision !== this.mutationRevision) return this.refresh();
      return;
    }
    this.refreshTask = this.command({ action: 'list', conversation: null }).then(() => {}).catch(e => { this.update({ error: String(e) }); throw e; });
    try { await this.refreshTask; } finally { this.refreshTask = undefined; }
  }
  start() {
    const poll = async () => {
      if (!this.alive) return;
      if (!this.value.busy && (typeof document === 'undefined' || !document.hidden)) await this.refresh().catch(() => {});
      if (this.alive) this.timer = setTimeout(poll, 2000);
    };
    void poll();
  }
  stop() { this.alive = false; clearTimeout(this.timer); this.value = emptyFiles(); this.changed(this.value); }
  count(conversation: string | null) { return this.value.snapshot?.files.filter(f => f.conversation === conversation && f.state !== 'cancelled').length ?? 0; }
  async act(request: FileRequest) {
    if (!this.alive) return;
    if (!('id' in request)) {
      if (this.value.busy) return;
      this.update({ busy: true, error: '' });
      try { await this.command(request); await this.refresh(); }
      catch (e) { this.update({ error: String(e) }); }
      finally { this.update({ busy: false }); }
      return;
    }
    const id = request.id, previous = this.actions.get(id);
    if (previous?.action === request.action) return previous.task;
    const generation = ++this.revision;
    const file = this.value.snapshot?.files.find(f => f.id === id);
    const old = this.value.transfers[id];
    if (file) this.update({ transfers: { ...this.value.transfers, [id]: {
      id, conversation: file.conversation, name: file.name, started: old?.started ?? Date.now(), pending: true, error: ''
    } }, error: '' });
    const current = () => this.alive && this.actions.get(id)?.generation === generation;
    const update = (pending: boolean, error = '') => {
      const transfer = this.value.transfers[id];
      if (current() && transfer) this.update({ transfers: { ...this.value.transfers, [id]: { ...transfer, pending, error } } });
    };
    const task = Promise.resolve(previous?.task).then(async () => {
      if (!current()) return;
      try {
        // A retry only resumes the same retained download after a fresh status read.
        for (let attempt = 0; ; attempt++) {
          if (!current()) return;
          try { await this.command(request); break; }
          catch (error) {
            if (!['accept', 'resume'].includes(request.action) || !chatError(error).retryable || attempt >= 2) throw error;
            await new Promise(resolve => setTimeout(resolve, attempt ? 1000 : 300));
            if (!current()) return;
            await this.refresh();
            const retained = this.value.snapshot?.files.find(f => f.id === id);
            if (retained && ['downloading', 'waiting_for_peers', 'complete'].includes(retained.state)) break;
            if (!retained || !['offered', 'paused'].includes(retained.state)) throw error;
          }
        }
        if (current()) { update(false); await this.refresh(); }
      } catch (error) { update(false, String(error)); }
      finally { if (current()) this.actions.delete(id); }
    });
    this.actions.set(id, { action: request.action, generation, task });
    await task;
  }
  async upload(file: File, conversation: string, resumeId?: string) {
    if (!this.access || this.value.busy || !this.alive) return;
    this.update({ busy: true, error: '', notice: '' });
    const id = resumeId ?? Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('');
    try {
      const prepared = await this.command({ action: 'prepare', id, conversation, name: file.name, size_bytes: String(file.size) });
      if (prepared.files.some(f => f.id === id && f.state === 'complete')) { this.update({ notice: 'File is already shared.' }); return; }
      // A successful prepare without a visible import is a retained reuse alias.
      // Recover its commit result instead of uploading the file again.
      if (resumeId && !prepared.files.some(f => f.id === id)) {
        await this.command({ action: 'commit', id });
        this.update({ notice: 'File is already shared; the retained result was recovered.' }); return;
      }
      for (let offset = 0, piece = 0; offset < file.size; offset += 262144, piece++) {
        this.assertAlive();
        this.update({ uploading: `${file.name} · ${Math.floor(offset / file.size * 100)}%` });
        const bytes = new Uint8Array(await file.slice(offset, offset + 262144).arrayBuffer());
        this.assertAlive();
        await this.access.exchange(encodeFileIo({ instance: this.instance, id, piece, upload: true }, bytes));
      }
      this.assertAlive();
      const committed = await this.command({ action: 'commit', id });
      const reused = committed.files.some(f => f.id !== id && f.aliases?.includes(id));
      this.update({ notice: reused ? 'Already shared here. You now share the existing verified copy.' : 'File shared with its conversation.' });
    } catch (e) { this.update({ error: String(e) }); }
    finally { this.update({ busy: false, uploading: '' }); if (this.alive) await this.refresh().catch(() => {}); }
  }
  async save(file: FileInfo) {
    if (!this.access || this.value.busy || !this.alive) return;
    this.update({ busy: true, error: '' });
    try { const path = await this.access.save(file.id); this.update({ notice: path ? `Saved to ${path}` : 'Save cancelled.' }); }
    catch (e) { this.update({ error: String(e) }); }
    finally { this.update({ busy: false }); }
  }
}
