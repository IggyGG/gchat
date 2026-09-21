<script lang="ts">
  import { onMount, tick, type Snippet } from 'svelte';
  import type { OperationHandle } from '@gcoms/rpc';
  import type { CommandOutput, CommandSpec, Completion, DirectoryEntry, JoinedNetwork, Message, NetworkStatus, Request, Response, Snapshot } from './api';
  import { NetworkWorkspace } from './network-workspace';
  import CommandResult from './CommandResult.svelte';
  import GhostMark from './GhostMark.svelte';
  import FilePanel from './FilePanel.svelte';
  import type { FileAccess } from './files';
  import NetworkSetup from './NetworkSetup.svelte';
  import { FileController, emptyFiles, type FileViewState } from './file-controller';
  import { hasNetworkSetup, networkLabel, localCommand, mergeViewCommands, viewCommands, readFont, writeFont, type ChatFont } from './workspace-state';
  import MessageResult from './MessageResult.svelte';
  import { chatError, type ChatError, type Transport } from './transport';
  import { MAX_INPUT_BYTES } from './api';
  import { ConversationViews, inputError, shouldComplete, readNavigation, writeNavigation } from './view-state';
  import { fitVisualViewport, isTouchActivation } from './viewport';

  let { transport: attachmentTransport, tools, fileAccess }: { transport: Transport; tools?: Snippet; fileAccess?: FileAccess } = $props();
  let networks = $state<JoinedNetwork[]>([]);
  let selectedNetwork = $state<string>();
  const transport = new NetworkWorkspace(() => attachmentTransport, value => networks = value);
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
  let panel = $state<'users' | 'files' | null>(null);
  let narrow = $state(false);
  const navigationModal = $derived(channelsOpen || (!!panel && narrow));
  let utility = $state<'network' | 'help' | 'font' | 'info' | null>(null);
  let channelTopic = $state('');
  let channelNickname = $state('');
  let detailsConversation = $state<string | null>(null);
  let leavingChannel = $state(false);
  let nextOwner = $state('');
  let replacingInvitation = $state(false);
  let networkStatus = $state<NetworkStatus>();
  let networkAccepted = $state(false), networkError = $state('');
  let networkPolling = false, networkGeneration = 0;
  let helpCommands = $state<CommandSpec[]>([]), helpError = $state('');
  let fileState = $state<FileViewState>(emptyFiles());
  let fileController = $state<FileController>();
  const fileControllers = new Map<string, FileController>();
  let fileStates = $state<Record<string, FileViewState>>({});
  let fileInput = $state<HTMLInputElement>();
  let fileTarget: { conversation: string; resumeId?: string; controller: FileController } | undefined;
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
  let running = true;
  let generation = 0;
  let snapshotGeneration = 0;
  let atBottom = $state(true);
  let loadingHistory = $state(false);
  let historyStale = false;
  let restoredSelection = false;
  let font = $state<ChatFont>('fixedsys');
  let navigationOpener: HTMLElement | null = null;
  const active = $derived(snapshot?.conversations.find(c => c.id === selected));
  const details = $derived(snapshot?.conversations.find(c => c.id === detailsConversation));
  const locked = $derived(snapshot?.instance.locked ?? true);
  const creating = $derived(snapshot?.instance.protocolLocked ? !snapshot.instance.profileExists : !snapshot?.instance.archiveExists);
  const title = $derived(active?.name ?? 'Status');
  const workspaceReady = $derived(!locked && networkAccepted);
  const fileIdentity = $derived(workspaceReady && snapshot?.instance.capabilities.includes('files.v1') ? `${snapshot.instance.id}/${snapshot.instance.bootId}` : null);
  const fileCount = $derived(fileState.snapshot?.files.filter(f => f.conversation === selected && f.state !== 'cancelled').length ?? 0);
  const connectionLabel = $derived(networkLabel(networkStatus, offline, locked));
  $effect(() => {
    if (!fileIdentity) return;
    return () => { for (const controller of fileControllers.values()) controller.stop(); fileControllers.clear(); fileStates = {}; fileController = undefined; };
  });
  $effect(() => {
    if (!fileIdentity) return;
    const scope = selectedNetwork ?? networks.find(n => n.primary)?.id ?? '';
    const available = networks.length ? networks.map(n => n.id) : [''];
    for (const network of available) {
      if (fileControllers.has(network)) continue;
      const controller = new FileController(transport.forNetwork(network || undefined), fileIdentity.split('/')[0], transport.fileAccess(network || undefined, fileAccess), value => fileStates = { ...fileStates, [network]: value });
      fileControllers.set(network, controller); controller.start();
    }
    fileController = fileControllers.get(scope);
    fileState = fileStates[scope] ?? emptyFiles();
  });
  $effect(() => { if (workspaceReady && !restoredSelection) void refreshInBackground(); });
  async function refreshNetwork() {
    if (!running || locked || networkPolling) return;
    networkPolling = true;
    const revision = networkGeneration;
    try {
      const response = await transport.request({ kind: 'network_status' });
      if (!running || locked || revision !== networkGeneration || response.kind !== 'network_status') return;
      networkStatus = response.status; networkError = '';
      if (hasNetworkSetup(response.status)) networkAccepted = true;
    } catch (error) { if (running && !locked && revision === networkGeneration) networkError = chatError(error).message; }
    finally { networkPolling = false; }
  }
  function imported(status: NetworkStatus) {
    networkGeneration++; networkStatus = status;
    if (hasNetworkSetup(status)) networkAccepted = true;
    replacingInvitation = false; utility = null; void refreshInBackground();
  }
  async function invitationJoined(response: Response) {
    selectedNetwork = transport.active;
    networkAccepted = true; replacingInvitation = false; utility = null; dialog = null;
    await refreshInBackground();
    await apply(response, selected);
    void refreshNetwork();
  }
  function openUtility(value: typeof utility) {
    closeNavigation(); utility = value; replacingInvitation = false;
    if (value === 'info') {
      detailsConversation = selected; channelTopic = active?.topic ?? ''; channelNickname = active?.members.find(m => m.isSelf)?.nickname ?? '';
      leavingChannel = false; nextOwner = active?.members.find(m => !m.isSelf)?.id ?? '';
    }
  }
  function channelCommand(text: string) {
    const conversation = detailsConversation;
    if (!conversation || !workspaceReady || busy) return;
    utility = null;
    void operation({ kind: 'submit', operation_id: crypto.randomUUID(), conversation, text });
  }
  async function showHelp() {
    openUtility('help'); helpError = '';
    helpCommands = viewCommands(!!selected);
    try {
      const response = await transport.request({ kind: 'catalogue', conversation: workspaceReady ? selected : null });
      if (utility === 'help' && response.kind === 'catalogue') helpCommands = mergeViewCommands(response.commands, !!selected && workspaceReady);
    } catch (error) { if (utility === 'help') helpError = chatError(error).message; }
  }
  function chooseFont(value: ChatFont) { font = value; writeFont(value); }
  async function find(text = '') {
    if (!selected || !workspaceReady) { notice = 'Choose a conversation before using /find.'; return; }
    searchOpen = true; searchText = text; searchResults = []; searchBefore = null; searchError = '';
    await tick(); document.getElementById('gchat-search')?.focus();
    if (text) await search();
  }
  function closeSearch() { searchOpen = false; searchGeneration++; searchBusy = false; composer?.focus(); }
  function chooseFile(resumeId?: string) {
    if (!selected || !workspaceReady || !fileAccess || active?.kind === 'archive' || fileState.busy) return;
    if (!fileController) return;
    fileTarget = { conversation: selected, resumeId, controller: fileController }; fileInput?.click();
  }
  function pickedFile() {
    const file = fileInput?.files?.[0], target = fileTarget;
    fileTarget = undefined; if (fileInput) fileInput.value = '';
    if (!file || !target || !workspaceReady) return;
    panel = 'files'; channelsOpen = false;
    void target.controller.upload(file, target.conversation, target.resumeId);
  }
  const draftError = $derived(inputError(draft, draft.startsWith('/') ? MAX_INPUT_BYTES : active?.inputLimitBytes ?? MAX_INPUT_BYTES));
  function failureTarget(id: string | null) {
    const conversation = snapshot?.conversations.find(c => c.id === id);
    return conversation ? `${conversation.name}${conversation.kind === 'query' ? ` · ${conversation.topic}` : ''}` : id ? 'Original conversation' : 'Status';
  }
  function dismissFailure(id: string) { failures = failures.filter(f => f.request.operation_id !== id); }


  onMount(() => {
    running = true; font = readFont(); narrow = window.innerWidth < 1000;
    const networkTimer = setInterval(() => void refreshNetwork(), 2000);
    void watch();
    const visible = () => { if (!document.hidden && (!connectionError || connectionError.retryable)) void refreshInBackground(); };
    document.addEventListener('visibilitychange', visible);
    const disconnected = () => connectionFailed(new Error('Network unavailable. Drafts and loaded history remain available.'));
    window.addEventListener('online', visible); window.addEventListener('offline', disconnected);
    return () => { running = false; clearInterval(networkTimer); networkGeneration++; generation++; password = ''; views.clear(); document.removeEventListener('visibilitychange', visible); window.removeEventListener('online', visible); window.removeEventListener('offline', disconnected); };
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
      generation++; searchGeneration++; views.clear(); outputs = {}; unreadMarkers = {}; messages = []; before = null; password = ''; draft = ''; savedDraft = ''; notice = ''; failures = []; completions = []; historyPosition = undefined; pending = {}; directory = undefined; destination = ''; nickname = ''; joinRequest = undefined; joinError = ''; dialog = null; searchOpen = false; searchText = ''; searchResults = []; searchBefore = null; hidden = []; restoredSelection = false; networkAccepted = false; networkStatus = undefined; networkGeneration++; networkError = ''; panel = null; channelsOpen = false; utility = null; fileTarget = undefined;
    }
    snapshot = next;
    selectedNetwork ??= transport.active;
    if (!next.instance.locked && !networkStatus) void refreshNetwork();
    if (workspaceReady && transport.pendingOperations) {
      try {
        savedOperations = transport.pendingOperations();
        for (const handle of savedOperations) {
          const id = handle.operation.id;
          if (!checkedSaved.has(id)) { checkedSaved.add(id); void checkSaved(id); }
        }
      } catch (error) { notice = chatError(error).message; }
    } else savedOperations = [];
    if (workspaceReady && !restoredSelection) {
      restoredSelection = true;
      const remembered = readNavigation(next.instance.id);
      await select(remembered && (remembered.selected === null || next.conversations.some(c => c.id === remembered.selected)) ? remembered.selected : next.conversations[0]?.id ?? null);
    }
    if (selected && !next.conversations.some(c => c.id === selected)) await select(null);
    views.retain(next.conversations.map(c => c.id));
    for (const id of Object.keys(outputs)) if (id && !next.conversations.some(c => c.id === id)) delete outputs[id];
    if ((changed || historyStale || offline) && selected && workspaceReady) await loadHistory(false, true);
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
  async function select(id: string | null, activation?: MouseEvent) {
    const nextNetwork = id ? transport.networkFor(id) : selectedNetwork;
    if (nextNetwork !== selectedNetwork) { networkGeneration++; networkStatus = networks.find(n => n.id === nextNetwork)?.status; }
    selectedNetwork = nextNetwork; transport.select(selectedNetwork);
    const fromDrawer = channelsOpen;
    const rememberedPosition = id && snapshot ? readNavigation(snapshot.instance.id)?.positions[id] : undefined;
    rememberPosition();
    if (!id) panel = null;
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
    channelsOpen = false; completions = [];
    if (fromDrawer) {
      await tick();
      if (isTouchActivation(activation, window.matchMedia('(pointer: coarse)').matches)) document.querySelector<HTMLElement>('.active-title')?.focus();
      else composer?.focus();
    }
    if (id && workspaceReady) await loadHistory(false);
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
    if (!snapshot || !workspaceReady || !restoredSelection) return;
    const value = readNavigation(snapshot.instance.id) ?? { selected, positions: {} };
    value.selected = selected;
    if (selected && transcript) value.positions[selected] = { top: transcript.scrollTop, atBottom, oldest: messages[0]?.id ?? null };
    writeNavigation(snapshot.instance.id, value);
  }
  async function loadHistory(older: boolean, background = false) {
    const conversation = selected;
    if (!conversation || !workspaceReady || (older && !before)) return;
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
    if (!selected || !atBottom || document.hidden || !document.hasFocus() || !workspaceReady) return;
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
    if (!text || !workspaceReady) return;
    const local = localCommand(text);
    if (local) {
      if (text === draft) draft = '';
      completions = []; historyPosition = undefined;
      if (local.name === 'help') await showHelp();
      else if (local.name === 'find') await find(local.args);
      else if (!local.args) openUtility('font');
      else if (local.args === 'fixedsys' || local.args === 'readable') chooseFont(local.args);
      else notice = 'Use /font, /font fixedsys or /font readable.';
      return;
    }
    if (busy) return;
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
      if (draft === text && selected === conversation && response.kind === 'completed') {
        const local = viewCommands(!!selected).filter(c => c.available && c.name.startsWith(text)).map(c => ({ text: c.name, description: c.description }));
        completions = [...response.items.filter(c => !local.some(l => l.text === c.text)), ...local];
      }
    } catch (error) { notice = String(error); }
  }
  function keydown(event: KeyboardEvent) {
    if (event.isComposing) return;
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void send(); }
    else if (shouldComplete(event, draft, completions.length > 0)) { event.preventDefault(); void complete(); }
    else if (event.key === 'Escape') { completions = []; channelsOpen = false; panel = null; dialog = null; }
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
    if (event.isComposing || dialog || utility) return;
    if (navigationModal) {
      if (event.key === 'Escape') { event.preventDefault(); closeNavigation(); return; }
      if (event.key === 'Tab') {
        const nodes = [...document.querySelectorAll<HTMLElement>('.gchat aside.open button:not(:disabled), .gchat aside.open input:not(:disabled), .gchat aside.open summary')];
        const index = nodes.indexOf(document.activeElement as HTMLElement);
        if (nodes.length && (index < 0 || (!event.shiftKey && index === nodes.length - 1) || (event.shiftKey && index === 0))) {
          event.preventDefault(); nodes[event.shiftKey ? nodes.length - 1 : 0]?.focus();
        }
        return;
      }
    }
    if (event.key === 'Escape' && searchOpen) { event.preventDefault(); closeSearch(); return; }
    if (event.key === 'Escape' && panel) { closeNavigation(); return; }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'f' && selected && workspaceReady) { event.preventDefault(); void find(searchText); return; }
    if (workspaceReady && event.altKey && ['ArrowLeft', 'ArrowRight'].includes(event.key)) {
      event.preventDefault();
      const ids = [null, ...snapshot?.conversations.filter(c => !hidden.includes(c.id)).map(c => c.id) ?? []];
      const index = ids.indexOf(selected);
      void select(ids[(index + ids.length + (event.key === 'ArrowRight' ? 1 : -1)) % ids.length]);
    }
  }
  function closeNavigation() { channelsOpen = false; panel = null; void tick().then(() => navigationOpener?.focus()); }
  async function openNavigation(mode: 'channels' | 'users' | 'files') {
    if ((mode === 'channels' && channelsOpen) || (mode !== 'channels' && panel === mode)) { closeNavigation(); return; }
    navigationOpener = document.activeElement as HTMLElement | null;
    channelsOpen = mode === 'channels'; panel = mode === 'channels' ? null : mode;
    await tick(); document.querySelector<HTMLButtonElement>(`.gchat .${mode === 'channels' ? 'channels' : 'inspector'}.open button:not(:disabled)`)?.focus();
  }
  function showModal(node: HTMLDialogElement) {
    const opener = document.activeElement as HTMLElement | null;
    node.showModal(); (node.querySelector<HTMLElement>('input, textarea') ?? node.querySelector<HTMLElement>('button:not(:disabled)'))?.focus();
    return { destroy() { opener?.focus(); } };
  }
  function openDialog(mode: 'join' | 'create') {
    if (!workspaceReady) return;
    closeNavigation();
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

<svelte:window onkeydown={cycle} onfocus={() => { void markRead(); void refreshNetwork(); void fileController?.refresh(); }} onresize={() => { narrow = window.innerWidth < 1000; if (window.innerWidth > 760) channelsOpen = false; }} />
<div class="gchat" class:unavailable={offline} class:readable={font === 'readable'} use:fitVisualViewport>
  <header class="titlebar" inert={navigationModal}>
    {#if workspaceReady}<button class="channel-toggle" aria-label="Channels" aria-expanded={channelsOpen} onclick={() => void openNavigation('channels')}>☰</button>{/if}
    <span class="brand"><strong>GChat.</strong><GhostMark /></span>
    {#if workspaceReady}<button class="active-title" title={active?.topic || title} onclick={() => openUtility('info')}>{title}</button>{:else}<span class="active-title">{locked ? 'Welcome' : 'Connect to GChat'}</span>{/if}
    <nav class="header-actions" aria-label="Chat actions">
      <button class="network-button" disabled={locked} title={`${networks.find(n => n.id === selectedNetwork)?.name ?? 'Network'} · ${connectionLabel}`} aria-label={`Network: ${connectionLabel}`} onclick={() => openUtility('network')}><span class="connection-dot" class:connected={!offline && networkStatus?.state === 'connected'} aria-hidden="true">●</span><span class="sr-only" role="status">{connectionLabel}</span></button>
      <button class="help-button" title="Help and commands" onclick={() => void showHelp()}>Help</button>
      {#if workspaceReady && active}
        <button class="count" aria-label={`Users: ${active.members.length}`} aria-expanded={panel === 'users'} title="Users" onclick={() => void openNavigation('users')}><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="9" cy="7" r="3" /><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6m3 11v-3a6 6 0 0 0-2-4" /></svg> {active.members.length}</button>
        {#if fileCount}<button class="count" aria-label={`Files: ${fileCount}`} aria-expanded={panel === 'files'} title="Files" onclick={() => void openNavigation('files')}><span aria-hidden="true">▤</span> {fileCount}</button>{/if}
      {/if}
      {#if tools}{@render tools()}{/if}
    </nav>
  </header>
  <input class="file-picker" type="file" aria-label="Choose a file to share" bind:this={fileInput} onchange={pickedFile} />
  <div class="workspace">
    {#if navigationModal}<button class="scrim" tabindex="-1" aria-label="Close navigation" onclick={closeNavigation}></button>{/if}
    {#if workspaceReady}<aside class="channels" class:open={channelsOpen} aria-label="Channels" role={channelsOpen ? 'dialog' : undefined} aria-modal={channelsOpen ? true : undefined}>
      {#if channelsOpen}<button onclick={closeNavigation}>Close channels</button>{/if}
      <div class="channel-entries">
      <button class:chosen={!selected} aria-current={!selected ? 'page' : undefined} onclick={event => void select(null, event)}><span class="symbol">◈</span> Status</button>
      {#each networks.length > 1 ? networks : [undefined] as network (network?.id ?? 'single')}
      {#if network}<button class="network-group" aria-pressed={selectedNetwork === network.id} onclick={event => { selectedNetwork = network.id; transport.select(network.id); networkGeneration++; networkStatus = network.status; void select(null, event); }}><span class="connection-dot" class:connected={network.status.state === 'connected'} aria-hidden="true">●</span>{network.name}</button>{/if}
      {#each snapshot?.conversations.filter(c => !hidden.includes(c.id) && (!network || transport.networkFor(c.id) === network.id)) ?? [] as conversation (conversation.id)}
        <button class:chosen={selected === conversation.id} aria-current={selected === conversation.id ? 'page' : undefined} class:unread={conversation.unread > 0} onclick={event => void select(conversation.id, event)} title={conversation.topic || conversation.name}>
          <span class="symbol">{conversation.kind === 'query' ? '↳' : conversation.kind === 'archive' ? '·' : '#'}</span>
          <span class="room-name">{conversation.name.replace(/^#/, '')}</span>
          {#if conversation.unread}<span class="badge">{conversation.unread}</span>{/if}
          {#if conversation.kind === 'query'}<small>{conversation.topic}</small>{/if}
          {#if conversation.kind === 'archive'}<small>read only</small>{/if}
        </button>
      {/each}
      {/each}
      </div>
      <div class="channel-actions"><button disabled={busy} onclick={() => openDialog('join')}>Join…</button>{#if snapshot?.instance.capabilities.includes('ChannelAdmin')}<button disabled={busy} onclick={() => openDialog('create')}>Create…</button>{/if}</div>
    </aside>{/if}
    <main class="conversation" inert={navigationModal}>
      {#if !locked && snapshot?.providerErrors?.length}<div class="provider-errors" role="status">{#each snapshot.providerErrors as error}<p>{error.retryable ? 'Conversation provider reconnecting' : 'Conversation provider blocked'}: {error.message}</p>{/each}<button onclick={() => void send('/refresh')}>Reconnect provider</button></div>{/if}
      {#if connectionError && !connectionError.retryable}<div class="notice" role="status"><span>{connectionError.message}</span><button onclick={() => { if (['instance', 'version', 'authentication'].includes(connectionError?.code ?? '')) location.reload(); else void refreshInBackground(); }}>{connectionError.action}</button></div>{/if}
      {#if searchOpen && selected && !locked}
        <section class="search" aria-label="Find in conversation">
          <form onsubmit={event => { event.preventDefault(); void search(); }}><label for="gchat-search">Find in {title}</label><input id="gchat-search" bind:value={searchText} required /><button disabled={searchBusy}>Find</button><button type="button" onclick={closeSearch}>Close search</button></form>
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
      {:else if !networkAccepted}
        <div class="welcome network-gate">
          <h1>Connect to GChat</h1>
          <p>Use an invitation to connect and start talking. A channel invitation can include everything you need.</p>
          {#if networkStatus?.state === 'invitation_required'}<NetworkSetup {transport} status={networkStatus} {imported} combined={snapshot?.instance.capabilities.includes('networks.v1') ?? false} joined={invitationJoined} />
          {:else}<p role="status">{networkError || networkStatus?.message || 'Checking network setup…'}</p><button class="primary" onclick={() => void refreshNetwork()}>Retry</button>{/if}
        </div>
      {:else if !selected}
        <div class="welcome status">
          {#if !snapshot?.conversations.length}
          <h1>Your channels. Your conversations.</h1>
          <p>Join with an invitation, or create a channel and invite someone.</p>
          <p>Select a user to open a private chat in that channel.</p>
          {:else}<h1>Status</h1><p>{offline ? 'Reconnecting to the selected instance. You can keep drafting.' : 'Attached to this instance. Closing this view keeps receiving messages.'}</p>{/if}
          <dl><dt>/join</dt><dd>Join with an invitation</dd><dt>/query nick</dt><dd>Open a private chat</dd><dt>/help</dt><dd>All commands available here</dd></dl>
          <p class="muted">Tab completes text · Shift+Tab leaves the input · Escape dismisses suggestions · ↑↓ command history · Alt+←/→ switches conversations</p>
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
      {#if workspaceReady && outputs[selected ?? '']?.length}
        <div class="results" aria-label="Conversation command results">
          <button onclick={() => { outputs = { ...outputs, [selected ?? '']: [] }; }}>Close results</button>
          {#each outputs[selected ?? ''] as output}<CommandResult {output} choose={chooseChannel} />{/each}
        </div>
      {/if}
      {#if workspaceReady && (Object.keys(pending).length || joinBusy)}<div class="progress" role="status">{Object.values(pending).map(name => `${name}: waiting for instance`).join(' · ')}{joinBusy ? ' Joining channel…' : ''}</div>{/if}
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
      {#if workspaceReady}
        <form class="composer" onsubmit={event => { event.preventDefault(); void send(); }}>
          {#if completions.length}<div class="completions" aria-label="Command completions">{#each completions as item}<button type="button" onclick={() => { draft = item.text + ' '; completions = []; composer?.focus(); }}><strong>{item.text}</strong><span>{item.description}</span></button>{/each}</div>{/if}
          {#if selected && fileAccess && fileController && active?.kind !== 'archive'}<button class="attach" type="button" aria-label="Share a file" title="Share a file" disabled={fileState.busy} onclick={() => chooseFile()}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m8 12 6-6a3 3 0 0 1 4 4l-8 8a5 5 0 0 1-7-7l9-9a7 7 0 0 1 10 10l-9 9" /></svg></button>{/if}
          <textarea bind:this={composer} bind:value={draft} aria-label="Message or command" aria-invalid={!!draftError} aria-describedby={draftError ? 'gchat-input-error' : undefined} rows="1" placeholder={active?.kind === 'archive' ? 'Read-only archive · /help for commands' : selected ? 'Message or /command' : '/join, /create or /help'} onkeydown={keydown} oninput={() => { completions = []; historyPosition = undefined; }}></textarea>
          <button class="send" type="submit" disabled={!draft || !!draftError || (busy && !localCommand(draft)) || (offline && !localCommand(draft))}>{busy ? '…' : 'Send'}</button>
        </form>
      {/if}
    </main>
    {#if workspaceReady && active && panel}
      <aside class="inspector open" aria-label="Conversation details" role={narrow ? 'dialog' : undefined} aria-modal={narrow ? true : undefined}>
        <div class="inspector-heading"><div role="tablist" tabindex="-1" aria-label="Conversation details" onkeydown={event => {
          if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key) || !fileController) return;
          event.preventDefault(); panel = event.key === 'Home' ? 'users' : event.key === 'End' ? 'files' : panel === 'users' ? 'files' : 'users';
          void tick().then(() => document.getElementById(`${panel}-tab`)?.focus());
        }}><button role="tab" id="users-tab" tabindex={panel === 'users' ? 0 : -1} aria-selected={panel === 'users'} aria-controls="users-panel" onclick={() => panel = 'users'}>Users <small>{active.members.length}</small></button>{#if fileController}<button role="tab" id="files-tab" tabindex={panel === 'files' ? 0 : -1} aria-selected={panel === 'files'} aria-controls="files-panel" onclick={() => panel = 'files'}>Files <small>{fileCount}</small></button>{/if}</div><button aria-label="Close details" onclick={closeNavigation}>×</button></div>
        {#if panel === 'users'}<div id="users-panel" role="tabpanel" tabindex="0" aria-labelledby="users-tab" class="users-list">{#each active.members as member (member.id)}<button class:self={member.isSelf} disabled={member.isSelf || busy} onclick={() => void send(`/query ${member.id}`)} title={member.isSelf ? 'Your channel identity' : 'Open private chat'}>{member.nickname}{#if member.isSelf}<small>you</small>{/if}</button>{/each}{#if !active.members.length}<p>No users to display.</p>{/if}</div>
        {:else if fileController && selected}<div id="files-panel" role="tabpanel" tabindex="0" aria-labelledby="files-tab"><FilePanel view={fileState} controller={fileController} conversation={selected} canShare={active.kind !== 'archive'} canSave={!!fileAccess} choose={chooseFile} /></div>{/if}
      </aside>
    {/if}
  </div>
  {#if utility}
    <dialog class="modal utility-modal" use:showModal aria-labelledby="utility-title" onclose={() => { utility = null; replacingInvitation = false; }}>
      <header><h2 id="utility-title">{utility === 'network' ? 'Network' : utility === 'help' ? 'Help' : utility === 'font' ? 'Chat font' : title}</h2><button aria-label="Close dialog" onclick={() => utility = null}>×</button></header>
      {#if utility === 'network'}
        {#if networks.length > 1}<label for="network-detail-selection">Network</label><select id="network-detail-selection" bind:value={selectedNetwork} onchange={() => { transport.select(selectedNetwork); networkGeneration++; networkStatus = networks.find(n => n.id === selectedNetwork)?.status; }}>{#each networks as network}<option value={network.id}>{network.name}</option>{/each}</select>{/if}
        <p role="status">{networkStatus?.message || networkError || connectionLabel}</p>
        {#if networkError}<p role="alert">{networkError}</p>{/if}
        {#if !networkAccepted || replacingInvitation || networkStatus?.state === 'invitation_expired'}<NetworkSetup {transport} status={networkStatus} {imported} combined={snapshot?.instance.capabilities.includes('networks.v1') ?? false} joined={invitationJoined} />{:else if networkStatus?.state !== 'local_only'}<button class="primary" onclick={() => replacingInvitation = true}>Replace network invitation…</button>{/if}
        {#if connectionError}<details><summary>Connection details</summary><p>{connectionError.message}</p></details>{/if}
      {:else if utility === 'font'}
        <p>Choose the font for messages and the composer. Saved on this device.</p>
        <div class="font-options"><button aria-pressed={font === 'fixedsys'} onclick={() => chooseFont('fixedsys')}>Fixedsys <span class="font-fixed">The quick brown fox</span></button><button aria-pressed={font === 'readable'} onclick={() => chooseFont('readable')}>Readable <span class="font-readable">The quick brown fox</span></button></div>
      {:else if utility === 'help'}
        {#if helpError}<p role="alert">{helpError}</p>{/if}<CommandResult output={{ kind: 'help', commands: helpCommands }} choose={chooseChannel} />
        <section class="shortcuts"><h3>Keyboard</h3><p>Enter sends · Shift+Enter adds a line<br />Tab completes · Shift+Tab moves focus<br />↑↓ recalls commands · Alt+←/→ changes conversation<br />Ctrl/Cmd+F finds messages · Escape closes panels</p><p>/lock hides the archive while receiving continues. /disconnect stops this instance in every view.</p></section>
      {:else}
        {#if details?.kind === 'channel' && details.active}
          {#if details.owner}
            <form onsubmit={(event) => { event.preventDefault(); channelCommand(channelTopic.trim() ? `/topic ${channelTopic.trim()}` : '/topic --clear'); }}>
              <label for="channel-topic">Topic</label><input id="channel-topic" bind:value={channelTopic} maxlength="512" placeholder="What is this channel for?" />
              <button type="submit" disabled={busy || channelTopic === details.topic}>Save topic</button>
            </form>
            <button onclick={() => channelCommand('/invite')} disabled={busy}>Invite someone…</button>
            <p class="muted">One invitation includes this network and channel.</p>
          {:else}<p>{details.topic || 'No topic set.'}</p>{/if}
          <form onsubmit={(event) => { event.preventDefault(); channelCommand(`/nick ${channelNickname.trim()}`); }}>
            <label for="channel-nickname">Your nickname here</label><input id="channel-nickname" bind:value={channelNickname} maxlength="64" autocomplete="nickname" required />
            <button type="submit" disabled={busy || !channelNickname.trim() || channelNickname === details.members.find(m => m.isSelf)?.nickname}>Save nickname</button>
          </form>
        {:else}<p>{details?.topic || 'No topic set.'}</p>{#if details?.kind === 'archive'}<p>Read-only history</p>{/if}{/if}
        <p class="muted">{details?.members.length ?? 0} users</p>
        {#if details?.kind === 'channel' && details.active}
          <section class="leave-actions">
            {#if !leavingChannel}<button onclick={() => leavingChannel = true}>Leave channel…</button>
            {:else if details.owner}
              <p>You own this channel. Transfer it to another member or close it for everyone. History stays on each device.</p>
              {#if details.members.some(m => !m.isSelf)}
                <label for="next-channel-owner">Next owner</label>
                <select id="next-channel-owner" bind:value={nextOwner}>{#each details.members.filter(m => !m.isSelf) as member (member.id)}<option value={member.id}>{member.nickname}</option>{/each}</select>
                <button disabled={busy || !nextOwner} onclick={() => channelCommand(`/part --transfer ${nextOwner}`)}>Transfer and leave</button>
              {/if}
              <p class="muted">Closing stops new messages. Unconfirmed sends may not arrive; offline members learn of closure when they reconnect.</p>
              <button class="danger" disabled={busy} onclick={() => channelCommand('/part --close')}>Close for everyone</button>
              <button onclick={() => leavingChannel = false}>Cancel</button>
            {:else}
              <p>Leave this channel? Your history stays. Membership removal waits for the owner if they are offline.</p>
              <button disabled={busy} onclick={() => channelCommand('/part')}>Leave channel</button><button onclick={() => leavingChannel = false}>Cancel</button>
            {/if}
          </section>
        {/if}
      {/if}
    </dialog>
  {/if}
  {#if dialog}
    <dialog class="modal" use:showModal aria-labelledby="gchat-dialog-title" onclose={() => dialog = null}>
      <header><h2 id="gchat-dialog-title">{dialog === 'join' ? 'Join a channel' : 'Create a channel'}</h2><button aria-label="Close dialog" onclick={() => dialog = null}>×</button></header>
      {#if dialog === 'join'}<nav aria-label="Join method"><button aria-pressed={!browse} onclick={() => browse = false}>Paste invitation</button><button aria-pressed={browse} onclick={() => void loadDirectory()}>Browse channels</button></nav>{/if}
      {#if browse && dialog === 'join'}<button onclick={() => void loadDirectory(true)}>Refresh public directory</button>{#if directory}<CommandResult output={directory} choose={chooseChannel} />{/if}{/if}
      {#if dialog === 'join' && !browse && snapshot?.instance.capabilities.includes('networks.v1')}<NetworkSetup {transport} {imported} combined joined={invitationJoined} />{:else}
      {#if dialog === 'create' && networks.length > 1}<label for="create-network">Network</label><select id="create-network" bind:value={selectedNetwork} onchange={() => transport.select(selectedNetwork)}>{#each networks as network}<option value={network.id}>{network.name}</option>{/each}</select>{/if}
      <form onsubmit={join}><label for="gchat-destination">{dialog === 'join' ? 'Invitation link or public #channel' : 'Channel name'}</label><input id="gchat-destination" bind:value={destination} disabled={joinBusy} required placeholder={dialog === 'create' ? '#friends' : 'Paste an invitation'} /><label for="gchat-nickname">Your nickname in this channel</label><input id="gchat-nickname" bind:value={nickname} disabled={joinBusy} required autocomplete="nickname" />{#if joinError}<p role="alert">{joinError}</p>{/if}<button class="primary" type="submit" disabled={joinBusy}>{joinBusy ? 'Joining…' : dialog === 'join' ? 'Join' : 'Create'}</button></form>
      {/if}
    </dialog>
  {/if}
</div>

<style>
  .leave-actions { border-top:1px solid var(--line); margin-top:16px; padding-top:16px; }
  .leave-actions button { margin:6px 6px 0 0; }
  .danger { color:var(--danger, #ed9b9b); }
  .network-group { font-size:12px; color:var(--muted); margin-top:12px; }
  @font-face { font-family:GchatFixedsys; src:url('/fonts/fixedsys-excelsior.ttf') format('truetype'); font-display:swap; }
  .gchat { --bg:#1c1e22; --panel:#25282e; --line:#363c44; --ink:#e4e7eb; --muted:#a8b0bb; --accent:#b7cbe4; color-scheme:dark; position:var(--gchat-viewport-position,relative); top:var(--gchat-viewport-top,auto); width:100%; height:var(--gchat-viewport-height,100dvh); min-height:min(260px,var(--gchat-viewport-height,100dvh)); display:flex; flex-direction:column; overflow:hidden; background:var(--bg); color:var(--ink); font:15px/1.5 Inter,ui-sans-serif,system-ui,sans-serif; padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left); box-sizing:border-box; }
  .gchat :global(*) { box-sizing:border-box; }
  button,input,textarea { font:inherit; color:inherit; }
  button { background:transparent; border:1px solid transparent; padding:6px 10px; cursor:pointer; text-align:left; min-height:36px; }
  button:hover:not(:disabled) { background:#343b46; color:#fff; }
  button:focus-visible,input:focus-visible,textarea:focus-visible,summary:focus-visible { outline:2px solid var(--accent); outline-offset:-2px; }
  button:disabled { color:#818889; cursor:default; }
  small,.muted { color:var(--muted); }
  .sr-only { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap; }
  .file-picker { display:none; }
  .titlebar { min-height:52px; display:flex; gap:12px; align-items:center; padding:6px 12px; background:#17191c; border-bottom:1px solid var(--line); }
  .brand { display:inline-flex; align-items:center; gap:8px; flex:none; }
  .brand :global(.ghost-mark) { --ghost-mark-size:18px; }
  .brand strong { color:var(--accent); letter-spacing:1px; font-size:20px; line-height:1; }
  .active-title { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-weight:600; }
  .header-actions { display:flex; align-items:center; flex:none; gap:2px; }
  .header-actions button { white-space:nowrap; }
  .connection-dot { color:#bd9866; font-size:10px; margin-left:6px; }
  .connection-dot.connected { color:#91b5a0; }
  .count { display:inline-flex; align-items:center; gap:5px; font-variant-numeric:tabular-nums; }.count[aria-expanded=true] { background:#343b46; }
  .channel-toggle { display:none; }
  .workspace { display:flex; flex:1; min-height:0; position:relative; }
  .channels { background:#22262b; width:200px; flex-shrink:0; border-right:1px solid var(--line); display:flex; flex-direction:column; padding-top:8px; }
  .channel-entries { overflow:auto; flex:1; min-height:0; }
  .channels button { width:100%; display:flex; align-items:center; flex-wrap:wrap; gap:6px; padding:8px 12px; }
  .channels button small { width:100%; padding-left:22px; font-size:12px; overflow:hidden; text-overflow:ellipsis; }
  .channels .chosen { background:#303741; box-shadow:inset 2px 0 var(--accent); }
  .symbol { width:16px; color:var(--accent); flex-shrink:0; }
  .room-name { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .unread .room-name { color:var(--accent); font-weight:600; }
  .badge { font-size:12px; background:#3b4b62; border-radius:3px; padding:1px 5px; }
  .channel-actions { display:flex; flex-shrink:0; gap:4px; padding:8px; border-top:1px solid var(--line); }
  .channel-actions button { justify-content:center; padding:8px; }
  .conversation { flex:1; min-width:0; display:flex; flex-direction:column; }
  .welcome { flex:1; min-height:0; overflow:auto; padding:clamp(20px,4vw,48px); }
  h1 { font-size:24px; font-weight:normal; color:var(--accent); margin:16px 0; }
  p { margin:12px 0; }
  .welcome form,.network-gate { width:100%; max-width:640px; }
  .welcome form { max-width:400px; margin-top:24px; }
  .network-gate { align-self:center; }
  label { display:block; margin:12px 0 6px; }
  input { display:block; width:100%; border:1px solid #626969; background:#16181c; padding:10px; min-height:40px; }
  .primary { margin-top:12px; border:1px solid #566476; background:#343b46; padding:9px 14px; }
  dl { display:grid; grid-template-columns:max-content 1fr; gap:8px 18px; margin:24px 0; }
  dt { color:var(--accent); } dd { margin:0; color:var(--muted); }
  details { margin-top:20px; color:var(--muted); } summary { cursor:pointer; }
  .identity { overflow-wrap:anywhere; font-size:12px; }
  .transcript,.composer { font:16px/1.4 GchatFixedsys,'Lucida Console',monospace; }
  .readable .transcript,.readable .composer { font-family:ui-monospace,'SFMono-Regular',Consolas,monospace; line-height:1.5; }
  .transcript { flex:1; overflow:auto; min-height:0; padding:16px; scrollbar-color:#5a6561 #242728; }
  .message { display:grid; grid-template-columns:7ch auto 1fr; column-gap:8px; margin:3px 0; align-items:baseline; }
  time { color:#858f8e; font-size:14px; }
  .nick { color:#a9c7e8; max-width:24ch; overflow-wrap:anywhere; }
  .mine .nick { color:var(--accent); }
  .body { white-space:pre-wrap; overflow-wrap:anywhere; min-width:0; }
  .empty { color:var(--muted); }
  .date { margin:14px 0; color:var(--muted); text-align:center; border-bottom:1px solid var(--line); }
  .acceptance { font:11px/1.4 ui-sans-serif,system-ui,sans-serif; }
  .older { display:block; margin:0 auto 12px; border-color:var(--line); color:var(--accent); }
  .unread-divider { color:var(--accent); border-top:1px solid var(--accent); text-align:center; margin:12px 0; }
  .jump { align-self:center; min-height:40px; color:var(--accent); }
  .results { max-height:45%; overflow:auto; border-top:1px solid var(--line); }
  .notice { display:flex; background:#2b3037; border-top:1px solid #566476; max-height:38%; overflow:auto; padding:8px 12px; gap:10px; }
  .notice pre { font:inherit; white-space:pre-wrap; overflow-wrap:anywhere; flex:1; margin:0; min-width:0; }
  .notice button { align-self:flex-start; }
  .retry { padding:8px 12px; background:#4b3a27; display:flex; flex-wrap:wrap; align-items:center; gap:8px; }
  .retry button { border-color:#806640; }
  .provider-errors,.progress { padding:6px 16px; color:var(--muted); }
  .search { max-height:50%; overflow:auto; padding:12px 16px; border-bottom:1px solid var(--line); }
  .search p { overflow-wrap:anywhere; white-space:pre-wrap; }.search label { margin-top:0; }
  .composer { position:relative; display:flex; gap:8px; align-items:center; border-top:1px solid var(--line); background:#191d22; padding:10px 12px; }
  textarea { resize:none; flex:1; width:0; min-height:36px; max-height:160px; padding:8px 3px; border:0; background:transparent; field-sizing:content; }
  .attach { display:flex; align-items:center; justify-content:center; color:var(--muted); padding:8px; }
  .send { color:var(--accent); border-color:#566476; }
  .completions { position:absolute; bottom:100%; left:0; right:0; z-index:2; background:#303739; border:1px solid #566476; max-height:240px; overflow:auto; }
  .completions button { display:flex; gap:20px; width:100%; padding:9px 12px; }.completions span { color:var(--muted); }
  .inspector { width:300px; flex:none; overflow:auto; border-left:1px solid var(--line); background:#22262b; }
  .inspector-heading { display:flex; align-items:center; gap:4px; padding:8px; border-bottom:1px solid var(--line); position:sticky; top:0; background:#22262b; z-index:1; }
  .inspector-heading [role=tablist] { flex:1; display:flex; gap:4px; }.inspector-heading [aria-selected=true] { background:#343b46; }
  .inspector-heading small { margin-left:4px; }.users-list { padding:8px; }.users-list button { display:flex; justify-content:space-between; gap:8px; width:100%; overflow-wrap:anywhere; }.users-list .self { color:var(--accent); }
  .scrim { position:absolute; inset:0; z-index:3; background:#0008; width:100%;border:0; }
  .modal::backdrop { background:#0009; }.modal { color:var(--ink); margin:auto; width:min(500px,calc(100% - 24px)); max-height:88dvh; overflow:auto; background:var(--panel); border:1px solid #566476; padding:20px; box-shadow:0 14px 60px #0008; }
  .modal header { display:flex; align-items:center; gap:12px; margin-bottom:12px; }.modal h2 { flex:1; font-size:20px; font-weight:normal; margin:0; color:var(--accent); }
  .utility-modal { width:min(560px,calc(100% - 24px)); }.font-options { display:grid; gap:8px; }.font-options button { border:1px solid var(--line); padding:12px; }.font-options [aria-pressed=true] { border-color:var(--accent); }.font-options span { display:block; margin-top:8px; font-size:16px; }.font-fixed { font-family:GchatFixedsys,monospace; }.font-readable { font-family:ui-monospace,monospace; }.shortcuts { padding:12px; color:var(--muted); }.shortcuts h3 { font:inherit; color:var(--ink); }
  @media(max-width:999px) { .inspector { position:absolute; right:0; top:0; bottom:0; z-index:4; width:min(340px,90vw); box-shadow:-4px 0 20px #0006; } }
  @media(max-width:760px) {
    .channel-toggle { display:block; }.brand strong { display:none; }.titlebar { padding:6px 8px; gap:6px; }.header-actions button { padding:6px; }.titlebar button { min-height:40px; }
    .channels { display:none; position:absolute; top:0; bottom:0; left:0; z-index:4; width:min(280px,85vw); box-shadow:4px 0 20px #0006; }.channels.open { display:flex; }.channels button { min-height:44px; }
    .transcript { padding:12px; }.message { grid-template-columns:6ch 1fr; column-gap:6px; margin:7px 0; }.body { grid-column:2; }.nick { max-width:none; }time { font-size:12px; }
    .composer { padding:8px; }.composer textarea,.send,.attach { min-height:44px; }.welcome { padding:24px; }h1 { font-size:22px; }
    .completions button { flex-wrap:wrap; gap:4px; }.completions span { width:100%; font-size:12px; }.notice { max-height:32%; }
  }
  @media(max-width:440px) { .brand { display:none; }.connection-dot { margin:0; font-size:12px; }.active-title { padding-left:2px; }.header-actions { gap:0; } }
  @media(pointer:coarse) {
    button,summary { min-height:44px; min-width:44px; }
    input,textarea,select { font-size:16px; }
    .titlebar button { min-height:44px; }
    .modal { top:var(--gchat-viewport-top,0px); bottom:auto; margin-block:12px; max-height:calc(var(--gchat-viewport-height,100dvh) - 24px); }
  }
</style>
