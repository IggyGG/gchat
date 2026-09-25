<script lang="ts">
  import { onDestroy } from 'svelte';
  import { readInvitationFile } from './invitation-card';
  import { MAX_NETWORK_INVITATION_BYTES, type NetworkStatus, type InvitationPreview, type Response } from './api';
  import { chatError, type Transport } from './transport';
  let { transport, status, imported, combined = false, joined, chooseFile, selectedFile, fileConsumed, initialInvitation = '', privateComposer = false }: { transport: Transport; initialInvitation?: string; privateComposer?: boolean; status?: NetworkStatus; imported: (status: NetworkStatus) => void; combined?: boolean; joined?: (response: Response) => void; chooseFile?: () => void; selectedFile?: { id: number; file: File }; fileConsumed?: (id: number) => void } = $props();
  let invitation = $state(''), error = $state(''), busy = $state(false);
  let preview = $state<InvitationPreview>(), nickname = $state('');
  let pendingCode = '', operationId = '';
  let seenInitial = '';
  $effect(() => { if (initialInvitation && initialInvitation !== seenInitial && !busy && !preview) { seenInitial = initialInvitation; invitation = initialInvitation; if (combined) void connect(); } });
  let running = true, fileRevision = 0;
  let consumedSelection: number | undefined;
  onDestroy(() => { running = false; fileRevision++; invitation = ''; pendingCode = ''; nickname = ''; });
  $effect(() => {
    if (selectedFile && selectedFile.id !== consumedSelection) {
      consumedSelection = selectedFile.id;
      void loadFile(selectedFile.file, selectedFile.id);
    } else if (!selectedFile && consumedSelection !== undefined) {
      consumedSelection = undefined; fileRevision++;
    }
  });
  async function readFile(event: Event) {
    const input = event.currentTarget as HTMLInputElement;
    const file = input.files?.[0]; input.value = '';
    if (file) await loadFile(file);
  }
  async function loadFile(file: File, selectionId?: number) {
    const current = ++fileRevision;
    try {
      const text = await readInvitationFile(file);
      if (running && !busy && current === fileRevision) { invitation = text.trim(); error = ''; if (combined && (file.type === 'image/png' || /\.png$/i.test(file.name))) await connect(); }
    }
    catch (failure) { if (running && current === fileRevision) error = failure instanceof Error ? failure.message : 'Could not read the invitation file.'; }
    finally { if (running && current === fileRevision && selectionId !== undefined) fileConsumed?.(selectionId); }
  }
  export async function answer(text: string) {
    if (busy) return;
    if (preview) { nickname = text.trim(); error = ''; return; }
    invitation = text.trim(); await connect();
  }
  async function connect(event?: SubmitEvent) {
    event?.preventDefault();
    if (busy) return;
    const code = invitation.trim();
    if (combined) {
      if (!code || new TextEncoder().encode(code).length > MAX_NETWORK_INVITATION_BYTES) { error = 'Use one complete invitation within the size limit.'; return; }
      busy = true; error = '';
      try {
        const response = await transport.request({ kind: 'networks', request: { kind: 'inspect', code } });
        if (!running) return;
        if (response.kind !== 'networks' || response.response.kind !== 'preview') throw new Error('Invalid invitation preview');
        preview = response.response.preview; pendingCode = code; invitation = ''; operationId = crypto.randomUUID();
      } catch (failure) { if (running) error = chatError(failure).message; }
      finally { busy = false; }
      return;
    }
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
  async function accept(event: SubmitEvent) {
    event.preventDefault();
    if (!preview || busy) return;
    busy = true; error = '';
    try {
      const response = await transport.request({ kind: 'networks', request: { kind: 'join', code: pendingCode, nickname, accepted_network: preview.network.id, operation_id: operationId } });
      if (!running) return;
      pendingCode = ''; nickname = ''; preview = undefined;
      joined?.(response);
    } catch (failure) { if (running) error = chatError(failure).message; }
    finally { busy = false; }
  }
</script>
<section class="network" aria-label="Network invitation" ondragover={event => { if (event.dataTransfer?.types.includes('Files')) event.preventDefault(); }} ondrop={event => { event.preventDefault(); const file = event.dataTransfer?.files[0]; if (file && !busy && !preview) void loadFile(file); }}>
  {#if preview}
  <form onsubmit={accept}>
    <p>{preview.channel ? `Join #${preview.channel.replace(/^#/, '')} on ${preview.network.name}` : `Connect to ${preview.network.name}`}</p>
    {#if preview.newNetwork}<p>This adds a new network. Your existing networks stay connected.</p><details><summary>Network identity</summary><code>{preview.network.fingerprint}</code></details>{/if}
    {#if preview.channel && privateComposer}<p>{nickname ? `Nickname: ${nickname}. Confirm Join when ready.` : 'Type your nickname in the private answer below, then confirm Join.'}</p>{:else if preview.channel}<label for="invitation-nickname">Your nickname in this channel</label><input id="invitation-nickname" bind:value={nickname} required maxlength="256" autocomplete="nickname" disabled={busy} />{/if}
    <p>Expires {new Date(preview.expires * 1000).toLocaleString()}</p>
    <div><button type="submit" disabled={busy || (!!preview.channel && !nickname.trim())}>{busy ? 'Joining…' : preview.channel ? 'Join' : 'Connect'}</button><button type="button" disabled={busy} onclick={() => { preview = undefined; pendingCode = ''; error = ''; }}>Cancel</button></div>
  </form>
  {:else}
  <p>{combined ? 'Paste an invitation to connect to its network and join its channel.' : 'Enter a network invitation from the person inviting you.'}</p>
  <form onsubmit={connect}>
    {#if privateComposer}<p>{invitation ? 'Invitation ready. Continue to review its signed network and channel.' : 'Paste your invitation in the private answer below, or choose a file.'}</p>{:else}
    <label for="network-invitation">{combined ? 'Invitation' : 'Network invitation'}</label>
    <textarea id="network-invitation" bind:value={invitation} rows="3" maxlength={MAX_NETWORK_INVITATION_BYTES} autocomplete="off" spellcheck="false" disabled={busy} placeholder={combined ? 'Paste an invitation' : 'GCNI1-…'}></textarea>{/if}
    {#if chooseFile}<button type="button" disabled={busy} onclick={chooseFile}>Or choose an invitation file</button>
    {:else}<label for="network-invitation-file">Or choose an invitation file</label>
    <input id="network-invitation-file" type="file" accept=".png,image/png,.txt,text/plain" onchange={event => void readFile(event)} disabled={busy} />{/if}
    <button type="submit" disabled={busy || !invitation.trim()}>{busy ? 'Validating…' : combined ? 'Continue' : 'Connect'}</button>
  </form>
  {/if}
  {#if error}<p role="alert">{error}</p>{/if}
</section>
<style>
  p { color:var(--muted); margin:0 0 16px; line-height:1.5; }
  form { display:grid; gap:8px; } label { margin-top:8px; } input { min-height:44px; padding:10px; background:var(--bg); border:1px solid var(--line); }
  textarea,input { max-width:100%; font:inherit; color:inherit; }
  textarea { resize:vertical; width:100%; box-sizing:border-box; background:var(--bg); border:1px solid var(--line); padding:10px; }
  button { width:fit-content; margin-top:12px; padding:9px 18px; cursor:pointer; background:#343b46; color:var(--ink); border:1px solid #566476; font:inherit; }
  [role=alert] { color:#ffb5b5; margin-top:12px; }
  :focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
  .network { min-width:0; overflow-wrap:anywhere; }
  @media(pointer:coarse) {
    button,summary { min-height:44px; min-width:44px; }
    input,textarea { font-size:16px; min-height:44px; }
  }
</style>
