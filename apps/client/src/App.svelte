<script lang="ts">
  import { onMount } from 'svelte';
  import type { FileAccess } from '@gchat/ui/files';
  import { Attachment, type DeviceUnlock } from '@gchat/ui';
  import { httpExchange, type Exchange } from '@gchat/ui/transport';
  import { invoke, isTauri } from '@tauri-apps/api/core';
  import { listen } from '@tauri-apps/api/event';
  import { httpTransport, type RpcTransport } from '@gchat/ui/rpc';
  let deviceUnlock = $state<DeviceUnlock>();
  let lifecycleError = $state('');
  onMount(() => {
    let active = true;
    let stop: (() => void) | undefined;
    if (isTauri()) void invoke<boolean>('chat_mobile_available').then(available => {
      if (available && active) {
        deviceUnlock = { unlock: (passphrase, create, remember) => invoke('chat_mobile_unlock', { passphrase, create, remember }) };
        void listen<string>('gchat-lifecycle-error', event => { lifecycleError = event.payload; }).then(unlisten => {
          if (active) stop = unlisten; else unlisten();
        });
      }
    }).catch(() => { /* Desktop uses its existing local service. */ });
    return () => { active = false; stop?.(); };
  });
  const exchange: Exchange = isTauri() ? envelope => invoke('chat_request', { envelope }) : httpExchange('/_gchat');
  const rpcTransport: RpcTransport = isTauri() ? { destination: 'tauri:chat-rpc', limit: 16 * 1024 * 1024, exchange: request => invoke('chat_rpc', { request }) } : httpTransport('/_gchat_rpc');
  const fileAccess: FileAccess | undefined = isTauri() ? {
    exchange: async frame => new Uint8Array(await invoke<ArrayBuffer>('chat_file_io', frame)),
    save: id => invoke<string>('chat_file_save', { id }),
  } : undefined;
</script>
{#if lifecycleError}<aside role="alert">{lifecycleError}<button onclick={() => lifecycleError = ''}>Dismiss</button></aside>{/if}
<Attachment {exchange} {rpcTransport} {fileAccess} {deviceUnlock} />
<style>
  :global(body) { margin:0; background:#1c1e22; }
  aside { position:fixed; top:env(safe-area-inset-top,0px); left:0; right:0; z-index:100; padding:12px; color:#fff; background:#632b24; font:16px/1.4 system-ui; }
  aside button { margin-left:12px; min-height:44px; font:inherit; }
</style>
