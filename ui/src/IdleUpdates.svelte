<script lang="ts">
  import { onMount } from 'svelte';
  import type { NativeShell } from './native-shell';
  import { IdleUpdates } from './idle-updates';
  let { updates, busy }: { updates?: NativeShell['updates']; busy: boolean } = $props();
  const controller = new IdleUpdates();
  $effect(() => { if (busy) controller.activity(); });
  onMount(() => {
    let alive = true;
    const activity = () => controller.activity();
    for (const name of ['pointerdown', 'keydown', 'input', 'wheel']) window.addEventListener(name, activity, { capture: true, passive: true });
    const timer = setInterval(() => void controller.poll(updates, () => !alive || busy), 2000);
    return () => {
      alive = false;
      clearInterval(timer);
      for (const name of ['pointerdown', 'keydown', 'input', 'wheel']) window.removeEventListener(name, activity, { capture: true });
    };
  });
</script>
