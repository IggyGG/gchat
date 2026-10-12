<script lang="ts">
  import type { Delivery, Member, MessageKind, ActionResult } from './api';
  import MessageText from './MessageText.svelte';
  import MessageResult from './MessageResult.svelte';
  let { timestamp, nickname, text, members, mine = false, highlighted = false, focused = false,
    kind, delivery, state, checking = false, result, details, edit }: {
    timestamp: number; nickname: string; text: string; members: Member[];
    mine?: boolean; highlighted?: boolean; focused?: boolean; kind?: MessageKind;
    delivery?: Delivery | null; state?: 'pending' | 'complete' | 'unknown' | 'rejected';
    checking?: boolean; result?: ActionResult | null; details?: () => void; edit?: () => void;
  } = $props();
  const legacyAction = $derived(text.startsWith('\u0001ACTION ') && text.endsWith('\u0001'));
  const action = $derived(kind === 'action' || legacyAction);
  const status = $derived(checking ? 'Checking…' : state === 'pending' ? 'Sending…' : state === 'unknown' ? 'Outcome unconfirmed' : state === 'rejected' ? 'Not sent' : delivery === 'delivered' ? 'delivered' : delivery === 'service_accepted' ? 'stored by service' : delivery === 'failed' ? 'failed' : delivery || state === 'complete' ? 'accepted locally' : '');
  const explanation = $derived(delivery === 'delivered' ? 'Acknowledged by the recipients of this message; not a read receipt' : delivery === 'service_accepted' ? 'Stored by the ciphertext service; recipient delivery is not confirmed' : delivery === 'failed' || state === 'rejected' ? 'This send was refused. Review the details before editing.' : state === 'unknown' ? 'The original request may have succeeded. Check its status before sending again.' : 'Accepted by this instance; recipient delivery is not confirmed');
</script>
<div class="message" class:mine class:highlighted class:focused class:attention={state === 'unknown' || state === 'rejected' || delivery === 'failed'}>
  <time title={new Date(timestamp * 1000).toLocaleString()}>[{new Date(timestamp * 1000).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit' })}]</time><bdi class="nick">{action ? `* ${nickname}` : kind === 'notice' ? `-${nickname}-` : `<${nickname}>`}</bdi><span class="body"><MessageText text={legacyAction ? text.slice(8, -1) : text} {members} /></span>{#if status}<small class="acceptance" title={explanation} aria-label={explanation}> · {status}</small>{/if}
  {#if details}<button class="message-action" onclick={details} aria-label={`Details for message from ${nickname}`}>Details</button>{/if}
  {#if edit}<button class="message-action" onclick={edit}>{state === 'rejected' ? 'Edit message' : 'Edit as new'}</button>{/if}
  {#if result}<MessageResult {result} />{/if}
</div>
<style>
  .message { padding:2px 0; overflow-wrap:anywhere; line-height:var(--chat-leading,1.45); }
  time { color:var(--muted); font-size:.875em; margin-inline-end:.65em; white-space:nowrap; }
  .nick { color:var(--nick,#a9c7e8); margin-inline-end:.5em; }
  .mine .nick { color:var(--self); font-weight:bold; }
  .body { white-space:pre-wrap; overflow-wrap:anywhere; unicode-bidi:plaintext; }
  .acceptance { color:var(--muted); font:12px/1.4 var(--ghost-font); }
  .attention .acceptance { color:var(--ghost-warning); }
  .highlighted,.focused { background:color-mix(in srgb,var(--accent) 12%,transparent); box-shadow:inset 2px 0 var(--accent); }
  .message-action { font:12px/1.4 var(--ghost-font); color:var(--accent); border:0; background:transparent; padding:2px 6px; min-height:24px; cursor:pointer; text-decoration:underline; }
  button:focus-visible { outline:2px solid var(--accent); outline-offset:1px; }
  @media(pointer:coarse) { .message-action { min-height:44px; } }
</style>
