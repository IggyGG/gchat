<script lang="ts">
  import type { Member } from './api';
  let { text, members }: { text: string; members: Member[] } = $props();
  const names = $derived(new Set(members.map(m => m.nickname.toLocaleLowerCase())));
  const selfNames = $derived(new Set(members.filter(m => m.isSelf).map(m => m.nickname.toLocaleLowerCase())));
  const parts = $derived(text.split(/(@[^\s@.,;:!?()[\]{}<>]+)/u));
</script>
{#each parts as part}{#if part.startsWith('@') && names.has(part.slice(1).toLocaleLowerCase())}<strong class="mention" class:self={selfNames.has(part.slice(1).toLocaleLowerCase())}>{part}</strong>{:else}{part}{/if}{/each}
<style>.mention { color:var(--accent); font-weight:bold; }.mention.self { color:var(--self); }</style>
