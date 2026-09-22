<script lang="ts">
  import type { CommandOutput, DirectoryEntry } from './api';
  let { output, choose, saveInvitation }: { output: CommandOutput; choose: (entry: DirectoryEntry) => void; saveInvitation?: (invitation: string) => Promise<string | null> } = $props();
  let feedback = $state('');
  async function copy(link: string) {
    try { await navigator.clipboard.writeText(link); feedback = 'Invitation copied'; }
    catch { feedback = 'Select and copy the complete invitation below, or save it as a file.'; }
  }
  let busy = $state(false);
  async function share(link: string, channel: string) {
    busy = true; feedback = '';
    try {
      await navigator.share({ title: `Join #${channel}`, text: link });
      feedback = 'Invitation handed to the share destination.';
    } catch (error) {
      feedback = error instanceof DOMException && error.name === 'AbortError' ? 'Sharing cancelled.' : 'Sharing failed. You can copy the invitation instead.';
    } finally { busy = false; }
  }
  async function save(link: string) {
    busy = true; feedback = '';
    try {
      if (saveInvitation) {
        const destination = await saveInvitation(link);
        feedback = destination ? `Saved to ${destination}` : 'Save cancelled.';
      } else {
        const url = URL.createObjectURL(new Blob([link], { type: 'text/plain' }));
        const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'gchat-invitation.txt'; anchor.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        feedback = 'Download requested: gchat-invitation.txt. Check your browser downloads for its location.';
      }
    } catch (error) { feedback = `Invitation was not saved: ${error instanceof Error ? error.message : String(error)}`; }
    finally { busy = false; }
  }

</script>
<section class="result" aria-label="Command result">
  {#if output.kind === 'help'}
    <h2>Commands</h2>
    <dl>{#each output.commands as command}<dt>{command.usage}</dt><dd>{command.description}{#if !command.available} <strong>Unavailable</strong>{/if}</dd>{/each}</dl>
  {:else if output.kind === 'directory'}
    <h2>Channels</h2>
    {#if !output.channels.length}<p>No channels found. Refresh the public directory or paste an invitation.</p>{/if}
    {#each output.channels as channel}<button onclick={() => choose(channel)}>{channel.name} · {channel.joined ? 'Open' : 'Join public channel'}</button>{/each}
  {:else if output.kind === 'invitation'}
    <h2>Invite to #{output.channel.replace(/^#/, '')}</h2>
    <p>Single use · Expires {new Date(output.expires * 1000).toLocaleString()}</p>
    {#if output.localOnly}<p>This invitation is reachable only on this computer. Configure a relay before sharing with another computer.</p>{/if}
    {#if output.expires * 1000 <= Date.now()}<p role="status">This invitation has expired. Create a new invitation to share.</p>{:else}
    <button disabled={busy} onclick={() => void copy(output.link)}>Copy invitation</button>
    {#if typeof navigator !== 'undefined' && typeof navigator.share === 'function'}<button disabled={busy} onclick={() => void share(output.link, output.channel)}>Share…</button>{/if}
    <button disabled={busy} onclick={() => void save(output.link)}>{saveInvitation ? 'Save as…' : 'Download file'}</button>
    <details><summary>Complete invitation</summary><textarea aria-label="Complete invitation" readonly value={output.link} rows="3"></textarea></details>
    {/if}
    {#if feedback}<p role="status">{feedback}</p>{/if}
  {:else if output.kind === 'text' || output.kind === 'status'}
    <h2>{output.kind === 'status' ? 'Status' : output.title}</h2><pre>{output.text}</pre>
  {/if}
</section>
<style>
  .result { padding:12px; border-bottom:1px solid var(--line); overflow-wrap:anywhere; }
  h2 { font:inherit; font-weight:600; margin:0 0 8px; } p { margin:8px 0; }
  button { font:inherit; color:var(--ink); background:var(--panel); border:1px solid var(--line); padding:8px; min-height:44px; margin:2px; cursor:pointer; }
  button:focus-visible,textarea:focus-visible,summary:focus-visible { outline:2px solid var(--accent); }
  dl { margin:0; } dt { font-family:monospace; margin-top:8px; } dd { margin:2px 0 8px; color:var(--muted); }
  textarea { width:100%; color:var(--ink); background:var(--bg); font:inherit; resize:vertical; }
  pre { white-space:pre-wrap; font:inherit; margin:0; }
</style>
