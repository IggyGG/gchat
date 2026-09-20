import type { FileInfo, FileRequest, FileSnapshot } from './api';
import { encodeFileIo, type FileAccess } from './files';
import type { Transport } from './transport';
export interface FileViewState { snapshot?: FileSnapshot; error: string; notice: string; busy: boolean; uploading: string; }
export const emptyFiles = (): FileViewState => ({ error: '', notice: '', busy: false, uploading: '' });

/** One owner per unlocked attachment. Panel visibility never owns an upload. */
export class FileController {
  value = emptyFiles();
  private alive = true;
  private timer?: ReturnType<typeof setTimeout>;
  private refreshing = false;
  constructor(private transport: Transport, private instance: string, private access: FileAccess | undefined, private changed: (value: FileViewState) => void) {}
  private update(value: Partial<FileViewState>) { if (this.alive) { this.value = { ...this.value, ...value }; this.changed(this.value); } }
  private assertAlive() { if (!this.alive) throw new Error('Import stopped with this locked or closed view. Reopen Files to resume the retained import.'); }
  async command(request: FileRequest): Promise<FileSnapshot> {
    this.assertAlive();
    const response = await this.transport.request({ kind: 'files', request });
    if (response.kind !== 'files') throw new Error('Unexpected file response');
    this.assertAlive();
    // Mutation responses may be filtered. A complete list is refreshed separately.
    if (request.action === 'list' && request.conversation === null) this.update({ snapshot: response.snapshot });
    return response.snapshot;
  }
  async refresh() {
    if (!this.alive || this.refreshing) return;
    this.refreshing = true;
    try { await this.command({ action: 'list', conversation: null }); }
    catch (e) { this.update({ error: String(e) }); }
    finally { this.refreshing = false; }
  }
  start() {
    const poll = async () => {
      if (!this.alive) return;
      if (!this.value.busy && (typeof document === 'undefined' || !document.hidden)) await this.refresh();
      if (this.alive) this.timer = setTimeout(poll, 2000);
    };
    void poll();
  }
  stop() { this.alive = false; clearTimeout(this.timer); this.value = emptyFiles(); this.changed(this.value); }
  count(conversation: string | null) { return this.value.snapshot?.files.filter(f => f.conversation === conversation && f.state !== 'cancelled').length ?? 0; }
  async act(request: FileRequest) {
    if (this.value.busy || !this.alive) return;
    this.update({ busy: true, error: '', notice: '' });
    try { await this.command(request); await this.refresh(); }
    catch (e) { this.update({ error: String(e) }); }
    finally { this.update({ busy: false }); }
  }
  async upload(file: File, conversation: string, resumeId?: string) {
    if (!this.access || this.value.busy || !this.alive) return;
    this.update({ busy: true, error: '', notice: '' });
    const id = resumeId ?? Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('');
    try {
      const prepared = await this.command({ action: 'prepare', id, conversation, name: file.name, size_bytes: String(file.size) });
      if (prepared.files.some(f => f.id === id && f.state === 'complete')) { this.update({ notice: 'File is already shared.' }); return; }
      for (let offset = 0, piece = 0; offset < file.size; offset += 262144, piece++) {
        this.assertAlive();
        this.update({ uploading: `${file.name} · ${Math.floor(offset / file.size * 100)}%` });
        const bytes = new Uint8Array(await file.slice(offset, offset + 262144).arrayBuffer());
        this.assertAlive();
        await this.access.exchange(encodeFileIo({ instance: this.instance, id, piece, upload: true }, bytes));
      }
      this.assertAlive();
      await this.command({ action: 'commit', id });
      this.update({ notice: 'File shared with its conversation.' });
    } catch (e) { this.update({ error: String(e) }); }
    finally { this.update({ busy: false, uploading: '' }); if (this.alive) await this.refresh(); }
  }
  async save(file: FileInfo) {
    if (!this.access || this.value.busy || !this.alive) return;
    this.update({ busy: true, error: '' });
    try { this.update({ notice: `Saved to ${await this.access.save(file.id)}` }); }
    catch (e) { this.update({ error: String(e) }); }
    finally { this.update({ busy: false }); }
  }
}
