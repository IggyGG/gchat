<script lang="ts">
  import EntryFrame from './EntryFrame.svelte';
  import ResizeHandles from './ResizeHandles.svelte';
  import type { NativeShell } from './native-shell';
  import { onMount, type Snippet } from 'svelte';
  import type { FileAccess } from './files';
  import type { DeviceUnlock } from './device-unlock';
  import Workspace from './Workspace.svelte';
  import { attach, chatError, type ChatError, type Exchange, type Transport } from './transport';
  import { attachRpc, type RpcTransport } from './rpc-transport';
  let { exchange, rpcTransport, expectedInstance, tools, fileAccess, deviceUnlock, nativeShell, pendingInvitation, consumeInvitation, discardInvitations }: { exchange: Exchange; rpcTransport?: RpcTransport; expectedInstance?: string; tools?: Snippet; fileAccess?: FileAccess; deviceUnlock?: DeviceUnlock; nativeShell?: NativeShell; pendingInvitation?: string; consumeInvitation?: () => void; discardInvitations?: () => void } = $props();
  let transport = $state<Transport>();
  let error = $state<ChatError>();
  let running = false, connecting = false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  onMount(() => {
    running = true; void connect();
    const online = () => { if (!error || error.retryable) void connect(); };
    window.addEventListener('online', online);
    return () => { running = false; clearTimeout(timer); window.removeEventListener('online', online); };
  });
  async function connect() {
    if (!running || connecting || transport) return;
    clearTimeout(timer); connecting = true;
    try { const next = await (rpcTransport ? attachRpc(exchange, rpcTransport, expectedInstance) : attach(exchange, expectedInstance)); if (running) { transport = next; error = undefined; } }
    catch (failure) { if (running) { error = chatError(failure); if (error.retryable) timer = setTimeout(connect, 1500); } }
    finally { connecting = false; }
  }
</script>
{#if transport}<Workspace {transport} {tools} {fileAccess} {deviceUnlock} {nativeShell} {pendingInvitation} {consumeInvitation} {discardInvitations} />{:else}
  <main><ResizeHandles shell={nativeShell} />{#if nativeShell && !nativeShell.mac}<nav aria-label="Window controls"><button onclick={() => void nativeShell?.minimize()}>−</button><button onclick={() => void nativeShell?.maximize()}>□</button><button onclick={() => void nativeShell?.close()}>×</button></nav>{/if}<EntryFrame title="Opening your space…" description="Your conversations will be ready as soon as your installation responds.">
    <p role="status">{error ? error.retryable ? 'Reconnecting. Your identity and history are preserved.' : error.message : 'Connecting to your installation…'}</p>
    {#if error}<button onclick={() => error?.retryable ? void connect() : location.reload()}>{error.action}</button><details><summary>Connection details</summary>{error.message}</details>{/if}
  </EntryFrame>
    {#if tools}{@render tools()}{/if}
  </main>
{/if}
<style>
  main { position:relative; box-sizing:border-box; min-height:100dvh; display:grid; align-content:center; background:#1c1e22; color:#e4e7eb; padding:2rem; font:16px/1.5 ui-sans-serif,system-ui,sans-serif; }
  nav { position:absolute; right:8px; top:8px; display:flex; gap:4px; }
  button { font:inherit; min-height:44px; cursor:pointer; } details { margin-top:16px; }
</style>
