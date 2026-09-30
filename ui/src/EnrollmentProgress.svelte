<script lang="ts">
  import { onDestroy, onMount, untrack } from 'svelte';
  import type { CommandOutput } from './api';
  import type { Transport } from './transport';
  let { initial, transport, changed }: { initial: Extract<CommandOutput, {kind:'enrollment'}>; transport?: Transport; changed?: () => void } = $props();
  let status = $state(untrack(() => initial)), busy = $state(false), error = $state(''), retired=$state(false);
  let alive=true;
  onDestroy(()=>alive=false);
  const labels: Record<string,string> = {waiting_network:'Connecting to the network',waiting_owner:'Waiting for the channel owner',verifying_return_route:'Checking the reply route',awaiting_admission:'Waiting for the owner to admit you',applying_membership:'Saving your channel membership',joined:'Joined',cancelled:'Cancelled'};
  async function update(action='status') {
    if (!transport || busy) return;
    busy=true;
    try {
      const response=await transport.request({kind:'enrollment',id:initial.id,action});
      if (!alive) return;
      if (response.kind==='error') throw new Error(response.message);
      if (response.kind==='output' && response.output.kind==='enrollment') {
        const complete=status.phase!=='joined' && response.output.phase==='joined';
        status=response.output; error='';
        if (complete) changed?.();
      }
      if (response.kind==='applied') {retired=true;error='';changed?.();}
    } catch(failure) {if(alive) error=failure instanceof Error?failure.message:String(failure);}
    finally {if(alive) busy=false;}
  }
  // Parent snapshots replace transport wrappers frequently. Keep the timer
  // tied to the component lifetime so refreshes cannot postpone polling forever.
  onMount(()=>{
    const timer=setInterval(()=>{if(!retired && !['joined','cancelled'].includes(status.phase)) void update();},2000);
    return ()=>clearInterval(timer);
  });
</script>
<section aria-label="Saved channel join">
{#if retired}<p role="status">Completed request removed. Your channel membership is unchanged.</p>{:else}
  <h3>{status.channel ? `Join #${status.channel.replace(/^#/,'')}` : 'Join channel'}</h3>
  <p role="status">{labels[status.phase]??status.phase}</p>
  {#if !['joined','cancelled'].includes(status.phase)}
    <progress aria-label="Channel join in progress"></progress>
    <p>Your identity and join request are saved. You can close this screen; GChat retries while it is running. The owner must be online.</p>
    <button disabled={busy || !transport} onclick={()=>void update('resume')}>Retry now</button>
    <button disabled={busy || !transport} onclick={()=>void update('cancel')}>Cancel join</button>
  {:else}
    <p>{status.phase==='joined' ? 'Your channel is available in Channels.' : 'This join was cancelled before admission.'}</p>
    <button disabled={busy || !transport} onclick={()=>void update('retire')}>Remove completed request</button>
  {/if}
  {#if status.message}<p>{status.message}</p>{/if}
  {#if error}<p role="alert">{error}</p>{/if}
  <details><summary>Details</summary><p>Request {status.id} · {status.attempts} attempts</p></details>
{/if}
</section>
<style>
section{max-width:38rem}h3{font:inherit;font-weight:600}p{line-height:1.5}button{font:inherit;margin:4px;padding:10px;min-height:44px;color:inherit;background:transparent;border:1px solid var(--line)}progress{width:100%}
</style>
