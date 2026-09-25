<script lang="ts">
  import type { Snippet } from 'svelte';
  import GhostMark from './GhostMark.svelte';
  import './theme.css';
  let { title, description = '', eyebrow = 'GChat.', children }: { title: string; description?: string; eyebrow?: string; children?: Snippet } = $props();
</script>
<section class="ghost-entry" aria-label={title}>
  <div class="entry-mark" aria-hidden="true"><GhostMark /></div>
  <p class="eyebrow">{eyebrow}</p>
  <h1>{title}</h1>
  {#if description}<p class="description">{description}</p>{/if}
  {#if children}{@render children()}{/if}
</section>
<style>
  section { width:min(100%,480px); margin:auto; padding:36px; }
  .entry-mark { --ghost-mark-size:48px; margin-bottom:30px; }
  .eyebrow { margin:0 0 12px; color:var(--ghost-accent); font:16px/1.4 monospace; letter-spacing:.06em; }
  h1 { color:var(--ghost-ink); font-size:clamp(28px,4vw,36px); font-weight:550; line-height:1.2; letter-spacing:-.035em; margin:0 0 16px; }
  .description { margin:0 0 24px; color:var(--ghost-muted); max-width:36ch; }
  @media(max-width:480px) { section { padding:24px; } .entry-mark { margin-bottom:22px; } }
</style>
