<script lang="ts">
  import type { Snippet } from 'svelte';
  let { title, close, children }: { title: string; close: () => void; children: Snippet } = $props();
  function present(node: HTMLDialogElement) {
    const opener = document.activeElement as HTMLElement | null;
    node.showModal();
    // Do not summon the phone keyboard before the user has read the screen.
    (node.querySelector<HTMLElement>('[data-screen-back]'))?.focus();
    return { destroy() { if (opener?.isConnected) opener.focus({ preventScroll: true }); } };
  }
</script>
<dialog use:present aria-label={title} oncancel={event => { event.preventDefault(); close(); }}>
  <header><button data-screen-back aria-label="Close dialog" onclick={close}>‹ Back</button><h2>{title}</h2></header>
  <div class="screen-body">{@render children()}</div>
</dialog>
<style>
  dialog { box-sizing:border-box; color:var(--ink,#e4e7eb); background:var(--panel,#25282e); border:1px solid var(--line,#363c44); padding:0; width:min(640px,calc(100vw - 48px)); max-width:none; max-height:calc(100dvh - 48px); overflow:auto; border-radius:8px; }
  dialog::backdrop { background:#000a; }
  header { display:flex; align-items:center; gap:16px; position:sticky; top:0; z-index:2; background:var(--panel,#25282e); padding:12px 16px; border-bottom:1px solid var(--line,#363c44); }
  h2 { margin:0; font:600 18px/1.4 system-ui; overflow-wrap:anywhere; }
  button { font:inherit; color:inherit; background:transparent; border:0; min-height:44px; min-width:44px; padding:8px; cursor:pointer; }
  button:focus-visible { outline:2px solid var(--accent,#b7cbe4); }
  .screen-body { padding:20px; overflow-wrap:anywhere; }
  .screen-body :global(form) { display:grid; gap:10px; }
  .screen-body :global(input:not([type=checkbox])),.screen-body :global(textarea),.screen-body :global(select) { box-sizing:border-box; width:100%; max-width:100%; font:inherit; color:inherit; background:var(--bg,#1c1e22); border:1px solid var(--line,#363c44); padding:10px; min-height:44px; }
  .screen-body :global(button) { min-height:44px; }
  .screen-body :global(.primary) { position:sticky; bottom:0; background:var(--panel,#25282e); z-index:1; }
  @media(max-width:640px) {
    dialog { position:fixed; margin:0; inset:var(--gchat-viewport-top,0px) 0 auto; width:100%; height:var(--gchat-viewport-height,100dvh); max-height:none; border:0; border-radius:0; padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left); }
    .screen-body :global(input:not([type=checkbox])),.screen-body :global(textarea),.screen-body :global(select) { font-size:16px; }
  }
</style>
