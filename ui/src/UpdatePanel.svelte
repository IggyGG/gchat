<script lang="ts">
  import { onMount } from 'svelte';
  import type { NativeShell, UpdateStatus } from './native-shell';
  let { updates, busy }: { updates?: NativeShell['updates']; busy: boolean } = $props();
  let status = $state<UpdateStatus>();
  let error = $state(''), working = $state(false);
  onMount(() => {
    let alive = true;
    const poll = async () => {
      try { const value = await updates?.status(); if (alive) status = value; }
      catch { if (alive) error = 'Update status is unavailable. Try again shortly.'; }
    };
    void poll();
    const timer = setInterval(() => void poll(), 1000);
    return () => { alive = false; clearInterval(timer); };
  });
  async function action(install = false) {
    if (!updates || working || (install && busy)) return;
    working = true; error = '';
    try { if (install) await updates.install(); else status = await updates.check(); }
    catch (e) { error = String(e); }
    finally { working = false; }
  }
</script>
{#if updates}
  <p role="status">{status?.message || 'Checking update status…'}</p>
  {#if status?.version}<p>Version {status.version}</p>{/if}
  {#if status?.state === 'downloading'}<progress aria-label="Update download" max={status.total || 1} value={status.downloaded}></progress>{/if}
  <p>Updates download automatically and activate at your next launch. Your profile is kept. You may need to unlock it again after restarting.</p>
  <button disabled={working || status?.state === 'downloading'} onclick={() => void action()}>Check for updates</button>
  {#if ['ready', 'deferred'].includes(status?.state ?? '')}<button disabled={working || busy} onclick={() => void action(true)}>{working ? 'Preparing restart…' : 'Restart now'}</button>{/if}
  {#if busy}<p>Finish or save your draft and wait for current actions before restarting.</p>{/if}
  {#if status?.running}<details><summary>Running build</summary><p>{status.running.version}</p><code>{status.running.releaseId}</code></details>{/if}
{:else}
  <p>This device uses its app store or installation provider for updates. Enable automatic updates there.</p>
{/if}
{#if error}<p role="alert">{error}</p>{/if}
<style>progress { width:100%; } code { overflow-wrap:anywhere; } button { margin:0 8px 8px 0; }</style>
