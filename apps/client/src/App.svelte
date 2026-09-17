<script lang="ts">
  import { Attachment } from '@gchat/ui';
  import { httpExchange, type Exchange } from '@gchat/ui/transport';
  import { invoke, isTauri } from '@tauri-apps/api/core';
  import { httpTransport, type RpcTransport } from '@gchat/ui/rpc';
  const exchange: Exchange = isTauri() ? envelope => invoke('chat_request', { envelope }) : httpExchange('/_gchat');
  const rpcTransport: RpcTransport = isTauri() ? { destination: 'tauri:chat-rpc', limit: 16 * 1024 * 1024, exchange: request => invoke('chat_rpc', { request }) } : httpTransport('/_gchat_rpc');
</script>
<Attachment {exchange} {rpcTransport} />
<style>:global(body) { margin:0; background:#1c1e22; }</style>
