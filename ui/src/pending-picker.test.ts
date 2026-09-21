import { afterEach, describe, expect, it, vi } from 'vitest';
import { PendingPicker, PICKER_TTL_MS, type PickerTarget } from './pending-picker';

afterEach(() => vi.useRealTimers());
describe('pending native picker', () => {
  it('keeps one unread handle through lock until the same profile is unlocked', () => {
    const changed = vi.fn(), picker = new PendingPicker(changed);
    const file = new File(['private fixture'], 'private.txt'), read = vi.spyOn(file, 'text');
    const id = picker.begin('profile-a', { kind: 'outgoing', conversation: 'channel/general', network: 'network-a' });
    picker.receive(id, file);
    expect(picker.read('profile-a', false)).toBeUndefined();
    expect(picker.read('profile-a', true)).toMatchObject({ file, view: { id, target: { conversation: 'channel/general', network: 'network-a' } } });
    expect(read).not.toHaveBeenCalled();
    picker.complete(id);
    expect(picker.read('profile-a', true)).toBeUndefined();
  });
  it('drops the selection on profile replacement and cannot revive it by returning', () => {
    const picker = new PendingPicker(vi.fn());
    const id = picker.begin('profile-a', { kind: 'invitation', context: 'setup' });
    picker.receive(id, new File(['fixture'], 'invite.txt'));
    expect(picker.read('profile-b', true)).toBeUndefined();
    expect(picker.read('profile-a', true)).toBeUndefined();
  });
  it('bounds RAM ownership and rejects late results from an expired or replaced picker', () => {
    vi.useFakeTimers();
    const changed = vi.fn(), picker = new PendingPicker(changed);
    const old = picker.begin('profile-a', { kind: 'invitation', context: 'setup' });
    vi.advanceTimersByTime(PICKER_TTL_MS);
    expect(changed).toHaveBeenLastCalledWith(undefined, 'expired');
    const current = picker.begin('profile-a', { kind: 'invitation', context: 'join' });
    picker.receive(old, new File(['old'], 'old.txt'));
    expect(picker.read('profile-a', true)).toBeUndefined();
    picker.receive(current, new File(['current'], 'current.txt'));
    expect(picker.read('profile-a', true)?.file.name).toBe('current.txt');
    picker.clear();
  });
  it('captures the original destination and cancellation releases it', () => {
    const changed = vi.fn(), picker = new PendingPicker(changed);
    const target: PickerTarget = { kind: 'outgoing', conversation: 'channel/general', resumeId: 'retained-operation' };
    const id = picker.begin('profile-a', target);
    target.conversation = 'channel/other';
    picker.receive(id, new File(['fixture'], 'share.txt'));
    expect(picker.read('profile-a', true)?.view.target).toMatchObject({ conversation: 'channel/general', resumeId: 'retained-operation' });
    picker.receive(id, undefined);
    expect(picker.read('profile-a', true)).toBeUndefined();
    expect(changed).toHaveBeenLastCalledWith(undefined, 'cancelled');
  });
});
