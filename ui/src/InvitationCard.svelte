<script lang="ts">
  import { onDestroy } from 'svelte';
  import GhostMark from './GhostMark.svelte';
  import { renderInvitationCard } from './invitation-card';
  import './theme.css';
  let { link, channel, expires, saveCard }: { link: string; channel: string; expires: number; saveCard?: (bytes: Uint8Array) => Promise<string | null> } = $props();
  let artwork: HTMLDivElement;
  let busy = $state(false), feedback = $state('');
  let alive = true;
  onDestroy(() => alive = false);
  async function save(share = false) {
    if (busy) return;
    if (expires * 1000 <= Date.now()) { feedback = 'This invitation has expired. Create a new one.'; return; }
    busy = true; feedback = '';
    try {
      const mark = artwork.querySelector('svg'); if (!mark) throw new Error('Card artwork is unavailable.');
      const bytes = await renderInvitationCard(link, channel, expires, mark);
      if (!alive) return;
      const file = new File([bytes], 'gchat-invitation.png', { type: 'image/png' });
      if (share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ title: 'GChat invitation', files: [file] }); feedback = 'Invitation card handed to the share destination.';
      } else if (saveCard) {
        const destination = await saveCard(bytes); feedback = destination ? `Invitation card saved to ${destination}` : 'Save cancelled.';
      } else {
        const url = URL.createObjectURL(file);
        const anchor = document.createElement('a'); anchor.href = url; anchor.download = file.name; anchor.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000); feedback = 'Invitation card downloaded. Share the original PNG as a file.';
      }
    } catch (failure) { if (alive) feedback = failure instanceof DOMException && failure.name === 'AbortError' ? 'Sharing cancelled.' : failure instanceof Error ? failure.message : 'Could not save this card.'; }
    finally { if (alive) busy = false; }
  }
</script>
<div class="ghost-entry invitation-card">
  <div class="face" bind:this={artwork}>
    <div class="brand"><span>GChat.</span><GhostMark /></div>
    <h3>You’re invited.</h3><p class="channel">#{channel.replace(/^#/, '')}</p>
    <p class="caption">A place for your people.</p>
    <p class="instructions">Open this original PNG in GChat to review and join.</p>
    <p class="expiry">Channel invitation expires {new Date(expires * 1000).toLocaleString()}</p>
  </div>
  <div class="actions"><button class="primary" disabled={busy} onclick={() => void save()}>{busy ? 'Preparing card…' : 'Save invitation card'}</button>{#if typeof navigator !== 'undefined' && typeof navigator.canShare === 'function'}<button disabled={busy} onclick={() => void save(true)}>Share card…</button>{/if}</div>
  <p class="hint">Share privately as a file. Screenshots and edited copies lose the invitation.</p>
  {#if feedback}<p role="status">{feedback}</p>{/if}
</div>
<style>
  .invitation-card { max-width:560px; margin:20px 0; }
  .face { background:var(--ghost-bg); border:1px solid var(--ghost-line); padding:28px; border-radius:8px; }
  .brand { display:flex; align-items:center; justify-content:space-between; color:var(--ghost-accent); font:18px monospace; --ghost-mark-size:48px; }
  h3 { font:500 30px/1.2 var(--ghost-font); margin:32px 0 12px; letter-spacing:-.03em; }
  .channel { color:var(--ghost-accent); font:21px/1.4 monospace; margin:0; overflow-wrap:anywhere; }
  .caption,.instructions,.expiry,.hint { color:var(--ghost-muted); font:13px/1.6 var(--ghost-font); }
  .instructions { border-top:1px solid var(--ghost-line); padding-top:20px; margin-top:26px; }.expiry { font-size:11px; }
  .actions { display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }
</style>
