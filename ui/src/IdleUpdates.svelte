<script lang="ts">
  import { onMount } from 'svelte';
  import type { NativeShell } from './native-shell';
  import { IdleUpdates } from './idle-updates';
  let { updates, busy }: { updates?: NativeShell['updates']; busy: boolean } = $props();
  let dialog: HTMLDialogElement;
  const controller = new IdleUpdates(() => performance.now(), active => {
    // Stop new input synchronously before the native maintenance request. A
    // draft typed during an awaited shutdown must not disappear on restart.
    if (active) dialog?.showModal(); else dialog?.close();
  });
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
<dialog bind:this={dialog} oncancel={event => event.preventDefault()} aria-label="Updating GChat">
  <p role="status">Updating GChat… Your profile is being kept.</p>
</dialog>
<style>dialog { border:1px solid #555; border-radius:8px; padding:24px; background:#24262b; color:#f1f1f1; } dialog::backdrop { background:#0009; }</style>
