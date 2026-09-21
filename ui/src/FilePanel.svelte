<script lang="ts">
  import type { FileViewState, FileController } from './file-controller';
  let { view, controller, conversation, canShare, canSave, choose }: {
    view: FileViewState; controller: FileController; conversation: string;
    canShare: boolean; canSave: boolean; choose: (resumeId?: string) => void;
  } = $props();
  let showAll = $state(false), cacheGiB = $state(10), retention = $state(7);
  const snapshot = $derived(view.snapshot), busy = $derived(view.busy);
  function bytes(value: string) { const n = Number(value); return n >= 1073741824 ? `${(n/1073741824).toFixed(1)} GiB` : n >= 1048576 ? `${(n/1048576).toFixed(1)} MiB` : `${n.toLocaleString()} bytes`; }
</script>
<section class="files" aria-label="Conversation files">

  <label><input type="checkbox" bind:checked={showAll} /> Show all cached files</label>
  <div class="toolbar">
    {#if canSave && canShare}<button class="share" disabled={busy} onclick={() => choose()}>Share a file…</button>{:else if !canShare}<span>This conversation is read only.</span>{:else}<span>Use an app with file access to import and save files.</span>{/if}
    <small>Accepted downloads are also shared with authorized participants while chat is unlocked.</small>
  </div>
  {#if view.uploading}<p role="status">Importing {view.uploading}</p>{/if}
  {#if view.notice}<p role="status">{view.notice}</p>{/if}
  {#if view.error}<p role="alert">{view.error}</p>{/if}
  {#each snapshot?.files.filter(f => (showAll || f.conversation === conversation) && f.state !== 'cancelled') ?? [] as file (file.id)}
    <article>
      <div><strong>{file.name}</strong>{#if file.conversation !== conversation}<small>Another conversation</small>{/if}<small>{bytes(file.size_bytes)} · {file.state.replaceAll('_', ' ')} · {file.sources} peers{#if file.completed_by} · {file.completed_by} confirmed complete{/if}</small></div>
      {#if ['downloading', 'waiting_for_peers', 'paused', 'importing'].includes(file.state)}
        <progress aria-label={`Verified progress for ${file.name}`} value={Number(file.verified_bytes)} max={Math.max(1, Number(file.size_bytes))}></progress>
        <small>{bytes(file.verified_bytes)} verified</small>
      {/if}
      {#if file.error}<p role="alert">{file.error}</p>{/if}
      <div class="actions">
        {#if file.state === 'importing' && canSave && canShare && file.conversation === conversation}<button disabled={busy} onclick={() => choose(file.id)}>Resume import</button>{/if}
        {#if file.state === 'offered'}<button disabled={busy} onclick={() => controller.act({ action: 'accept', id: file.id })}>Download & share</button>{/if}
        {#if ['downloading', 'waiting_for_peers'].includes(file.state)}<button disabled={busy} onclick={() => controller.act({ action: 'pause', id: file.id })}>Pause</button>{/if}
        {#if file.state === 'paused'}<button disabled={busy} onclick={() => controller.act({ action: 'resume', id: file.id })}>Resume</button>{/if}
        {#if file.state === 'complete' && canSave}<button disabled={busy} onclick={() => controller.save(file)}>Save file…</button>{/if}
        <button disabled={busy} onclick={() => controller.act({ action: 'cancel', id: file.id })}>{file.state === 'complete' ? 'Remove cached copy' : 'Cancel'}</button>
      </div>
    </article>
  {/each}
  <details class="settings"><summary>Cache settings</summary>
    <p>{bytes(snapshot?.used_bytes ?? '0')} reserved of {bytes(snapshot?.quota_bytes ?? '10737418240')}; completed copies retained for {snapshot?.retention_days ?? 7} days. Saved files are kept separately.</p>
    <label>Cache size (GiB) <input type="number" min="1" max="1024" bind:value={cacheGiB} /></label>
    <label>Retention (days) <input type="number" min="1" max="365" bind:value={retention} /></label>
    <button disabled={busy} onclick={() => controller.act({ action: 'configure', quota_bytes: String(Math.round(Number(cacheGiB) * 1073741824)), retention_days: Number(retention) })}>Apply</button>
  </details>
</section>
<style>
  .files{padding:16px;font:14px/1.5 system-ui,sans-serif;color:var(--ink)}summary{cursor:pointer;min-height:24px}.toolbar{display:grid;gap:10px;margin:12px 0}article{padding:14px 0;border-bottom:1px solid var(--line)}strong{overflow-wrap:anywhere}small{display:block;color:var(--muted)}progress{width:100%;height:8px}.actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}button,input{font:inherit;max-width:100%;min-height:34px}button{cursor:pointer;color:var(--ink);background:transparent;border:1px solid var(--line);padding:5px 8px}button:hover{background:#343b46}.settings{margin-top:20px}label{display:flex;align-items:center;gap:8px;margin:6px 0}input[type=number]{width:6em;background:var(--bg);color:var(--ink);border:1px solid var(--line)}[role=alert]{color:#ffb3b3}:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  @media(pointer:coarse) {
    button,summary { min-height:44px; min-width:44px; }
    label { min-height:44px; }
    input { font-size:16px; }
    input[type=number] { min-height:44px; }
  }
</style>
