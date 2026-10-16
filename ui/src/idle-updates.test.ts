import { describe, it, expect, vi } from 'vitest';
import { IdleUpdates } from './idle-updates';

describe('automatic activation', () => {
  it('does not restart after a startup check timeout without a verified update', async () => {
    let now = 0;
    const activation = vi.fn();
    const idle = new IdleUpdates(() => now, activation);
    const updates = {
      status: vi.fn(async () => ({ state: 'deferred', downloaded: 0,
        message: 'Startup update check timed out. GChat will check again in the background.' })),
      install: vi.fn(async () => {}), check: vi.fn()
    };
    now = 30_000; await idle.poll(updates, () => false);
    now += 60_000; await idle.poll(updates, () => false);
    expect(updates.install).not.toHaveBeenCalled();
    expect(activation).not.toHaveBeenCalledWith(true);
  });
  it('blocks new input before native maintenance and releases it on deferral', async () => {
    let now = 0, guarded = false;
    const idle = new IdleUpdates(() => now, active => { guarded = active; });
    const updates = { status: vi.fn(async () => ({state: 'ready', downloaded: 0, message: ''})),
      install: vi.fn(async () => { expect(guarded).toBe(true); throw Error('busy daemon'); }), check: vi.fn() };
    now = 30_000; await idle.poll(updates, () => false);
    expect(updates.install).toHaveBeenCalledOnce();
    expect(guarded).toBe(false);
  });
  it('honors revocation of a previously ready native target', async () => {
    let now = 0;
    const idle = new IdleUpdates(() => now);
    const updates = { status: vi.fn(async () => ({state:'ready',installable:false,downloaded:0,message:''})),
      install: vi.fn(async () => {}), check: vi.fn() };
    now = 30_000; await idle.poll(updates, () => false);
    expect(updates.install).not.toHaveBeenCalled();
  });
  it('waits for both quiet input and cleared drafts/actions', async () => {
    let now = 0, busy = true;
    const idle = new IdleUpdates(() => now);
    const updates = { status: vi.fn(async () => ({state: 'ready', downloaded: 0, message: ''})), install: vi.fn(async () => {}), check: vi.fn() };
    now = 60_000; await idle.poll(updates, () => busy);
    expect(updates.install).not.toHaveBeenCalled();
    busy = false; now += 29_999; await idle.poll(updates, () => busy);
    expect(updates.install).not.toHaveBeenCalled();
    now++; await idle.poll(updates, () => busy);
    expect(updates.install).toHaveBeenCalledOnce();
  });
  it('rechecks activity after awaiting native status and retries a deferral', async () => {
    let now = 0;
    const idle = new IdleUpdates(() => now);
    const updates = { status: vi.fn(async () => { idle.activity(); return {state: 'ready', downloaded: 0, message: ''}; }), install: vi.fn(async () => { throw Error('another window'); }), check: vi.fn() };
    now = 30_000; await idle.poll(updates, () => false);
    expect(updates.install).not.toHaveBeenCalled();
    updates.status.mockImplementation(async () => ({state: 'deferred', installable: true, downloaded: 0, message: ''}));
    now += 30_000; await idle.poll(updates, () => false);
    expect(updates.install).toHaveBeenCalledTimes(1);
    now++; await idle.poll(updates, () => false);
    expect(updates.install).toHaveBeenCalledTimes(1);
    now += 60_000; await idle.poll(updates, () => false);
    expect(updates.install).toHaveBeenCalledTimes(2);
  });
});
