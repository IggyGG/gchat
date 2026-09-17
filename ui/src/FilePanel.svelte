<script lang="ts">
  import { onMount } from 'svelte';
  import type { FileInfo, FileRequest, FileSnapshot } from './api';
  import type { Transport } from './transport';
  import { encodeFileIo, type FileAccess } from './files';
  let { transport, conversation, instance, access, canShare = true }: { transport: Transport; conversation: string; instance: string; access?: FileAccess; canShare?: boolean } = $props();
  let snapshot = $state<FileSnapshot>();
  let error = $state(''), notice = $state(''), busy = $state(false), uploading = $state('');
  let alive = true;
  let showAll = $state(false);
  let cacheGiB = $state(10), retention = $state(7);
  let input = $state<HTMLInputElement>();
  let resumeImport = $state<string>();
  async function command(request: FileRequest) {
    const response = await transport.request({ kind: 'files', request });
    if (response.kind !== 'files') throw new Error('Unexpected file response');
    if (alive) snapshot = response.snapshot;
    return response.snapshot;
  }
  async function refresh() { try { await command({ action: 'list', conversation: showAll ? null : conversation }); } catch (e) { if (alive) error = String(e); } }
  onMount(() => {
    alive = true;
    void (async () => { while (alive) { if (!busy) await refresh(); await new Promise(r => setTimeout(r, 2000)); } })();
    return () => { alive = false; };
  });
  async function act(request: FileRequest) {
    busy = true; error = ''; notice = '';
    try { await command(request); await refresh(); } catch (e) { error = String(e); } finally { busy = false; }
  }
  async function upload(file: File) {
    if (!access) return;
    busy = true; error = ''; notice = '';
    const id = resumeImport ?? Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('');
    resumeImport = undefined;
    try {
      const prepared = await command({ action: 'prepare', id, conversation, name: file.name, size_bytes: String(file.size) });
      if (prepared.files.some(f => f.id === id && f.state === 'complete')) { notice = 'File is already shared.'; return; }
      for (let offset = 0, piece = 0; offset < file.size; offset += 262144, piece++) {
        if (!alive) throw new Error('Upload paused. Reopen Files to resume the retained import.');
        uploading = `${file.name} · ${Math.floor(offset / file.size * 100)}%`;
        const bytes = new Uint8Array(await file.slice(offset, offset + 262144).arrayBuffer());
        await access.exchange(encodeFileIo({ instance, id, piece, upload: true }, bytes));
      }
      await command({ action: 'commit', id }); notice = 'File shared with this conversation.';
    } catch (e) { if (alive) error = String(e); }
    finally { busy = false; uploading = ''; if (input) input.value = ''; if (alive) await refresh(); }
  }
  async function save(file: FileInfo) {
    if (!access) return;
    busy = true; error = '';
    try { notice = `Saved to ${await access.save(file.id)}`; } catch (e) { error = String(e); } finally { busy = false; }
  }
  function bytes(value: string) { const n = Number(value); return n >= 1073741824 ? `${(n/1073741824).toFixed(1)} GiB` : n >= 1048576 ? `${(n/1048576).toFixed(1)} MiB` : `${n.toLocaleString()} bytes`; }
</script>
<details class="files">
  <summary>Files{#if snapshot} · {snapshot.files.filter(f => (showAll || f.conversation === conversation) && f.state !== 'cancelled').length}{/if}</summary>
  <label><input type="checkbox" bind:checked={showAll} onchange={() => void refresh()} /> Show all cached files</label>
  <div class="toolbar">
    {#if access && canShare}<input bind:this={input} type="file" aria-label="Choose a file to share" disabled={busy} onchange={() => { const file = input?.files?.[0]; if (file) void upload(file); }} />{:else if !canShare}<span>Choose an active conversation to share a new file.</span>{:else}<span>Use the desktop or terminal app to import and save files.</span>{/if}
    <small>Accepted downloads are also shared with authorized participants while chat is unlocked.</small>
  </div>
  {#if uploading}<p role="status">Importing {uploading}</p>{/if}
  {#if notice}<p role="status">{notice}</p>{/if}
  {#if error}<p role="alert">{error}</p>{/if}
  {#each snapshot?.files.filter(f => (showAll || f.conversation === conversation) && f.state !== 'cancelled') ?? [] as file (file.id)}
    <article>
      <div><strong>{file.name}</strong>{#if file.conversation !== conversation}<small>Another conversation</small>{/if}<small>{bytes(file.size_bytes)} · {file.state.replaceAll('_', ' ')} · {file.sources} peers{#if file.completed_by} · {file.completed_by} confirmed complete{/if}</small></div>
      {#if ['downloading', 'waiting_for_peers', 'paused', 'importing'].includes(file.state)}
        <progress aria-label={`Verified progress for ${file.name}`} value={Number(file.verified_bytes)} max={Math.max(1, Number(file.size_bytes))}></progress>
        <small>{bytes(file.verified_bytes)} verified</small>
      {/if}
      {#if file.error}<p role="alert">{file.error}</p>{/if}
      <div class="actions">
        {#if file.state === 'importing' && access && canShare && file.conversation === conversation}<button disabled={busy} onclick={() => { resumeImport = file.id; input?.click(); }}>Resume import</button>{/if}
        {#if file.state === 'offered'}<button disabled={busy} onclick={() => act({ action: 'accept', id: file.id })}>Download & share</button>{/if}
        {#if ['downloading', 'waiting_for_peers'].includes(file.state)}<button disabled={busy} onclick={() => act({ action: 'pause', id: file.id })}>Pause</button>{/if}
        {#if file.state === 'paused'}<button disabled={busy} onclick={() => act({ action: 'resume', id: file.id })}>Resume</button>{/if}
        {#if file.state === 'complete' && access}<button disabled={busy} onclick={() => save(file)}>Save to Downloads</button>{/if}
        <button disabled={busy} onclick={() => act({ action: 'cancel', id: file.id })}>{file.state === 'complete' ? 'Remove cached copy' : 'Cancel'}</button>
      </div>
    </article>
  {/each}
  <details class="settings"><summary>Cache settings</summary>
    <p>{bytes(snapshot?.used_bytes ?? '0')} reserved of {bytes(snapshot?.quota_bytes ?? '10737418240')}; completed copies retained for {snapshot?.retention_days ?? 7} days. Saved files are kept separately.</p>
    <label>Cache size (GiB) <input type="number" min="1" max="1024" bind:value={cacheGiB} /></label>
    <label>Retention (days) <input type="number" min="1" max="365" bind:value={retention} /></label>
    <button disabled={busy} onclick={() => act({ action: 'configure', quota_bytes: String(Math.round(Number(cacheGiB) * 1073741824)), retention_days: Number(retention) })}>Apply</button>
  </details>
</details>
<style>
  .files{border-top:1px solid #42484c;background:#202529;padding:8px 12px;font:14px/1.4 system-ui,sans-serif;color:#e4e7eb;max-height:40vh;overflow:auto}summary{cursor:pointer;min-height:24px}.toolbar{display:grid;gap:8px;margin:8px 0}article{padding:10px 0;border-bottom:1px solid #42484c}strong{overflow-wrap:anywhere}small{display:block;color:#b7c2c7}progress{width:100%;height:8px}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}button,input{font:inherit;max-width:100%;min-height:32px}button{cursor:pointer}.settings{margin-top:12px}label{display:inline-flex;gap:6px;margin:4px}label input{width:6em}[role=alert]{color:#ffb3b3}
</style>
