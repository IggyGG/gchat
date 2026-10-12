<script lang="ts">
  import type { Activity } from './api';
  import { activitySummary } from './timeline';
  let { activities }: { activities: Activity[] } = $props();
  const first = $derived(activities[0]);
  const warning = $derived(activities.some(a => ['send_failed', 'operation_failed', 'unavailable', 'removed'].includes(a.kind)));
</script>
<div class="activity" class:warning>
  <time>[{new Date(first.timestamp * 1000).toLocaleTimeString([], { hour12:false, hour:'2-digit', minute:'2-digit' })}]</time>
  {#if activities.length > 1}
    <details><summary>*** {activities.length} channel updates</summary>{#each activities as activity (activity.id)}<p data-timeline-key={activity.id}>{activity.text}</p>{/each}</details>
  {:else if activitySummary(first) !== first.text}
    <details><summary>*** {activitySummary(first)}</summary><p>{first.text}</p></details>
  {:else}<span>*** {first.text}</span>{/if}
</div>
<style>
  .activity { display:flex; align-items:baseline; gap:.65em; padding:1px 0; color:var(--muted); font-size:.875em; overflow-wrap:anywhere; }
  time { flex:none; white-space:nowrap; } details,span { min-width:0; } summary { cursor:pointer; } p { margin:4px 0; white-space:pre-wrap; }
  .warning { color:var(--ghost-warning); } summary:focus-visible { outline:2px solid var(--accent); }
</style>
