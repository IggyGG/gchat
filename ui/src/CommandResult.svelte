<script lang="ts">
  import { invitationLink } from './invitation-link';
  import type { CommandOutput, DirectoryEntry } from './api';
  let { output, choose, saveInvitation, prepareCommand, helpHeading = true, invitationHeading = true }: { invitationHeading?: boolean; helpHeading?: boolean; output: CommandOutput; prepareCommand?: (usage: string) => void; choose: (entry: DirectoryEntry) => void; saveInvitation?: (invitation: string) => Promise<string | null> } = $props();
  let feedback = $state('');
  async function copy(link: string) {
    try { await navigator.clipboard.writeText(link); feedback = 'Invitation copied'; }
    catch { feedback = 'Select and copy the complete invitation below, or save it as a file.'; }
  }
  let busy = $state(false);
  async function share(link: string, channel: string) {
    busy = true; feedback = '';
    try {
      const file = new File([link], 'gchat-invitation.txt', { type: 'text/plain' });
      if (!navigator.canShare?.({ files: [file] })) { await save(link); return; }
      await navigator.share({ title: `Join #${channel}`, files: [file] });
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
    <!-- Descriptions wrap naturally, without a separate block per command. -->
    {#if helpHeading}<h2>Commands</h2>{/if}
    <ul class="commands">{#each output.commands as command}<li><button class="command" disabled={!command.available || !prepareCommand} onclick={() => prepareCommand?.(command.usage)}>{command.usage}</button><span>{' - '}{command.description}{#if !command.available} <strong>Unavailable</strong>{/if}</span></li>{/each}</ul>
  {:else if output.kind === 'directory'}
    <h2>Channels</h2>
    {#if !output.channels.length}<p>No channels found. Refresh the public directory or paste an invitation.</p>{/if}
    {#each output.channels as channel}<button onclick={() => choose(channel)}>{channel.name} · {channel.joined ? 'Open' : 'Join public channel'}</button>{/each}
  {:else if output.kind === 'invitation'}
    {@const appLink = invitationLink(output.link)}
    {#if invitationHeading}<h2>Invite to #{output.channel.replace(/^#/, '')}</h2>{/if}
    <p>Send this single-use invitation to the person you want to join. It includes the network and channel.</p>
    <p>Single use · Expires {new Date(output.expires * 1000).toLocaleString()}</p>
    {#if output.localOnly}<p>This invitation is reachable only on this computer. Configure a relay before sharing with another computer.</p>{/if}
    {#if output.expires * 1000 <= Date.now()}<p role="status">This invitation has expired. Create a new invitation to share.</p>{:else}
    <button disabled={busy} onclick={() => void copy(appLink ?? output.link)}>Copy invitation</button>
    {#if typeof navigator !== 'undefined' && typeof navigator.share === 'function'}<button disabled={busy} onclick={() => void share(output.link, output.channel)}>Share invitation file…</button>{/if}
    <button disabled={busy} onclick={() => void save(output.link)}>{saveInvitation ? 'Save as…' : 'Download file'}</button>
    {#if !appLink}<p>This invitation is too large for an app link. Share the complete code or file.</p>{/if}
    <details><summary>Complete invitation</summary><button onclick={() => void copy(output.link)}>Copy raw code</button><textarea aria-label="Complete invitation" readonly value={output.link} rows="3"></textarea></details>
    {/if}
    {#if feedback}<p role="status">{feedback}</p>{/if}
  {:else if output.kind === 'text' || output.kind === 'status'}
    <h2>{output.kind === 'status' ? 'Status' : output.title}</h2><pre>{output.text}</pre>
  {/if}
</section>
<style>
  .result { padding:8px 0; overflow-wrap:anywhere; }
  h2 { font:inherit; font-weight:600; margin:0 0 8px; } p { margin:8px 0; }
  button { font:inherit; color:var(--ink); background:transparent; border:0; text-decoration:underline; padding:8px; min-height:44px; margin:2px; cursor:pointer; }
  button:focus-visible,textarea:focus-visible,summary:focus-visible { outline:2px solid var(--accent); }
  .commands { list-style:none; padding:0; margin:0; font:inherit; }.commands li { margin:0; padding:0; line-height:inherit; }.commands span { color:var(--muted); }
  textarea { width:100%; color:var(--ink); background:var(--bg); font:inherit; resize:vertical; }
  pre { white-space:pre-wrap; font:inherit; margin:0; }
  .command { display:inline; min-height:0; min-width:0; line-height:inherit; margin:0; padding:0; color:var(--accent); }.command:disabled { color:var(--muted); cursor:default; }
</style>
