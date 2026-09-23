import { describe, expect, it } from 'vitest';
import { OperationResults } from './operation-results';

describe('operation results', () => {
  it('restores terminal results without applying an original response twice', () => {
    const results = new OperationResults();
    const record = results.begin('instance', 'network', 'one', 'channel/a', '/invite');
    results.restore([{ id: 'one', instance: 'instance', network: 'network', conversation: 'channel/a', action: '/invite', started: 1, state: 'complete', output: null, message: 'Completed' }], () => 'other');
    expect(results.get(record.key)?.state).toBe('complete');
    expect(results.complete(record.key, { kind: 'applied', conversation: 'channel/a', notice: null })).toBe(true);
    expect(results.complete(record.key, { kind: 'applied', conversation: 'channel/a', notice: null })).toBe(false);
  });
  it('coalesces original and recovered replies, while keeping separately requested invitations', () => {
    const results = new OperationResults();
    const response = { kind: 'output' as const, conversation: 'channel/a', output: { kind: 'text' as const, title: 'Invite', text: 'result' } };
    const first = results.begin('instance', 'network', 'one', null, '/invite SECRET');
    expect(first.action).toBe('/invite');
    expect(results.complete(first.key, response)).toBe(true);
    expect(results.complete(first.key, response)).toBe(false);
    results.error(first.key, 'outcome_unknown', 'late poll failed');
    expect(results.get(first.key)?.state).toBe('complete');
    results.begin('instance', 'network', 'two', null, '/invite');
    results.begin('instance', 'other-network', 'one', null);
    results.begin('other-instance', 'network', 'one', null);
    expect(results.values()).toHaveLength(4);
    results.clear();
    expect(results.values()).toEqual([]);
  });
  it('does not erase a fresh check response with an older unknown snapshot', () => {
    const results = new OperationResults();
    const detail = { id: 'one', instance: 'instance', network: 'network', conversation: 'channel/a', action: '/create', started: 1, state: 'unknown' as const, output: null, message: 'Interrupted after admission.' };
    results.restore([detail], () => 'network');
    const key = results.key('instance', 'network', 'one');
    results.error(key, 'outcome_unknown', 'No new result is available.');
    const checked = results.get(key)?.checked;
    results.restore([detail], () => 'network');
    expect(results.get(key)?.message).toBe('No new result is available.');
    expect(results.get(key)?.recordedMessage).toBe('Interrupted after admission.');
    expect(results.get(key)?.checked).toBe(checked);
    results.restore([{ ...detail, state: 'complete', message: 'Completed.' }], () => 'network');
    expect(results.get(key)?.state).toBe('complete');
  });

  it('keeps the recorded failure visible without turning uncertainty into success', () => {
    const results = new OperationResults();
    const record = results.begin('instance', 'network', 'one', 'channel/a', '/reconnect PRIVATE');
    results.error(record.key, 'outcome_unknown', 'Operation was interrupted after admission.');
    results.restore([{ id: 'one', instance: 'instance', network: 'network', conversation: 'channel/a', action: '/reconnect', started: 1, state: 'unknown', output: null, message: 'local channel route is still reconnecting; try again when ready' }], () => 'network');
    expect(results.get(record.key)?.state).toBe('unknown');
    expect(results.get(record.key)?.message).toBe('Operation was interrupted after admission.');
    expect(results.get(record.key)?.recordedMessage).toContain('local channel route is still reconnecting');
    expect(JSON.stringify(results.values())).not.toContain('PRIVATE');
  });

});
