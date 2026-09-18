<script lang="ts">
  import { onMount } from 'svelte';
  import { MAX_NETWORK_INVITATION_BYTES, type NetworkStatus } from './api';
  import { chatError, type Transport } from './transport';
  let { transport }: { transport: Transport } = $props();
  let status = $state<NetworkStatus>();
  let invitation = $state('');
  let error = $state('');
  let busy = $state(false);
  let replacing = $state(false);
  let running = false;
  let revision = 0;
  let fileRevision = 0;
  let polling = false;
  let timer: ReturnType<typeof setInterval> | undefined;
  const needsInvitation = $derived(status?.state === 'invitation_required' || status?.state === 'invitation_expired');
  onMount(() => {
    running = true; void refresh(); timer = setInterval(() => void refresh(), 2000);
    return () => { running = false; revision++; fileRevision++; clearInterval(timer); invitation = ''; };
  });
  async function refresh() {
    if (!running || busy || polling) return;
    polling = true;
    const current = revision;
    try {
      const response = await transport.request({ kind: 'network_status' });
      if (running && !busy && current === revision && response.kind === 'network_status') status = response.status;
    } catch { /* The workspace owns IPC errors; do not invent network progress. */ }
    finally { polling = false; }
  }
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
    busy = true; error = ''; invitation = ''; revision++; fileRevision++;
    try {
      const response = await transport.request({ kind: 'import_network_invitation', code });
      if (running && response.kind === 'network_status') { status = response.status; replacing = false; }
    } catch (failure) { if (running) error = chatError(failure).message; }
    finally { if (running) { busy = false; void refresh(); } }
  }
</script>
{#if status && status.state !== 'local_only' && status.state !== 'locked'}
  <section class="network" aria-label="GChat network">
    <p role="status">{status.message}</p>
    {#if needsInvitation || replacing}
      <h2>Connect to the GChat network</h2>
      <p>Your relay settings are already installed. Get a network invitation privately from the person inviting you; it is separate from a conversation invitation.</p>
      <form onsubmit={connect}>
        <label for="network-invitation">Network invitation</label>
        <textarea id="network-invitation" bind:value={invitation} rows="2" maxlength={MAX_NETWORK_INVITATION_BYTES} autocomplete="off" spellcheck="false" disabled={busy} placeholder="GCNI1-…"></textarea>
        <label for="network-invitation-file">Or select an invitation file</label>
        <input id="network-invitation-file" type="file" accept=".txt,text/plain" onchange={event => void readFile(event)} disabled={busy} />
        <button type="submit" disabled={busy || !invitation.trim()}>{busy ? 'Importing…' : 'Import and connect'}</button>
      </form>
    {:else}<button onclick={() => replacing = true}>Replace network invitation</button>{/if}
    {#if error}<p role="alert">{error}</p>{/if}
  </section>
{/if}
<style>
  .network { padding:12px 18px; border-bottom:1px solid #41454d; background:#25282e; color:#e4e7eb; }
  p { margin:4px 0 8px; line-height:1.45; } h2 { font-size:1.1rem; }
  form { display:grid; gap:8px; max-width:640px; } textarea { resize:vertical; width:100%; box-sizing:border-box; background:#1c1e22; color:inherit; border:1px solid #666d79; padding:8px; font:inherit; }
  button { width:fit-content; padding:7px 12px; cursor:pointer; } input { max-width:100%; } [role=alert] { color:#ffb5b5; }
</style>
