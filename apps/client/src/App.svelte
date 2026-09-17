<script lang="ts">
  import type { FileAccess } from '@gchat/ui/files';
  import { Attachment } from '@gchat/ui';
  import { httpExchange, type Exchange } from '@gchat/ui/transport';
  import { invoke, isTauri } from '@tauri-apps/api/core';
  import { httpTransport, type RpcTransport } from '@gchat/ui/rpc';
  const exchange: Exchange = isTauri() ? envelope => invoke('chat_request', { envelope }) : httpExchange('/_gchat');
  const rpcTransport: RpcTransport = isTauri() ? { destination: 'tauri:chat-rpc', limit: 16 * 1024 * 1024, exchange: request => invoke('chat_rpc', { request }) } : httpTransport('/_gchat_rpc');
  const fileAccess: FileAccess | undefined = isTauri() ? {
    exchange: async frame => new Uint8Array(await invoke<ArrayBuffer>('chat_file_io', frame)),
    save: id => invoke<string>('chat_file_save', { id }),
  } : undefined;
</script>
<Attachment {exchange} {rpcTransport} {fileAccess} />
<style>:global(body) { margin:0; background:#1c1e22; }</style>
