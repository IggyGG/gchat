<script lang="ts">
  import { toCanvas } from 'qrcode';
  let { link }: {link:string}=$props();
  let canvas=$state<HTMLCanvasElement>(), error=$state('');
  $effect(()=>{
    if (!canvas) return;
    let active=true;
    void toCanvas(canvas,link,{errorCorrectionLevel:'M',margin:4,scale:4}).catch(()=>{if(active) error='QR unavailable. Copy the link or save the original card.';});
    return ()=>active=false;
  });
</script>
{#if error}<p role="status">{error}</p>{:else}<canvas bind:this={canvas} aria-label="Invitation QR code"></canvas><p>Scan with a camera to open GChat. Anyone with this code can use the invitation.</p>{/if}
<style>canvas{max-width:min(100%,340px);height:auto!important;display:block;background:white;image-rendering:pixelated}p{font-size:13px;line-height:1.5}</style>
