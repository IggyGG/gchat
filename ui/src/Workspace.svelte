<script lang="ts">
  import { onMount, tick, type Snippet } from 'svelte';
  import type { OperationHandle } from '@gcoms/rpc';
  import type { CommandOutput, Completion, DirectoryEntry, Message, Request, Response, Snapshot } from './api';
  import CommandResult from './CommandResult.svelte';
  import GhostMark from './GhostMark.svelte';
  import NetworkSetup from './NetworkSetup.svelte';
  import MessageResult from './MessageResult.svelte';
  import { chatError, type ChatError, type Transport } from './transport';
  import { MAX_INPUT_BYTES } from './api';
  import { ConversationViews, inputError, shouldComplete, readNavigation, writeNavigation } from './view-state';

  let { transport, tools }: { transport: Transport; tools?: Snippet } = $props();
  let snapshot = $state<Snapshot>();
  let selected = $state<string | null>(null);
  let messages = $state<Message[]>([]);
  let before = $state<string | null>(null);
  let unreadMarkers = $state<Record<string, string>>({});
  let searchOpen = $state(false);
  let searchText = $state('');
  let searchResults = $state<Message[]>([]);
  let searchBefore = $state<string | null>(null);
  let searchBusy = $state(false);
  let searchError = $state('');
  let searchGeneration = 0;
  let draft = $state('');
  let password = $state('');
  let lifecycleBusy = $state(false);
  let pending = $state<Record<string, string>>({});
  const busy = $derived(lifecycleBusy || !!pending[selected ?? '']);
  type FailedOperation = { request: Extract<Request, { kind: 'submit' }>; code: string; message: string };
  let failures = $state<FailedOperation[]>([]);
  let savedOperations = $state<OperationHandle[]>([]);
  let recoveryMessages = $state<Record<string, string>>({});
  let checkingSaved = $state<Record<string, boolean>>({});
  const checkedSaved = new Set<string>();
  let notice = $state('');
  let outputs = $state<Record<string, CommandOutput[]>>({});
  let hidden = $state<string[]>([]);
  let browse = $state(false);
  let directory = $state<CommandOutput>();
  let offline = $state(false);
  let connectionError = $state<ChatError>();
  let channelsOpen = $state(false);
  let membersOpen = $state(false);
  let dialog = $state<'join' | 'create' | null>(null);
  let destination = $state('');
  let nickname = $state('');
  let joinError = $state('');
  let joinBusy = $state(false);
  let joinRequest: Extract<Request, { kind: 'submit' }> | undefined;
  const views = new ConversationViews();
  let completions = $state<Completion[]>([]);
  let historyPosition: number | undefined;
  let savedDraft = '';
  let transcript = $state<HTMLDivElement>();
  let composer = $state<HTMLTextAreaElement>();
  let moreMenu = $state<HTMLDetailsElement>();
  let running = true;
  let generation = 0;
  let snapshotGeneration = 0;
  let atBottom = $state(true);
  let loadingHistory = $state(false);
  let historyStale = false;
  let restoredSelection = false;
  let readableFont = $state(false);
  let navigationOpener: HTMLElement | null = null;
  const active = $derived(snapshot?.conversations.find(c => c.id === selected));
  const locked = $derived(snapshot?.instance.locked ?? true);
  const creating = $derived(snapshot?.instance.protocolLocked ? !snapshot.instance.profileExists : !snapshot?.instance.archiveExists);
  const title = $derived(active?.name ?? 'Status');
  const draftError = $derived(inputError(draft, draft.startsWith('/') ? MAX_INPUT_BYTES : active?.inputLimitBytes ?? MAX_INPUT_BYTES));
  function failureTarget(id: string | null) {
    const conversation = snapshot?.conversations.find(c => c.id === id);
    return conversation ? `${conversation.name}${conversation.kind === 'query' ? ` · ${conversation.topic}` : ''}` : id ? 'Original conversation' : 'Status';
  }
  function dismissFailure(id: string) { failures = failures.filter(f => f.request.operation_id !== id); }


  onMount(() => {
    running = true;
    void watch();
    const visible = () => { if (!document.hidden && (!connectionError || connectionError.retryable)) void refreshInBackground(); };
    document.addEventListener('visibilitychange', visible);
    const disconnected = () => connectionFailed(new Error('Network unavailable. Drafts and loaded history remain available.'));
    window.addEventListener('online', visible); window.addEventListener('offline', disconnected);
    return () => { running = false; generation++; password = ''; views.clear(); document.removeEventListener('visibilitychange', visible); window.removeEventListener('online', visible); window.removeEventListener('offline', disconnected); };
  });
  async function refreshInBackground() {
    try { await refresh(); }
    catch (error) { if (running) connectionFailed(error); }
  }
  function connectionFailed(error: unknown) { offline = true; connectionError = chatError(error); }
  async function refresh() {
    const revision = ++snapshotGeneration;
    const response = await transport.request({ kind: 'snapshot' });
    if (revision !== snapshotGeneration || !running || response.kind !== 'snapshot') return;
    const next = response.snapshot;
    const changed = snapshot?.revision !== next.revision;
    if ((next.instance.locked && !snapshot?.instance.locked) || (snapshot && snapshot.instance.bootId !== next.instance.bootId)) {
      generation++; searchGeneration++; views.clear(); outputs = {}; unreadMarkers = {}; messages = []; before = null; password = ''; draft = ''; savedDraft = ''; notice = ''; failures = []; completions = []; historyPosition = undefined; pending = {}; directory = undefined; destination = ''; nickname = ''; joinRequest = undefined; joinError = ''; dialog = null; searchOpen = false; searchText = ''; searchResults = []; searchBefore = null; hidden = []; restoredSelection = false;
    }
    snapshot = next;
    if (!next.instance.locked && transport.pendingOperations) {
      try {
        savedOperations = transport.pendingOperations();
        for (const handle of savedOperations) {
          const id = handle.operation.id;
          if (!checkedSaved.has(id)) { checkedSaved.add(id); void checkSaved(id); }
        }
      } catch (error) { notice = chatError(error).message; }
    } else savedOperations = [];
    if (!next.instance.locked && !restoredSelection) {
      restoredSelection = true;
      const remembered = readNavigation(next.instance.id);
      await select(remembered && (remembered.selected === null || next.conversations.some(c => c.id === remembered.selected)) ? remembered.selected : next.conversations[0]?.id ?? null);
    }
    if (selected && !next.conversations.some(c => c.id === selected)) await select(null);
    views.retain(next.conversations.map(c => c.id));
    for (const id of Object.keys(outputs)) if (id && !next.conversations.some(c => c.id === id)) delete outputs[id];
    if ((changed || historyStale || offline) && selected && !next.instance.locked) await loadHistory(false, true);
    offline = false;
    connectionError = undefined;
  }
  async function watch() {
    while (running) {
      if (connectionError && !connectionError.retryable) { await new Promise(resolve => setTimeout(resolve, 1500)); continue; }
      try {
        await refresh();
        if (!running) break;
        await transport.request({ kind: 'events', after: snapshot?.revision ?? '', wait_ms: 20000 });
      } catch (error) {
        if (!running) break;
        // Background connectivity belongs to live status, not dismissible action notices.
        connectionFailed(error);
        await new Promise(resolve => setTimeout(resolve, 1500));
      }
    }
  }
  async function select(id: string | null) {
    const fromDrawer = channelsOpen || membersOpen;
    const rememberedPosition = id && snapshot ? readNavigation(snapshot.instance.id)?.positions[id] : undefined;
    rememberPosition();
    if (id) hidden = hidden.filter(value => value !== id);
    if (id !== selected) {
      searchGeneration++; searchOpen = false; searchResults = []; searchBefore = null; searchText = ''; searchBusy = false; searchError = '';
      if (selected && atBottom) delete unreadMarkers[selected];
      views.save(selected, { draft, messages, before, scrollTop: transcript?.scrollTop ?? 0, atBottom });
      const view = views.restore(id);
      if (!views.has(id) && rememberedPosition) { view.atBottom = rememberedPosition.atBottom; view.scrollTop = rememberedPosition.top; }
      selected = id; generation++; draft = view.draft; messages = view.messages; before = view.before; atBottom = view.atBottom;
      historyPosition = undefined; savedDraft = '';
      await tick();
      if (transcript) transcript.scrollTop = view.scrollTop;
    }
    channelsOpen = false; membersOpen = false; completions = [];
    if (fromDrawer) { await tick(); composer?.focus(); }
    if (id && !locked) await loadHistory(false);
    if (id && snapshot && !views.has(id)) {
      const position = rememberedPosition;
      if (position && !position.atBottom) {
        // Rehydrate previously loaded pages before restoring a scrolled-back viewport.
        while (selected === id && before && position.oldest && !messages.some(m => m.id === position.oldest) && !historyStale) await loadHistory(true);
        if (selected === id && transcript) { atBottom = false; transcript.scrollTop = position.top; }
      }
    }
    rememberPosition();
  }
  function rememberPosition() {
    if (!snapshot || locked || !restoredSelection) return;
    const value = readNavigation(snapshot.instance.id) ?? { selected, positions: {} };
    value.selected = selected;
    if (selected && transcript) value.positions[selected] = { top: transcript.scrollTop, atBottom, oldest: messages[0]?.id ?? null };
    writeNavigation(snapshot.instance.id, value);
  }
  async function loadHistory(older: boolean, background = false) {
    const conversation = selected;
    if (!conversation || (older && !before)) return;
    const revision = ++generation;
    const scrollHeight = transcript?.scrollHeight ?? 0;
    const scrollTop = transcript?.scrollTop ?? 0;
    loadingHistory = true;
    try {
      const response = await transport.request({ kind: 'history', conversation, before: older ? before : null, limit: 200 });
      if (!running || revision !== generation || selected !== conversation || locked || response.kind !== 'history') return;
      if (!older && !unreadMarkers[conversation]) {
        const unread = snapshot?.conversations.find(c => c.id === conversation)?.unread ?? 0;
        const incoming = response.page.messages.filter(m => !m.mine);
        const first = unread ? incoming[Math.max(0, incoming.length - unread)] : undefined;
        if (first) unreadMarkers = { ...unreadMarkers, [conversation]: first.id };
      }
      // A newer snapshot can refresh the tail without erasing already loaded scrollback.
      if (older) { messages = [...response.page.messages, ...messages]; before = response.page.before; }
      else {
        const incoming = new Set(response.page.messages.map(m => m.id));
        const overlap = messages.findIndex(m => incoming.has(m.id));
        messages = overlap >= 0 ? [...messages.slice(0, overlap), ...response.page.messages] : response.page.messages;
        if (overlap < 0) before = response.page.before;
      }
      historyStale = false;
      await tick();
      if (older && transcript) transcript.scrollTop = scrollTop + transcript.scrollHeight - scrollHeight;
      else if (atBottom && transcript) transcript.scrollTop = transcript.scrollHeight;
      void markRead();
    } catch (error) {
      if (revision === generation) {
        historyStale = true;
        if (background && !active?.provider) throw error;
        if (background && active?.provider) return;
        notice = String(error);
      }
    }
    finally { if (revision === generation) loadingHistory = false; }
  }
  async function markRead() {
    if (!selected || !atBottom || document.hidden || !document.hasFocus() || locked) return;
    const last = messages.at(-1);
    if (last) try { await transport.request({ kind: 'mark_read', conversation: selected, message_id: last.id }); } catch { /* Read markers retry after the next successful refresh. */ }
  }
  async function apply(response: Response, origin = selected) {
    if (response.kind === 'output' && !locked) {
      if (response.output.kind === 'close') {
        hidden = [...hidden, response.output.conversation];
        if (selected === response.output.conversation) await select(null);
      } else {
        const key = response.conversation ?? '';
        outputs = { ...outputs, [key]: [...(outputs[key] ?? []), response.output].slice(-30) };
        if (response.output.kind === 'status' && selected === origin) await select(null);
      }
    }
    if (response.kind === 'applied' && !locked) {
      if (response.notice) notice = response.notice;
      if (response.conversation && selected === origin) await select(response.conversation);
    } else if (response.kind === 'completed' && !locked) completions = response.items;
    // Submission has already completed. Refresh failure must not turn it into a failed send.
    await refreshInBackground();
  }
  async function operation(request: Request) {
    if (moreMenu) moreMenu.open = false;
    const scope = request.kind === 'submit' ? request.conversation ?? '' : null;
    if (lifecycleBusy || (scope !== null && pending[scope])) return false;
    const origin = selected;
    if (scope === null) lifecycleBusy = true;
    else pending = { ...pending, [scope]: snapshot?.conversations.find(c => c.id === scope)?.name ?? 'Status' };
    if (request.kind === 'submit') dismissFailure(request.operation_id);
    notice = '';
    try { await apply(await transport.request(request), origin); return true; }
    catch (error) { if (!running || (locked && request.kind === 'submit')) return false; const failure = chatError(error); if (request.kind === 'submit' && !locked) failures = [...failures, { request, code: failure.code, message: failure.message }]; else notice = failure.message; return false; }
    finally { if (scope === null) lifecycleBusy = false; else { const remaining = { ...pending }; delete remaining[scope]; pending = remaining; } }
  }
  async function send(text = draft) {
    if (!text || busy || locked) return;
    const error = inputError(text, text.startsWith('/') ? MAX_INPUT_BYTES : active?.inputLimitBytes ?? MAX_INPUT_BYTES);
    if (error) { notice = error; return; }
    const request: Request = { kind: 'submit', operation_id: crypto.randomUUID(), conversation: selected, text };
    if (text === draft) draft = '';
    completions = []; historyPosition = undefined;
    await operation(request);
  }
  async function checkSaved(id: string) {
    if (!transport.checkOperation || checkingSaved[id]) return;
    checkingSaved = { ...checkingSaved, [id]: true };
    try {
      const result = await transport.checkOperation(id);
      if (!running || locked) return;
      dismissFailure(id);
      savedOperations = savedOperations.filter(h => h.operation.id !== id);
      await apply(result, selected);
    } catch (error) {
      if (!running || locked) return;
      const failure = chatError(error);
      recoveryMessages = { ...recoveryMessages, [id]: failure.message };
      failures = failures.map(f => f.request.operation_id === id ? { ...f, code: failure.code, message: failure.message } : f);
    } finally { checkingSaved = { ...checkingSaved, [id]: false }; }
  }
  function forgetSaved(id: string) {
    transport.forgetOperation?.(id);
    savedOperations = savedOperations.filter(h => h.operation.id !== id);
    dismissFailure(id);
  }
  async function editFailed(request: Extract<Request, { kind: 'submit' }>) {
    // Selection must happen before restoring text, or it becomes another channel's draft.
    await select(request.conversation);
    draft = request.text; dismissFailure(request.operation_id);
    await tick(); composer?.focus();
  }
  async function unlock(event: SubmitEvent) {
    event.preventDefault();
    const passphrase = password; password = '';
    await operation({ kind: 'unlock', passphrase, create: creating });
  }
  async function complete() {
    if (locked) return;
    const text = draft, conversation = selected;
    try {
      const response = await transport.request({ kind: 'complete', text, conversation });
      if (draft === text && selected === conversation && response.kind === 'completed') completions = response.items;
    } catch (error) { notice = String(error); }
  }
  function keydown(event: KeyboardEvent) {
    if (event.isComposing) return;
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void send(); }
    else if (shouldComplete(event, draft, completions.length > 0)) { event.preventDefault(); void complete(); }
    else if (event.key === 'Escape') { completions = []; channelsOpen = false; membersOpen = false; dialog = null; }
    else if ((event.key === 'ArrowUp' || event.key === 'ArrowDown') && !draft.includes('\n')) {
      const history = snapshot?.inputHistory.filter(item => item.conversation === selected).map(item => item.text) ?? [];
      if (!history.length) return;
      event.preventDefault();
      if (historyPosition === undefined) { historyPosition = history.length; savedDraft = draft; }
      historyPosition = Math.min(history.length, Math.max(0, historyPosition + (event.key === 'ArrowUp' ? -1 : 1)));
      draft = history[historyPosition] ?? savedDraft;
    }
  }
  function cycle(event: KeyboardEvent) {
    if (channelsOpen || membersOpen) {
      if (event.key === 'Escape') { event.preventDefault(); closeNavigation(); return; }
      if (event.key === 'Tab') {
        const buttons = [...document.querySelectorAll<HTMLButtonElement>('.gchat aside.open button:not(:disabled)')];
        const index = buttons.indexOf(document.activeElement as HTMLButtonElement);
        if (index < 0 || (!event.shiftKey && index === buttons.length - 1) || (event.shiftKey && index === 0)) {
          event.preventDefault(); buttons[event.shiftKey ? buttons.length - 1 : 0]?.focus();
        }
        return;
      }
    }
    if (event.altKey && ['ArrowLeft', 'ArrowRight'].includes(event.key)) {
      event.preventDefault();
      const ids = [null, ...snapshot?.conversations.filter(c => !hidden.includes(c.id)).map(c => c.id) ?? []];
      const index = ids.indexOf(selected);
      void select(ids[(index + ids.length + (event.key === 'ArrowRight' ? 1 : -1)) % ids.length]);
    }
  }
  function closeNavigation() { channelsOpen = false; membersOpen = false; void tick().then(() => navigationOpener?.focus()); }
  async function openNavigation(mode: 'channels' | 'members') {
    if ((mode === 'channels' && channelsOpen) || (mode === 'members' && membersOpen)) { closeNavigation(); return; }
    navigationOpener = document.activeElement as HTMLElement | null;
    channelsOpen = mode === 'channels'; membersOpen = mode === 'members';
    await tick(); document.querySelector<HTMLButtonElement>(`.gchat .${mode}.open button:not(:disabled)`)?.focus();
  }
  function showModal(node: HTMLDialogElement) {
    const opener = document.activeElement as HTMLElement | null;
    node.showModal(); node.querySelector<HTMLInputElement>('input')?.focus();
    return { destroy() { opener?.focus(); } };
  }
  function openDialog(mode: 'join' | 'create') {
    if (moreMenu) moreMenu.open = false;
    nickname ||= active?.members.find(m => m.isSelf)?.nickname ?? snapshot?.conversations.flatMap(c => c.members).find(m => m.isSelf)?.nickname ?? '';
    if (!joinBusy) { joinError = ''; dialog = mode; } else dialog = joinRequest?.text.startsWith('/create ') ? 'create' : 'join';
  }
  async function search(older = false) {
    const conversation = selected, text = searchText.trim(), revision = ++searchGeneration;
    if (!conversation || !text || locked) return;
    searchError = inputError(text, 256); if (searchError) return;
    searchBusy = true;
    try {
      const response = await transport.request({ kind: 'search', conversation, text, before: older ? searchBefore : null, limit: 200 });
      if (revision !== searchGeneration || selected !== conversation || locked || response.kind !== 'history') return;
      searchResults = older ? [...response.page.messages, ...searchResults] : response.page.messages; searchBefore = response.page.before;
    } catch (error) { if (revision === searchGeneration) searchError = chatError(error).message; }
    finally { if (revision === searchGeneration) searchBusy = false; }
  }
  async function join(event: SubmitEvent) {
    event.preventDefault();
    if (!destination || !nickname || joinBusy) return;
    const target = destination.trim(), nick = nickname.trim();
    if (/\s/.test(target)) { joinError = 'Use one invitation or channel name, without spaces.'; return; }
    if (!nick || /[\r\n\t]/.test(nick)) { joinError = 'Enter a nickname on one line.'; return; }
    const text = `/${dialog} ${target} ${nick}`;
    joinError = inputError(text, MAX_INPUT_BYTES);
    if (joinError) return;
    joinBusy = true;
    // A lost reply checks the same admitted operation, including after closing/reopening.
    if (!joinRequest || joinRequest.text !== text) joinRequest = { kind: 'submit', operation_id: crypto.randomUUID(), conversation: selected, text };
    const origin = selected, submitted = joinRequest;
    try {
      const response = await transport.request(submitted);
      if (!running || locked || joinRequest !== submitted) return;
      await apply(response, origin); dialog = null; destination = ''; joinRequest = undefined;
    } catch (error) { if (!running || locked || joinRequest !== submitted) return; const failure = chatError(error); joinError = failure.message; if (failure.code === 'rejected') joinRequest = undefined; }
    finally { joinBusy = false; }
  }
  function chooseChannel(entry: DirectoryEntry) {
    if (entry.conversation && entry.joined) { dialog = null; void select(entry.conversation); }
    else { openDialog('join'); destination = entry.conversation ?? entry.name; browse = false; }
  }
  async function loadDirectory(refreshDirectory = false) {
    joinError = ''; browse = true;
    try {
      if (refreshDirectory) await transport.request({ kind: 'submit', operation_id: crypto.randomUUID(), conversation: null, text: '/refresh' });
      const reply = await transport.request({ kind: 'submit', operation_id: crypto.randomUUID(), conversation: null, text: '/list' });
      if (reply.kind === 'output') directory = reply.output;
    } catch (error) { joinError = chatError(error).message; }
  }
  function time(timestamp: number) { return new Date(timestamp * 1000).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit' }); }
</script>

<svelte:window onkeydown={cycle} onfocus={() => void markRead()} onresize={() => { if (window.innerWidth > 760 && (channelsOpen || membersOpen)) closeNavigation(); }} />
<div class="gchat" class:unavailable={offline} class:readable={readableFont}>
  <header class="titlebar" inert={channelsOpen || membersOpen}>
    <span class="brand"><strong>GChat.</strong><GhostMark /></span><span class="instance" title={snapshot?.instance.id}>{snapshot?.instance.label ?? 'Connecting'}</span>
    <span class="connection" role="status">{offline ? connectionError && !connectionError.retryable ? connectionError.action : 'Reconnecting…' : snapshot?.instance.protocolLocked ? 'Disconnected' : locked ? 'Archive locked' : 'Attached'}</span>
  </header>
  <nav class="toolbar" aria-label="Chat actions" inert={channelsOpen || membersOpen}>
    <button class="mobile" onclick={() => void openNavigation('channels')} aria-expanded={channelsOpen}>☰ Windows</button>
    <button disabled={locked || busy} onclick={() => openDialog('join')}>Join…</button>
    {#if snapshot?.instance.capabilities.includes('ChannelAdmin')}<button class="desktop" disabled={locked || busy} onclick={() => openDialog('create')}>Create…</button>{/if}
    <button class="desktop" disabled={locked || busy} onclick={() => void send('/help')}>Help</button>
    <button class="desktop" aria-pressed={readableFont} onclick={() => readableFont = !readableFont}>Readable font</button>
    <span class="spacer"></span>
    {#if tools}{@render tools()}{/if}
    <button class="desktop" disabled={locked || lifecycleBusy} onclick={() => void operation({ kind: 'lock' })}>Lock</button>
    <button class="desktop" disabled={snapshot?.instance.protocolLocked || lifecycleBusy} onclick={() => void operation({ kind: 'disconnect' })}>Disconnect</button>
    <button class="mobile" disabled={!active?.members.length} onclick={() => void openNavigation('members')} aria-expanded={membersOpen}>Nicks</button>
    <details class="mobile more" bind:this={moreMenu}><summary>More</summary><div class="more-items">
      <button aria-pressed={readableFont} onclick={() => readableFont = !readableFont}>Readable font</button>
      {#if snapshot?.instance.capabilities.includes('ChannelAdmin')}<button disabled={locked || busy} onclick={() => openDialog('create')}>Create channel…</button>{/if}
      <button disabled={locked || busy} onclick={() => void send('/help')}>Help</button>
      <button disabled={locked || lifecycleBusy} onclick={() => void operation({ kind: 'lock' })}>Lock</button>
      <button disabled={!snapshot || snapshot.instance.protocolLocked || lifecycleBusy} onclick={() => void operation({ kind: 'disconnect' })}>Disconnect</button>
    </div></details>
  </nav>
  <div class="workspace">
    {#if channelsOpen || membersOpen}<button class="scrim" tabindex="-1" aria-label="Close navigation" onclick={closeNavigation}></button>{/if}
    <aside class="channels" class:open={channelsOpen} aria-label="Windows" role={channelsOpen ? 'dialog' : undefined} aria-modal={channelsOpen ? true : undefined}>
      {#if channelsOpen}<button onclick={closeNavigation}>Close windows</button>{/if}
      <div class="pane-label">WINDOWS</div>
      <button class:chosen={!selected} aria-current={!selected ? 'page' : undefined} onclick={() => void select(null)}><span class="symbol">◈</span> Status</button>
      {#each snapshot?.conversations.filter(c => !hidden.includes(c.id)) ?? [] as conversation (conversation.id)}
        <button class:chosen={selected === conversation.id} aria-current={selected === conversation.id ? 'page' : undefined} class:unread={conversation.unread > 0} onclick={() => void select(conversation.id)} title={conversation.topic || conversation.name}>
          <span class="symbol">{conversation.kind === 'query' ? '↳' : conversation.kind === 'archive' ? '·' : '#'}</span>
          <span class="room-name">{conversation.name.replace(/^#/, '')}</span>
          {#if conversation.unread}<span class="badge">{conversation.unread}</span>{/if}
          {#if conversation.kind === 'query'}<small>{conversation.topic}</small>{/if}
          {#if conversation.kind === 'archive'}<small>read only</small>{/if}
        </button>
      {/each}
    </aside>
    <main class="conversation" inert={channelsOpen || membersOpen}>
      {#if !locked}<NetworkSetup {transport} />{/if}
      {#if !locked && snapshot?.providerErrors?.length}<div class="provider-errors" role="status">{#each snapshot.providerErrors as error}<p>{error.retryable ? 'Conversation provider reconnecting' : 'Conversation provider blocked'}: {error.message}</p>{/each}<button onclick={() => void send('/refresh')}>Reconnect provider</button></div>{/if}
      {#if offline && connectionError?.retryable}<details class="connection-details"><summary>Connection details</summary><p>{connectionError.message}</p><button onclick={() => void refreshInBackground()}>Reconnect</button></details>{/if}
      {#if connectionError && !connectionError.retryable}<div class="notice" role="status"><span>{connectionError.message}</span><button onclick={() => { if (['instance', 'version', 'authentication'].includes(connectionError?.code ?? '')) location.reload(); else void refreshInBackground(); }}>{connectionError.action}</button></div>{/if}
      <div class="topic"><strong>{title}</strong>{#if selected && !locked}<button aria-expanded={searchOpen} onclick={() => { searchOpen = !searchOpen; }}>Find…</button>{/if}<span>{active?.topic || (active ? `${active.members.length} ${active.members.length === 1 ? 'nick' : 'nicks'}` : 'Welcome to gchat')}</span></div>
      {#if searchOpen && selected && !locked}
        <section class="search" aria-label="Find in conversation">
          <form onsubmit={event => { event.preventDefault(); void search(); }}><label for="gchat-search">Find in {title}</label><input id="gchat-search" bind:value={searchText} required /><button disabled={searchBusy}>Find</button><button type="button" onclick={() => { searchOpen = false; searchGeneration++; searchBusy = false; composer?.focus(); }}>Close search</button></form>
          {#if searchError}<p role="status">{searchError}</p>{/if}
          {#if searchBefore}<button disabled={searchBusy} onclick={() => void search(true)}>Search earlier messages</button>{/if}
          <p role="status">{searchBusy ? 'Searching…' : `${searchResults.length} matches`}</p>
          {#each searchResults as message (message.id)}<p><time>{new Date(message.timestamp * 1000).toLocaleString()}</time> &lt;{message.nickname}&gt; {message.body}</p>{/each}
        </section>
      {/if}
      {#if locked}
        <div class="welcome">
          <h1>{creating ? 'Create your GChat identity' : snapshot?.instance.protocolLocked ? 'Reconnect this instance' : 'Unlock chat'}</h1>
          <p>{creating ? 'Choose a passphrase to protect your identity and message history. Keep it safe: there is no passphrase reset.' : snapshot?.instance.protocolLocked ? 'Receiving has stopped. Enter this instance’s passphrase to reconnect.' : 'Receiving continues. Unlocking makes the archive available to attached views.'}</p>
          <form onsubmit={unlock}>
            <label for="gchat-password">{creating ? 'Choose a passphrase' : snapshot?.instance.protocolLocked ? 'Instance passphrase' : 'Archive passphrase'}</label>
            <input id="gchat-password" type="password" autocomplete={creating ? 'new-password' : 'current-password'} bind:value={password} minlength={creating ? 8 : undefined} maxlength="4096" required disabled={busy} />
            <button class="primary" type="submit" disabled={busy || !snapshot}>{busy ? 'Opening…' : creating ? 'Create identity' : snapshot?.instance.protocolLocked ? 'Reconnect' : 'Unlock'}</button>
          </form>
        </div>
      {:else if !selected}
        <div class="welcome status">
          {#if !snapshot?.conversations.length}
          <h1>Your channels. Your conversations.</h1>
          <p>After connecting to the network, join a channel with a conversation invitation and choose a nickname.</p>
          <p>Select a nick to open a private chat in that channel.</p>
          {:else}<h1>Status</h1><p>{offline ? 'Reconnecting to the selected instance. You can keep drafting.' : 'Attached to this instance. Closing this view keeps receiving messages.'}</p>{/if}
          <dl><dt>/join</dt><dd>Join with an invitation</dd><dt>/query nick</dt><dd>Open a private chat</dd><dt>/help</dt><dd>All commands available here</dd></dl>
          <p class="muted">Tab completes text · Shift+Tab leaves the input · Escape dismisses suggestions · ↑↓ command history · Alt+←/→ switches windows</p>
          <details><summary>Instance identity</summary><p class="identity">{snapshot?.instance.id}</p><p class="identity">{snapshot?.instance.safetyNumber}</p></details>
        </div>
      {:else}
        <!-- svelte-ignore a11y_no_noninteractive_tabindex (Keyboard scrollback is intentional.) -->
        <div class="transcript" bind:this={transcript} role="log" aria-label={`${title} messages`} aria-live="polite" tabindex="0" onscroll={() => { atBottom = !!transcript && transcript.scrollHeight - transcript.scrollTop - transcript.clientHeight < 35; rememberPosition(); if (atBottom) void markRead(); }}>
          {#if before}<button class="older" disabled={loadingHistory} onclick={() => void loadHistory(true)}>Load earlier messages</button>{/if}
          {#if !messages.length}<p class="empty">{loadingHistory ? 'Loading…' : '*** Beginning of this conversation'}</p>{/if}
          {#each messages as message, index (message.id)}
            {@const date = new Date(message.timestamp * 1000).toLocaleDateString()}
            {@const action = message.body.startsWith('\u0001ACTION ') && message.body.endsWith('\u0001')}
            {#if !index || new Date(messages[index - 1].timestamp * 1000).toLocaleDateString() !== date}<div class="date">{date}</div>{/if}
            {#if selected && unreadMarkers[selected] === message.id}<div class="unread-divider">New messages</div>{/if}
            <div class="message" class:mine={message.mine}><time title={new Date(message.timestamp * 1000).toLocaleString()}>[{time(message.timestamp)}]</time><span class="nick">{action ? `* ${message.nickname}` : `<${message.nickname}>`}</span><span class="body">{action ? message.body.slice(8, -1) : message.body}{#if message.delivery === 'local_accepted'}<small class="acceptance" title="Accepted by this instance; recipient delivery is not confirmed"> · accepted locally</small>{/if}{#if message.result}<MessageResult result={message.result} />{/if}</span></div>
          {/each}
        </div>
        {#if !atBottom}<button class="jump" onclick={() => { atBottom = true; if (transcript) transcript.scrollTop = transcript.scrollHeight; void markRead(); }}>Jump to latest</button>{/if}
      {/if}
      {#if !locked && outputs[selected ?? '']?.length}
        <div class="results" aria-label="Conversation command results">
          <button onclick={() => { outputs = { ...outputs, [selected ?? '']: [] }; }}>Close results</button>
          {#each outputs[selected ?? ''] as output}<CommandResult {output} choose={chooseChannel} />{/each}
        </div>
      {/if}
      {#if !locked && (Object.keys(pending).length || joinBusy)}<div class="progress" role="status">{Object.values(pending).map(name => `${name}: waiting for instance`).join(' · ')}{joinBusy ? ' Joining channel…' : ''}</div>{/if}
      {#if notice}<div class="notice" role="status"><pre>{notice}</pre><button aria-label="Dismiss notice" onclick={() => notice = ''}>×</button></div>{/if}
      {#each failures as failure (failure.request.operation_id)}
        <div class="retry" role="status"><span>{failureTarget(failure.request.conversation)}: {failure.message} {failure.code === 'rejected' ? 'Command was not accepted.' : 'Outcome not confirmed. Checking uses the original operation.'}</span>{#if failure.code !== 'rejected'}<button disabled={lifecycleBusy || !!pending[failure.request.conversation ?? '']} onclick={() => void checkSaved(failure.request.operation_id)}>Check result</button>{/if}<button onclick={() => void editFailed(failure.request)}>{failure.code === 'rejected' ? 'Edit command' : 'Edit as new'}</button><button aria-label="Dismiss failed operation" onclick={() => dismissFailure(failure.request.operation_id)}>×</button></div>
      {/each}
      {#if !locked}
        {#each savedOperations.filter(h => !failures.some(f => f.request.operation_id === h.operation.id)) as handle (handle.operation.id)}
          <div class="retry" role="status"><span>{recoveryMessages[handle.operation.id] ?? 'Checking a saved operation from this instance…'}</span><button disabled={checkingSaved[handle.operation.id]} onclick={() => void checkSaved(handle.operation.id)}>Check result</button><button onclick={() => forgetSaved(handle.operation.id)}>Dismiss</button></div>
        {/each}
      {/if}
      {#if draftError}<p class="input-error" id="gchat-input-error">{draftError}</p>{/if}
      {#if !locked}
        <form class="composer" onsubmit={event => { event.preventDefault(); void send(); }}>
          {#if completions.length}<div class="completions" aria-label="Command completions">{#each completions as item}<button type="button" onclick={() => { draft = item.text + ' '; completions = []; composer?.focus(); }}><strong>{item.text}</strong><span>{item.description}</span></button>{/each}</div>{/if}
          <span class="prompt">{active?.members.find(m => m.isSelf)?.nickname ?? '>'}</span>
          <textarea bind:this={composer} bind:value={draft} aria-label="Message or command" aria-invalid={!!draftError} aria-describedby={draftError ? 'gchat-input-error' : undefined} rows="1" placeholder={active?.kind === 'archive' ? 'Read-only archive · /help for commands' : selected ? 'Message or /command' : '/join, /create or /help'} onkeydown={keydown} oninput={() => { completions = []; historyPosition = undefined; }}></textarea>
          <button class="send" type="submit" disabled={!draft || !!draftError || busy || offline}>{busy ? '…' : 'Send'}</button>
        </form>
      {/if}
      <footer><span>{active?.kind === 'archive' ? 'Read-only history' : title}</span><span>{busy ? 'Working…' : offline ? 'Reconnecting to selected instance…' : 'Enter sends · Shift+Enter new line'}</span></footer>
    </main>
    {#if active?.members.length}
      <aside class="members" class:open={membersOpen} aria-label="Channel nicks" role={membersOpen ? 'dialog' : undefined} aria-modal={membersOpen ? true : undefined}>
        {#if membersOpen}<button onclick={closeNavigation}>Close nicks</button>{/if}
        <div class="pane-label">NICKS <span>{active.members.length}</span></div>
        {#each active.members as member (member.id)}<button class:self={member.isSelf} disabled={member.isSelf || busy} onclick={() => void send(`/query ${member.id}`)} title={member.isSelf ? 'Your channel identity' : 'Open private chat'}><span class="symbol">{member.isSelf ? '›' : '·'}</span>{member.nickname}</button>{/each}
      </aside>
    {/if}
  </div>
  {#if dialog}
    <dialog class="modal" use:showModal aria-labelledby="gchat-dialog-title" onclose={() => dialog = null}>
      <header><h2 id="gchat-dialog-title">{dialog === 'join' ? 'Join a channel' : 'Create a channel'}</h2><button aria-label="Close dialog" onclick={() => dialog = null}>×</button></header>
      {#if dialog === 'join'}<nav aria-label="Join method"><button aria-pressed={!browse} onclick={() => browse = false}>Paste invitation</button><button aria-pressed={browse} onclick={() => void loadDirectory()}>Browse channels</button></nav>{/if}
      {#if browse && dialog === 'join'}<button onclick={() => void loadDirectory(true)}>Refresh public directory</button>{#if directory}<CommandResult output={directory} choose={chooseChannel} />{/if}{/if}
      <form onsubmit={join}><label for="gchat-destination">{dialog === 'join' ? 'Invitation link or public #channel' : 'Channel name'}</label><input id="gchat-destination" bind:value={destination} disabled={joinBusy} required placeholder={dialog === 'create' ? '#friends' : 'Paste an invitation'} /><label for="gchat-nickname">Your nickname in this channel</label><input id="gchat-nickname" bind:value={nickname} disabled={joinBusy} required autocomplete="nickname" />{#if joinError}<p role="alert">{joinError}</p>{/if}<button class="primary" type="submit" disabled={joinBusy}>{joinBusy ? 'Joining…' : dialog === 'join' ? 'Join' : 'Create'}</button></form>
    </dialog>
  {/if}
</div>

<style>
  .provider-errors { padding:4px 12px; color:var(--muted); }
  .connection-details { margin:0; padding:4px 12px; }
  .search { max-height:50%; overflow:auto; padding:8px 12px; border-bottom:1px solid var(--line); }
  .search p { overflow-wrap:anywhere; white-space:pre-wrap; }
  .progress { padding:5px 12px; color:var(--muted); }
  .unread-divider { color:var(--accent); border-top:1px solid var(--accent); text-align:center; margin:10px 0; }
  .transcript,.composer { font:16px/1.3 GchatFixedsys,'Lucida Console',monospace; }
  .readable .transcript,.readable .composer { font-family:ui-monospace,'SFMono-Regular',Consolas,monospace; line-height:1.5; }
  .date { margin:12px 0; color:var(--muted); text-align:center; border-bottom:1px solid var(--line); }
  .acceptance { font:11px/1.4 ui-sans-serif,system-ui,sans-serif; }
  .jump { align-self:center; min-height:44px; color:var(--accent); }
  .results { max-height:45%; overflow:auto; border-top:1px solid var(--line); }
  @font-face { font-family: GchatFixedsys; src: url('/fonts/fixedsys-excelsior.ttf') format('truetype'); font-display: swap; }
  .gchat { --bg:#1c1e22; --panel:#25282e; --line:#3e444d; --ink:#e4e7eb; --muted:#a8b0bb; --accent:#b7cbe4; color-scheme:dark; height:100dvh; min-height:260px; display:flex; flex-direction:column; overflow:hidden; background:var(--bg); color:var(--ink); font:15px/1.4 Inter,ui-sans-serif,system-ui,sans-serif; padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left); box-sizing:border-box; }
  .gchat :global(*) { box-sizing:border-box; }
  button,input,textarea { font:inherit; color:inherit; }
  button { background:transparent; border:1px solid transparent; padding:5px 10px; cursor:pointer; text-align:left; }
  button:hover:not(:disabled) { background:#343b46; color:#fff; }
  button:focus-visible,input:focus-visible,textarea:focus-visible,summary:focus-visible { outline:2px solid var(--accent); outline-offset:-2px; }
  button:disabled { color:#818889; cursor:default; }
  .titlebar { display:flex; gap:14px; align-items:center; padding:8px 12px; background:#17191a; border-bottom:1px solid #353a3c; }
  .titlebar .brand { display:inline-flex; align-items:center; gap:8px; flex:none; }
  .titlebar .brand :global(.ghost-mark) { --ghost-mark-size:18px; transform:translateY(0.5px); }
  .titlebar strong { color:var(--accent); letter-spacing:1px; font-size:20px; line-height:1; }
  .instance { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  small,.muted { color:var(--muted); }
  .connection { color:var(--accent); font-size:14px; }
  .unavailable .connection { color:#efbe88; }
  .toolbar { display:flex; align-items:center; padding:3px 6px; background:var(--panel); border-bottom:1px solid var(--line); gap:2px; }
  .spacer { flex:1; }
  .workspace { display:flex; flex:1; min-height:0; position:relative; }
  aside { background:#25282a; flex-shrink:0; overflow:auto; }
  .channels { width:210px; border-right:1px solid var(--line); display:flex; flex-direction:column; }
  .pane-label { padding:10px 12px 8px; font-size:12px; color:var(--muted); letter-spacing:1px; display:flex; justify-content:space-between; }
  aside button { width:100%; padding:7px 10px; display:flex; flex-wrap:wrap; align-items:center; gap:5px; }
  aside button small { width:100%; font-size:12px; padding-left:23px; overflow:hidden; text-overflow:ellipsis; }
  .symbol { width:16px; color:var(--accent); flex-shrink:0; }
  .room-name { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  aside .chosen { background:#343b46; border-left:2px solid var(--accent); }
  .unread .room-name { color:var(--accent); }
  .badge { font-size:12px; background:#3b4b62; border-radius:3px; padding:1px 5px; }
  .conversation { flex:1; min-width:0; display:flex; flex-direction:column; }
  .topic { border-bottom:1px solid var(--line); padding:9px 12px; display:flex; align-items:baseline; gap:16px; background:#25282a; }
  .topic strong { color:var(--accent); white-space:nowrap; }
  .topic span { color:var(--muted); font-size:14px; overflow-wrap:anywhere; }
  .welcome { flex:1; min-height:0; overflow:auto; padding:clamp(18px,4vw,52px); }
  h1 { font-size:24px; font-weight:normal; color:var(--accent); margin:22px 0 14px; }
  p { margin:12px 0; }
  .welcome form { max-width:400px; margin-top:25px; }
  label { display:block; margin:15px 0 6px; }
  input { display:block; width:100%; border:1px solid #626969; background:#16181c; padding:10px; min-height:44px; }
  .primary { margin-top:16px; border:1px solid #566476; background:#343b46; padding:10px 14px; }
  dl { display:grid; grid-template-columns:max-content 1fr; gap:8px 18px; margin:28px 0; }
  dt { color:var(--accent); } dd { margin:0; color:var(--muted); }
  details { margin-top:24px; color:var(--muted); } summary { cursor:pointer; }
  .identity { overflow-wrap:anywhere; font-size:12px; }
  .transcript { flex:1; overflow:auto; min-height:0; padding:12px; scrollbar-color:#5a6561 #242728; }
  .message { display:grid; grid-template-columns:7ch auto 1fr; column-gap:8px; margin:2px 0; align-items:baseline; }
  time { color:#858f8e; font-size:14px; }
  .nick { color:#a9c7e8; max-width:24ch; overflow-wrap:anywhere; }
  .mine .nick { color:var(--accent); }
  .body { white-space:pre-wrap; overflow-wrap:anywhere; min-width:0; }
  .empty { color:var(--muted); }
  .older { display:block; margin:0 auto 12px; border-color:var(--line); color:var(--accent); }
  .notice { display:flex; background:#2b3037; border-top:1px solid #566476; max-height:38%; overflow:auto; padding:8px 12px; gap:10px; }
  .notice pre { font:inherit; white-space:pre-wrap; overflow-wrap:anywhere; flex:1; margin:0; min-width:0; }
  .notice button { align-self:flex-start; }
  .retry { padding:7px 12px; background:#4b3a27; display:flex; flex-wrap:wrap; align-items:center; gap:8px; }
  .retry button { border-color:#806640; }
  .composer { position:relative; display:flex; gap:8px; align-items:center; border-top:1px solid var(--line); background:#191d1e; padding:7px 10px; }
  .prompt { color:var(--accent); max-width:18ch; overflow:hidden; text-overflow:ellipsis; }
  textarea { resize:none; flex:1; width:0; min-height:36px; max-height:160px; padding:8px 3px; border:0; background:transparent; field-sizing:content; }
  .send { color:var(--accent); border-color:#566476; }
  .completions { position:absolute; bottom:100%; left:0; right:0; z-index:2; background:#303739; border:1px solid #566476; max-height:240px; overflow:auto; }
  .completions button { display:flex; gap:20px; width:100%; padding:9px 12px; }
  .completions span { color:var(--muted); }
  footer { display:flex; justify-content:space-between; gap:10px; font-size:12px; padding:4px 10px; color:var(--muted); background:var(--panel); }
  .members { width:160px; border-left:1px solid var(--line); }
  .members button { overflow-wrap:anywhere; }.members .self { color:var(--accent); }
  .mobile,.scrim { display:none; }
  .more { position:relative; margin:0; color:var(--ink); }
  .more summary { padding:12px 10px; list-style:none; }
  .more-items { position:absolute; right:0; top:100%; width:190px; z-index:8; padding:4px; border:1px solid var(--line); background:var(--panel); box-shadow:0 6px 20px #0008; }
  .more-items button { display:block; width:100%; }

  .modal::backdrop { background:#0009; }
  .modal { color:var(--ink); margin:auto; width:min(460px,100%); max-height:90dvh; overflow:auto; background:var(--panel); border:1px solid #566476; padding:18px; box-shadow:0 14px 60px #0008; }
  .modal header { display:flex; align-items:center; gap:10px; }.modal h2 { flex:1; font-size:20px; font-weight:normal; margin:0; color:var(--accent); }
  @media(max-width:1000px) and (min-width:761px) { .channels{width:180px}.members{width:135px} }
  @media(max-width:760px) {
    .mobile { display:block; }.desktop { display:none; }.toolbar { gap:0; }.toolbar button { padding:8px; min-height:44px; font-size:14px; white-space:nowrap; }
    .titlebar { padding:8px 10px; }
    .channels,.members { display:none; position:absolute; top:0; bottom:0; z-index:4; width:min(280px,85vw); box-shadow:4px 0 20px #0006; }
    .channels.open { display:flex; }.members.open{display:block;right:0;}.channels button,.members button{min-height:44px;}
    .scrim { display:block; position:absolute; inset:0; z-index:3; background:#0008; width:100%;border:0; }
    .topic{padding:8px 10px;flex-wrap:wrap;gap:3px 10px;}.topic span{font-size:12px;}
    .transcript{padding:10px 8px;}.message{grid-template-columns:6ch 1fr;column-gap:4px;margin:6px 0;}.body{grid-column:2;}.nick{max-width:none;}time{font-size:12px;}
    .composer{padding:4px 8px;}.composer textarea,.send{min-height:44px;}.prompt{max-width:10ch;font-size:14px;}
    footer span:last-child{display:none;}footer{padding:4px 8px;}.welcome{padding:20px;}h1{font-size:22px;}
    .completions button{flex-wrap:wrap;gap:4px;}.completions span{width:100%;font-size:12px;}.notice{max-height:32%;}
  }
</style>
