<script lang="ts">
  import type { ActionResult } from './api';
  let { result }: { result: ActionResult } = $props();
  const output = $derived.by(() => {
    if (!result.outputBase64) return '';
    try { return new TextDecoder().decode(Uint8Array.from(atob(result.outputBase64), c => c.charCodeAt(0))); }
    catch { return 'Output bytes could not be displayed.'; }
  });
  function safeLink(url: string) { try { return ['http:', 'https:'].includes(new URL(url).protocol); } catch { return false; } }
</script>
<div class="action-result">
  <span class="state" title={result.messageId ? `Result for message ${result.messageId}` : undefined}>{result.state}{result.stderr ? ' · stderr' : ''}</span>
  {#if output}<pre>{output}</pre>{/if}
  {#each result.details as detail}<p>{detail}</p>{/each}
  {#each result.artifacts as artifact}{#if safeLink(artifact.url)}<a href={artifact.url} target="_blank" rel="noreferrer">{artifact.name}</a>{/if}{/each}
</div>
<style>
  .action-result { margin-top:4px; border-left:2px solid var(--line); padding:4px 10px; }
  .state { color:var(--muted); font:12px/1.5 ui-sans-serif,system-ui,sans-serif; }
  pre { font:inherit; white-space:pre-wrap; overflow-wrap:anywhere; margin:4px 0; }
  p { margin:4px 0; } a { display:inline-block; color:var(--accent); padding:8px; min-height:44px; }
</style>
