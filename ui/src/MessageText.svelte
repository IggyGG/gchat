<script lang="ts">
  import type { Member } from './api';
  import { ircFormat, formatStyle } from './irc-format';
  let { text, members }: { text: string; members: Member[] } = $props();
  const names = $derived(new Set(members.map(m => m.nickname.toLocaleLowerCase())));
  const selfNames = $derived(new Set(members.filter(m => m.isSelf).map(m => m.nickname.toLocaleLowerCase())));
  const segments = $derived(ircFormat(text));
</script>
{#each segments as segment}<span class:bold={segment.format.bold} class:italic={segment.format.italic} class:underline={segment.format.underline} style={formatStyle(segment.format)}>{#each segment.text.split(/(@[^\s@.,;:!?()[\]{}<>]+)/u) as part}{#if part.startsWith('@') && names.has(part.slice(1).toLocaleLowerCase())}<strong class="mention" class:self={selfNames.has(part.slice(1).toLocaleLowerCase())}>{part}</strong>{:else}{part}{/if}{/each}</span>{/each}
<style>.mention { color:var(--accent); font-weight:bold; }.mention.self { color:var(--self); }.bold { font-weight:bold; }.italic { font-style:italic; }.underline { text-decoration:underline; }</style>
