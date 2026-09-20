<script lang="ts">
  import { onDestroy } from 'svelte';
  import { MAX_NETWORK_INVITATION_BYTES, type NetworkStatus } from './api';
  import { chatError, type Transport } from './transport';
  let { transport, status, imported }: { transport: Transport; status?: NetworkStatus; imported: (status: NetworkStatus) => void } = $props();
  let invitation = $state(''), error = $state(''), busy = $state(false);
  let running = true, fileRevision = 0;
  onDestroy(() => { running = false; fileRevision++; invitation = ''; });
  async function readFile(event: Event) {
    const input = event.currentTarget as HTMLInputElement;
    const file = input.files?.[0]; input.value = '';
    const current = ++fileRevision;
    if (!file) return;
    if (file.size > MAX_NETWORK_INVITATION_BYTES) { error = 'This invitation file is too large.'; return; }
    try { const text = await file.text(); if (running && !busy && current === fileRevision) { invitation = text.trim(); error = ''; } }
    catch { if (running && current === fileRevision) error = 'Could not read the invitation file.'; }
  }
  async function connect(event: SubmitEvent) {
    event.preventDefault();
    if (busy) return;
    const code = invitation.trim();
    if (!code.startsWith('GCNI1-')) { error = 'Use a network invitation beginning with GCNI1-. Conversation invitations are used after connecting.'; return; }
    if (new TextEncoder().encode(code).length > MAX_NETWORK_INVITATION_BYTES) { error = 'This invitation is too large.'; return; }
    busy = true; error = ''; invitation = ''; fileRevision++;
    try {
      const response = await transport.request({ kind: 'import_network_invitation', code });
      if (response.kind !== 'network_status') throw new Error('Unexpected network response. Try again.');
      if (running && response.kind === 'network_status') { imported(response.status); }
    } catch (failure) { if (running) error = chatError(failure).message; }
    finally { if (running) busy = false; }
  }
</script>
<section class="network" aria-label="Network invitation">
  <p>Enter a network invitation from the person inviting you. Channel invitations are separate.</p>
  <form onsubmit={connect}>
    <label for="network-invitation">Network invitation</label>
    <textarea id="network-invitation" bind:value={invitation} rows="3" maxlength={MAX_NETWORK_INVITATION_BYTES} autocomplete="off" spellcheck="false" disabled={busy} placeholder="GCNI1-…"></textarea>
    <label for="network-invitation-file">Or choose an invitation file</label>
    <input id="network-invitation-file" type="file" accept=".txt,text/plain" onchange={event => void readFile(event)} disabled={busy} />
    <button type="submit" disabled={busy || !invitation.trim()}>{busy ? 'Validating…' : 'Connect'}</button>
  </form>
  {#if error}<p role="alert">{error}</p>{/if}
</section>
<style>
  p { color:var(--muted); margin:0 0 16px; line-height:1.5; }
  form { display:grid; gap:8px; } label { margin-top:8px; }
  textarea,input { max-width:100%; font:inherit; color:inherit; }
  textarea { resize:vertical; width:100%; box-sizing:border-box; background:var(--bg); border:1px solid var(--line); padding:10px; }
  button { width:fit-content; margin-top:12px; padding:9px 18px; cursor:pointer; background:#343b46; color:var(--ink); border:1px solid #566476; font:inherit; }
  [role=alert] { color:#ffb5b5; margin-top:12px; }
  :focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
</style>
