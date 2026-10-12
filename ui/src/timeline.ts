import type { Activity } from './api';
import type { OperationResult } from './operation-results';

const routine = new Set(['join', 'part', 'nickname', 'topic']);
/** Group only adjacent routine events, never across messages, dates or long gaps. */
export function groupActivity<T extends { id: string; timestamp: number; activity?: Activity }>(items: T[]): (T & { activities?: Activity[] })[] {
  const rows: (T & { activities?: Activity[] })[] = [];
  for (const item of items) {
    const previous = rows.at(-1);
    const last = previous?.activities?.at(-1);
    if (item.activity && routine.has(item.activity.kind) && last && routine.has(last.kind)
      && item.timestamp - last.timestamp <= 120
      && new Date(item.timestamp * 1000).toDateString() === new Date(last.timestamp * 1000).toDateString()) {
      previous!.activities!.push(item.activity);
    } else rows.push({ ...item, activities: item.activity ? [item.activity] : undefined });
  }
  return rows;
}

/** Hide only the machine identity suffix in known service event formats.
 * The original event remains available in Details; this is never used for identity matching. */
export function activitySummary(activity: Activity): string {
  if (!['join', 'policy'].includes(activity.kind)) return activity.text;
  return activity.text.replace(/ \([a-f0-9]{64}\)(?= )/gi, '');
}

export function operationLabel(result: OperationResult, checking = false): string {
  if (checking) return 'Checking…';
  if (result.state === 'pending') return result.action === '/join' ? 'Waiting for channel confirmation…' : 'Working…';
  if (result.state === 'unknown') return 'Outcome unconfirmed';
  if (result.state === 'rejected') return 'Not completed';
  const output = result.output;
  if (!output) return result.message && result.message !== 'Completed.' ? result.message : 'Done';
  if (output.kind === 'invitation' || output.kind === 'reusable_invitation') return 'Invitation created';
  if (output.kind === 'invitation_options') return 'Invitation options';
  if (output.kind === 'text') return output.title;
  if (output.kind === 'directory') return `${output.channels.length} channels found`;
  if (output.kind === 'status') return 'Connection status';
  if (output.kind === 'enrollment') return output.phase === 'joined' ? 'Joined channel' : 'Join saved';
  if (output.kind === 'enrollments') return 'Saved joins';
  if (output.kind === 'membership_recovery') return 'Membership recovery';
  if (output.kind === 'invitations') return 'Saved invitations';
  return 'Done';
}

export function fileSize(value: string): string {
  const bytes = Number(value);
  if (!Number.isFinite(bytes) || bytes < 0) return 'Size unavailable';
  if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(1)} GiB`;
  if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(1)} MiB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KiB`;
  return `${bytes.toLocaleString()} B`;
}
