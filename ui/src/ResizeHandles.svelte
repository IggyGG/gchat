<script lang="ts">
  import type { NativeShell, ResizeDirection } from './native-shell';
  let { shell }: { shell?: NativeShell } = $props();
  const directions: ResizeDirection[] = ['North', 'South', 'East', 'West', 'NorthEast', 'NorthWest', 'SouthEast', 'SouthWest'];
</script>
{#if shell && !shell.mac}
  {#each directions as direction}
    <div class={`resize ${direction}`} role="presentation" onpointerdown={event => { if (event.button === 0) { event.preventDefault(); void shell?.resize(direction); } }}></div>
  {/each}
{/if}
<style>
  .resize { position:absolute; z-index:50; touch-action:none; }
  .North,.South { left:8px; right:8px; height:5px; cursor:ns-resize; }.North { top:0; }.South { bottom:0; }
  .East,.West { top:8px; bottom:8px; width:5px; cursor:ew-resize; }.East { right:0; }.West { left:0; }
  .NorthEast,.NorthWest,.SouthEast,.SouthWest { width:8px; height:8px; }
  .NorthEast,.SouthWest { cursor:nesw-resize; }.NorthWest,.SouthEast { cursor:nwse-resize; }
  .NorthEast { top:0; right:0; }.NorthWest { top:0; left:0; }.SouthEast { bottom:0; right:0; }.SouthWest { bottom:0; left:0; }
</style>
