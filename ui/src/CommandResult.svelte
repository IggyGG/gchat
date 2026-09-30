<script lang="ts">
  import InvitationCard from './InvitationCard.svelte';
  import EnrollmentProgress from './EnrollmentProgress.svelte';
  import type { Transport } from './transport';
  import { invitationLink } from './invitation-link';
  import type { CommandOutput, DirectoryEntry } from './api';
  let { output, transport, changed, choose, saveInvitation, saveInvitationCard, prepareCommand, executeCommand, helpHeading = true, invitationHeading = true }: { transport?: Transport; changed?: () => void; invitationHeading?: boolean; helpHeading?: boolean; output: CommandOutput; executeCommand?: (command: string) => Promise<boolean>; prepareCommand?: (usage: string) => void; choose: (entry: DirectoryEntry) => void; saveInvitation?: (invitation: string) => Promise<string | null>; saveInvitationCard?: (bytes: Uint8Array) => Promise<string | null> } = $props();
  let feedback = $state('');
  let invitationPreset = $state('friends'), days = $state(7), admissionLimit = $state(25);
  let noExpiry = $state(false), unlimited = $state(false);
  async function run(command: string) {
    if(!executeCommand || busy) return; busy=true; feedback='Saving…';
    try { feedback=await executeCommand(command)?'':'Could not complete this request. Open Details for the error.'; }
    catch(error){feedback=String(error);}finally{busy=false;}
  }
  let recoverySelection = $state<string[]>([]);
  let recoveryConfirmed = $state(false);
  let recoveryPreview = '';
  $effect(() => {
    const next = output.kind === 'membership_recovery' ? `${output.expected}:${output.epoch}` : '';
    if (next === recoveryPreview) return;
    recoveryPreview = next;
    recoverySelection = []; recoveryConfirmed = false; feedback = '';
  });
  async function refreshRecovery() {
    if (!executeCommand) return;
    busy = true; feedback = 'Refreshing membership…';
    try { feedback = await executeCommand('/recover-membership') ? '' : 'Could not refresh. Check the operation details.'; }
    catch (error) { feedback = String(error); }
    finally { busy = false; }
  }
  async function recoverMembers() {
    if (output.kind !== 'membership_recovery' || !executeCommand || !recoverySelection.length) return;
    busy = true; feedback = 'Saving membership recovery…';
    const command = `/recover-membership ${output.expected} ${recoverySelection.join(' ')}`;
    try { const accepted = await executeCommand(command); feedback = accepted ? 'Recovery saved. Removed members need a new invitation.' : 'Recovery was not confirmed. Check the operation details before trying again.'; }
    catch (error) { feedback = String(error); }
    finally { busy = false; recoveryConfirmed = false; }
  }
  async function copy(link: string, reconnect = false) {
    try { await navigator.clipboard.writeText(link); feedback = reconnect ? 'Reconnect command copied. Paste it into this channel on the other device.' : 'Invitation copied'; }
    catch { feedback = reconnect ? 'Select and copy the reconnect command below.' : 'Select and copy the complete invitation below, or save it as a file.'; }
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
  {:else if output.kind === 'invitation_options'}
    <h2>Invite to #{output.channel.replace(/^#/, '')}</h2>
    <p>Choose who this invitation is for. Everyone receives their own identity and membership.</p>
    <label>Invitation for <select bind:value={invitationPreset} disabled={busy}><option value="person">One person · 1 hour · 1 join</option><option value="friends">Friends · 7 days · 25 joins</option><option value="devices">Devices · 90 days · 100 joins</option><option value="custom">Custom…</option></select></label>
    {#if invitationPreset === 'custom'}
      <label><input type="checkbox" bind:checked={noExpiry} disabled={busy} />No expiry</label>
      {#if !noExpiry}<label>Valid for days <input type="number" min="1" max="36500" bind:value={days} disabled={busy} /></label>{/if}
      <label><input type="checkbox" bind:checked={unlimited} disabled={busy} />No total admission limit</label>
      {#if !unlimited}<label>Maximum joins <input type="number" min="1" max="5000000" bind:value={admissionLimit} disabled={busy} /></label>{/if}
    {/if}
    <p>The owner must be online to admit people. Anyone with the invitation can join until its limit or expiry. You can revoke it at any time. Device invitations do not grant permission to run commands.</p>
    <button disabled={busy || !executeCommand} onclick={() => void run(invitationPreset === 'custom' ? `/invite custom ${noExpiry ? 'never' : days} ${unlimited ? 'unlimited' : admissionLimit}` : `/invite ${invitationPreset}`)}>{busy ? 'Creating…' : 'Create invitation'}</button>
    <button disabled={busy || !executeCommand} onclick={() => void run('/invites')}>Manage invitations</button>
    {#if feedback}<p role="status">{feedback}</p>{/if}
  {:else if output.kind === 'invitations'}
    <h2>Invitations · #{output.channel.replace(/^#/, '')}</h2>
    {#if !output.records.length}<p>No saved invitations.</p>{/if}
    {#each output.records as record (record.id)}
      <article><p><strong>{record.revoked ? 'Revoked' : record.expires !== null && record.expires * 1000 <= Date.now() ? 'Expired' : 'Active'}</strong> · {record.admitted}{record.limit === null ? ' joins · no total limit' : ` / ${record.limit} joins`}{record.pending ? ` · ${record.pending} confirming` : ''}</p>
      <p>{record.expires === null ? 'No expiry' : `Expires ${new Date(record.expires * 1000).toLocaleString()}`}</p>
      {#if !record.revoked}<button disabled={busy || !executeCommand} onclick={() => void run(`/share-invite ${record.id}`)}>Share</button><button disabled={busy || !executeCommand} onclick={() => void run(`/revoke-invite ${record.id}`)}>Revoke</button>{:else if !record.pending}<button disabled={busy || !executeCommand} onclick={() => void run(`/retire-invite ${record.id}`)}>Remove from list</button>{/if}
      <details><summary>Details</summary><code>{record.id}</code><p>Revoking prevents new joins. Current members and already accepted joins keep their access. Removing a member does not refund a join.</p></details></article>
    {/each}
    <button disabled={busy || !executeCommand} onclick={() => void run('/invite')}>New invitation</button><button disabled={busy || !executeCommand} onclick={() => void run('/invites')}>Refresh</button>
    {#if feedback}<p role="status">{feedback}</p>{/if}
  {:else if output.kind === 'enrollment'}
    {#key output.id}<EnrollmentProgress initial={output} {transport} {changed} />{/key}
  {:else if output.kind === 'enrollments'}
    <h2>Saved channel joins</h2>
    {#if !output.entries.length}<p>No saved joins.</p>{/if}
    {#each output.entries as entry}{#if entry.kind === 'enrollment'}{#key entry.id}<EnrollmentProgress initial={entry} {transport} {changed} />{/key}{/if}{/each}
  {:else if output.kind === 'membership_recovery'}
    <h2>Channel recovery · {output.channel}</h2>
    <button disabled={busy || !executeCommand} onclick={() => void refreshRecovery()}>Refresh preview</button>
    <p>{output.pending ? 'Waiting for members to confirm the last membership change. GChat continues retrying in the background.' : 'No membership change is waiting for confirmation.'}</p>
    <p>Remove members only when they should no longer belong to this channel. They lose access to future messages and will need a fresh invitation to return. History stays.</p>
    {#each output.members.filter(member => !member.isSelf) as member (member.id)}
      <label class="recovery-member"><input type="checkbox" value={member.id} bind:group={recoverySelection} disabled={busy} onchange={() => recoveryConfirmed = false} />{member.nickname}<small>{member.missingCommit ? 'Membership confirmation missing' : 'Current member'}{member.pendingMessages ? ` · ${member.pendingMessages} unconfirmed messages` : ''}</small></label>
    {/each}
    {#if output.members.length === 1}<p>You are the only member. You can send messages and create a new invitation.</p>{/if}
    {#if output.retained_messages}<p>{output.retained_messages} saved messages remain unconfirmed. Removing a member does not mark their messages delivered.</p>{/if}
    {#if recoverySelection.length}
      {#if recoveryConfirmed}<p>Remove {recoverySelection.length} selected members from this channel?</p><button disabled={busy || !executeCommand} onclick={() => void recoverMembers()}>Confirm removal</button><button disabled={busy} onclick={() => recoveryConfirmed = false}>Cancel</button>
      {:else}<button disabled={busy || !executeCommand} onclick={() => recoveryConfirmed = true}>Remove selected members…</button>{/if}
    {/if}
    <details><summary>Details</summary><p>Membership version: {output.epoch}</p>{#each output.members as member}<p>{member.nickname}: {member.id}</p>{/each}</details>
    {#if feedback}<p role="status">{feedback}</p>{/if}
  {:else if output.kind === 'directory'}
    <h2>Channels</h2>
    {#if !output.channels.length}<p>No channels found. Refresh the public directory or paste an invitation.</p>{/if}
    {#each output.channels as channel}<button onclick={() => choose(channel)}>{channel.name} · {channel.joined ? 'Open' : 'Join public channel'}</button>{/each}
  {:else if output.kind === 'invitation' || output.kind === 'reusable_invitation'}
    {@const appLink = invitationLink(output.link)}
    {#if invitationHeading}<h2>Invite to #{output.channel.replace(/^#/, '')}</h2>{/if}
    <p>{output.kind === 'invitation' ? 'Send this single-use invitation to the person you want to join.' : 'Share this invitation privately with the people or devices you want to join.'} It includes the network and channel.</p>
    <p>{output.kind === 'invitation' ? 'Single use' : output.limit === null ? 'No total admission limit' : `${output.limit} distinct joins`} · {output.expires === null ? 'No expiry' : `Expires ${new Date(output.expires * 1000).toLocaleString()}`}</p>
    {#if output.localOnly}<p>This invitation is reachable only on this computer. Configure a relay before sharing with another computer.</p>{/if}
    {#if output.expires !== null && output.expires * 1000 <= Date.now()}<p role="status">This invitation has expired. Create a new invitation to share.</p>{:else}
    <InvitationCard link={output.link} channel={output.channel} expires={output.expires} saveCard={saveInvitationCard} />
    <button disabled={busy} onclick={() => void copy(appLink ?? output.link)}>Copy invitation</button>
    {#if typeof navigator !== 'undefined' && typeof navigator.share === 'function'}<button disabled={busy} onclick={() => void share(output.link, output.channel)}>Share invitation file…</button>{/if}
    <button disabled={busy} onclick={() => void save(output.link)}>{saveInvitation ? 'Save as…' : 'Download file'}</button>
    {#if !appLink}<p>This invitation is too large for an app link. Share the complete code or file.</p>{/if}
    <details><summary>Complete invitation</summary><button onclick={() => void copy(output.link)}>Copy raw code</button><textarea aria-label="Complete invitation" readonly value={output.link} rows="3"></textarea></details>
    {/if}
    {#if feedback}<p role="status">{feedback}</p>{/if}
  {:else if output.kind === 'text' && output.title === 'Reconnect this channel' && output.text.startsWith('gchat-reconnect1:')}
    <h2>Reconnect this channel</h2>
    <p>Use this only when existing members cannot receive each other's messages. It preserves your channel, identity and saved messages.</p>
    <p>Copy this command to the other device using another app. Paste and send it in the same GChat channel there while both devices are connected. This is not an invitation and cannot add a member.</p>
    <button onclick={() => void copy(`/reconnect ${output.text}`, true)}>Copy reconnect command</button>
    <details><summary>Complete reconnect command</summary><textarea aria-label="Reconnect command" readonly value={`/reconnect ${output.text}`} rows="3"></textarea></details>
    {#if feedback}<p role="status">{feedback}</p>{/if}
  {:else if output.kind === 'text' || output.kind === 'status'}
    <h2>{output.kind === 'status' ? 'Status' : output.title}</h2><pre>{output.text}</pre>
  {/if}
</section>
<style>
  select,input { font:inherit; max-width:100%; color:var(--ink); background:var(--bg); border:1px solid var(--line); padding:8px; } label { display:block; margin:12px 0; } article { border-bottom:1px solid var(--line); padding:12px 0; }
  .recovery-member { display:flex; flex-wrap:wrap; align-items:center; gap:8px; padding:8px 0; min-height:44px; }.recovery-member small { color:var(--muted); }
  .result { padding:8px 0; overflow-wrap:anywhere; }
  h2 { font:inherit; font-weight:600; margin:0 0 8px; } p { margin:8px 0; }
  button { font:inherit; color:var(--ink); background:transparent; border:0; text-decoration:underline; padding:8px; min-height:44px; margin:2px; cursor:pointer; }
  button:focus-visible,textarea:focus-visible,summary:focus-visible { outline:2px solid var(--accent); }
  .commands { list-style:none; padding:0; margin:0; font:inherit; }.commands li { margin:0; padding:0; line-height:inherit; }.commands span { color:var(--muted); }
  textarea { width:100%; color:var(--ink); background:var(--bg); font:inherit; resize:vertical; }
  pre { white-space:pre-wrap; font:inherit; margin:0; }
  .command { display:inline; min-height:0; min-width:0; line-height:inherit; margin:0; padding:0; color:var(--accent); }.command:disabled { color:var(--muted); cursor:default; }
</style>
