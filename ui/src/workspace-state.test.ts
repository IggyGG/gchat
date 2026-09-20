import { describe, expect, it } from 'vitest';
import type { NetworkState } from './api';
import { hasNetworkSetup, localCommand, mergeViewCommands, networkLabel } from './workspace-state';

describe('network onboarding and view commands', () => {
  it('requires service evidence of a validated invitation or retained configuration', () => {
    expect(hasNetworkSetup(undefined)).toBe(false);
    for (const state of ['locked', 'invitation_required', 'unavailable'] as NetworkState[]) expect(hasNetworkSetup({ state, message: '' })).toBe(false);
    for (const state of ['connected', 'connecting', 'reconnecting', 'invitation_expired', 'local_only'] as NetworkState[]) expect(hasNetworkSetup({ state, message: '' })).toBe(true);
    expect(networkLabel({ state: 'reconnecting', message: '' }, false, false)).toBe('Reconnecting');
    expect(networkLabel({ state: 'connected', message: '' }, true, false)).toBe('Service unavailable');
  });
  it('keeps literal and provider input out of the local command handler', () => {
    expect(localCommand('/find the whole phrase')).toEqual({ name: 'find', args: 'the whole phrase' });
    expect(localCommand('/font readable')).toEqual({ name: 'font', args: 'readable' });
    for (const text of ['/say /font', '/finder text', 'hello /find', '/network join secret', '/cmd #c /find']) expect(localCommand(text)).toBeUndefined();
    const commands = mergeViewCommands([{ name: '/custom', usage: '/custom', description: 'Provider command', scope: 'provider', capability: null, available: false }], false);
    expect(commands.find(c => c.name === '/custom')?.available).toBe(false);
    expect(commands.find(c => c.name === '/find')?.available).toBe(false);
  });
});
