<script lang="ts">
  let { text, query }: { text: string; query: string } = $props();
  const parts = $derived.by(() => {
    const result: { text:string; match:boolean }[] = [];
    const needle = query.trim();
    if (!needle) return [{ text, match:false }];
    // Escaped literal matches keep indices in the original Unicode text.
    const pattern = new RegExp(needle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'giu');
    let start = 0;
    for (const match of text.matchAll(pattern)) {
      const index = match.index!;
      result.push({ text:text.slice(start,index), match:false }, { text:match[0], match:true });
      start = index + match[0].length;
    }
    result.push({ text:text.slice(start), match:false });
    return result;
  });
</script>
{#each parts as part}{#if part.match}<mark>{part.text}</mark>{:else}{part.text}{/if}{/each}
<style>mark { background:var(--accent); color:var(--bg); border-radius:2px; }</style>
