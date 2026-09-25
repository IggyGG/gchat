<script lang="ts">
  import EntryFrame from './EntryFrame.svelte';
  import { readInvitationFile } from './invitation-card';
  import { onDestroy } from 'svelte';
  let { profileKey, known, creating, protocolLocked, busy, password = $bindable(''), rememberDevice = $bindable(false), mobile = false, companion = false, submit, receiveInvitation, error = '' }: {
    profileKey: string; known: boolean; creating: boolean; protocolLocked: boolean; busy: boolean; password?: string; rememberDevice?: boolean; mobile?: boolean; companion?: boolean;
    submit: (event: SubmitEvent) => void; receiveInvitation: (code: string) => void; error?: string;
  } = $props();
  let confirmation = $state(''), reveal = $state(false), localError = $state(''), invitationReady = $state(false), reading = $state(false);
  let input = $state<HTMLInputElement>();
  let alive = true, generation = 0;
  $effect(() => { profileKey; generation++; invitationReady = false; reading = false; localError = ''; confirmation = ''; });
  onDestroy(() => { alive = false; generation++; confirmation = ''; });
  async function open(file?: File) {
    if (!file || busy || reading) return;
    const revision = ++generation; reading = true; localError = '';
    try { const code = await readInvitationFile(file); if (alive && revision === generation) { receiveInvitation(code); invitationReady = true; } }
    catch (failure) { if (alive && revision === generation) localError = failure instanceof Error ? failure.message : 'Could not open this invitation.'; }
    finally { if (alive && revision === generation) reading = false; }
  }
  function unlock(event: SubmitEvent) {
    event.preventDefault(); localError = '';
    if (creating && password !== confirmation) { localError = 'The passphrases do not match. Please try again.'; return; }
    confirmation = ''; reveal = false; submit(event);
  }
</script>
<div class="arrival" role="region" aria-label="Welcome to GChat" ondragover={event => { if (event.dataTransfer?.types.includes('Files')) event.preventDefault(); }} ondrop={event => { event.preventDefault(); void open(event.dataTransfer?.files[0]); }}>
  <EntryFrame title={!known ? 'Opening your space…' : creating ? 'Make yourself at home.' : 'Welcome back.'}
    description={!known ? 'Checking your identity and saved conversations.' : creating ? 'Create a private identity for your conversations. No email or central account.' : protocolLocked ? 'Unlock your identity to reconnect and pick up where you left off.' : 'Unlock your message history. Receiving continues while it is locked.'}>
    {#if known}
      <form onsubmit={unlock} aria-busy={busy}>
        <label for="gchat-password">{creating ? 'Choose a passphrase' : protocolLocked ? 'Identity passphrase' : 'Archive passphrase'}</label>
        <div class="password"><input id="gchat-password" type={reveal ? 'text' : 'password'} autocomplete={creating ? 'new-password' : 'current-password'} bind:value={password} minlength={creating ? 8 : undefined} maxlength="4096" required disabled={busy} aria-describedby="identity-help" /><button type="button" aria-label={reveal ? 'Hide passphrase' : 'Show passphrase'} aria-pressed={reveal} onclick={() => reveal = !reveal}>{reveal ? 'Hide' : 'Show'}</button></div>
        {#if creating}<label for="gchat-confirm">Confirm passphrase</label><input id="gchat-confirm" type={reveal ? 'text' : 'password'} autocomplete="new-password" bind:value={confirmation} required disabled={busy} />{/if}
        <p id="identity-help" class="hint">{creating ? 'Keep it safe. There is no passphrase reset.' : companion ? 'This opens the identity in your connected installation.' : 'Your identity and history stay in this installation.'}</p>
        {#if mobile}<label class="remember"><input type="checkbox" bind:checked={rememberDevice} disabled={busy} />Remember on this device</label><p class="hint">Uses secure device storage to reconnect after suspension. /lock removes the saved credential.</p>{/if}
        {#if localError || error}<p role="alert">{localError || error}</p>{/if}
        <button class="primary" type="submit" disabled={busy || reading}>{busy ? 'Opening…' : creating ? 'Create identity' : protocolLocked ? 'Reconnect' : 'Unlock'}</button>
      </form>
      <div class="invitation">
        <input class="file-input" type="file" accept=".png,image/png,.txt,text/plain" aria-label="Open invitation card" bind:this={input} onchange={event => { const file = event.currentTarget.files?.[0]; event.currentTarget.value = ''; void open(file); }} />
        <button type="button" disabled={busy || reading} onclick={() => input?.click()}>{reading ? 'Opening card…' : invitationReady ? 'Choose a different invitation' : 'Open invitation card'}</button>
        <p class="hint" role="status">{invitationReady ? 'Invitation ready. After unlocking, review where it takes you before joining.' : 'Have an invitation? Open or drop the original PNG here.'}</p>
      </div>
      <details><summary>About your identity and recovery</summary><p class="hint">Your passphrase protects your identity and encrypted history. Keep it somewhere safe. To back up an existing installation, stop it first and copy its private data; keep the passphrase separately. Run gchat paths to find the data locations. <a href="https://github.com/IggyGG/gchat/blob/main/docs/INSTALL.md" target="_blank" rel="noreferrer">Installation guide</a></p></details>
    {:else}<p class="hint" role="status">{error || 'Opening GChat…'}</p>{/if}
  </EntryFrame>
</div>
<style>
  .arrival { flex:1; min-height:0; overflow:auto; display:flex; padding:32px 16px; background:radial-gradient(ellipse at 50% 20%,#b8d9c40b,transparent 65%); }
  form { display:grid; }.password { display:flex; gap:8px; }.password input { min-width:0; }.password button { flex:none; }
  .hint { color:var(--ghost-muted); font-size:13px; line-height:1.55; margin:10px 0 16px; }
  .primary { margin-top:10px; }.invitation { border-top:1px solid var(--ghost-line); margin-top:28px; padding-top:24px; }
  .invitation button { width:100%; }.file-input { display:none; }.remember { display:flex; gap:10px; align-items:center; }
  details { color:var(--ghost-muted); font-size:13px; } summary { cursor:pointer; padding:8px 0; min-height:44px; }
  @media(max-width:480px) { .arrival { padding:12px 0; } }
</style>
