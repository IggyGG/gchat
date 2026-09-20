import type { CommandSpec, NetworkStatus } from './api';

/** These states are only returned after invitation import or retained setup. */
export function hasNetworkSetup(status: NetworkStatus | undefined): boolean {
  return !!status && ['local_only', 'connecting', 'connected', 'reconnecting', 'invitation_expired'].includes(status.state);
}
export function networkLabel(status: NetworkStatus | undefined, offline: boolean, locked: boolean): string {
  if (offline) return 'Service unavailable';
  if (locked) return 'Locked';
  const labels: Record<NetworkStatus['state'], string> = {
    locked: 'Locked', local_only: 'Local network', invitation_required: 'Setup needed', connecting: 'Connecting',
    connected: 'Connected', reconnecting: 'Reconnecting', invitation_expired: 'Invitation expired', unavailable: 'Unavailable',
  };
  return status ? labels[status.state] : 'Checking network';
}
export type LocalCommand = { name: 'font' | 'find' | 'help'; args: string };
export function localCommand(text: string): LocalCommand | undefined {
  const match = text.trim().match(/^\/(font|find|help)(?:\s+([\s\S]*))?$/i);
  return match ? { name: match[1].toLowerCase() as LocalCommand['name'], args: (match[2] ?? '').trim() } : undefined;
}
export function viewCommands(hasConversation: boolean): CommandSpec[] {
  return [
    { name: '/font', usage: '/font [fixedsys|readable]', description: 'Choose the chat font for this device', scope: 'view', capability: null, available: true },
    { name: '/find', usage: '/find [text]', description: 'Search this conversation · Ctrl/Cmd+F', scope: 'view', capability: null, available: hasConversation },
  ];
}
export function mergeViewCommands(commands: CommandSpec[], hasConversation: boolean): CommandSpec[] {
  const local = viewCommands(hasConversation);
  return [...commands.filter(c => !local.some(l => l.name === c.name)), ...local];
}
export type ChatFont = 'fixedsys' | 'readable';
export function readFont(): ChatFont {
  try { return localStorage.getItem('gchat.display.font') === 'readable' ? 'readable' : 'fixedsys'; } catch { return 'fixedsys'; }
}
export function writeFont(font: ChatFont) {
  try { localStorage.setItem('gchat.display.font', font); } catch { /* A display preference is optional. */ }
}
