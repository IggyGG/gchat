/** One opaque File handle in RAM. No bytes, credentials or selection are persisted. */
export type PickerTarget =
  | { kind: 'invitation'; context: 'setup' | 'network' | 'join'; network?: string }
  | { kind: 'outgoing'; conversation: string; network?: string; resumeId?: string };
export type PendingPickerView = {
  id: number; instance: string; target: Readonly<PickerTarget>; selected: boolean;
};
export type PickerClearReason = 'cancelled' | 'expired' | 'profile_changed' | 'completed' | 'discarded';
export const PICKER_TTL_MS = 5 * 60 * 1000;

export class PendingPicker {
  private value?: PendingPickerView;
  private file?: File;
  private timer?: ReturnType<typeof setTimeout>;
  private expires = 0;
  private sequence = 0;
  constructor(private changed: (view: PendingPickerView | undefined, reason?: PickerClearReason) => void) {}

  begin(instance: string, target: PickerTarget): number {
    this.clear('discarded');
    const id = ++this.sequence;
    this.expires = Date.now() + PICKER_TTL_MS;
    this.value = { id, instance, target: Object.freeze({ ...target }), selected: false };
    this.timer = setTimeout(() => this.clear('expired'), PICKER_TTL_MS);
    this.changed(this.value);
    return id;
  }
  private current(id?: number): PendingPickerView | undefined {
    if (this.value && Date.now() >= this.expires) this.clear('expired');
    return id === undefined || id === this.value?.id ? this.value : undefined;
  }
  receive(id: number, file: File | undefined): void {
    const current = this.current(id);
    if (!current) return;
    if (!file) { this.clear('cancelled'); return; }
    this.file = file;
    this.value = { ...current, selected: true };
    this.changed(this.value);
  }
  profile(instance: string): void {
    if (this.current()?.instance !== undefined && this.value?.instance !== instance) this.clear('profile_changed');
  }
  /** Called only by an explicit Continue action after refreshing unlocked state. */
  read(instance: string, unlocked: boolean): { view: PendingPickerView; file: File } | undefined {
    this.profile(instance);
    const view = this.current();
    return unlocked && view && this.file ? { view, file: this.file } : undefined;
  }
  complete(id: number): void { if (this.current(id)) this.clear('completed'); }
  clear(reason: PickerClearReason = 'discarded'): void {
    const hadValue = !!this.value;
    clearTimeout(this.timer); this.timer = undefined;
    this.value = undefined; this.file = undefined; this.expires = 0;
    if (hadValue) this.changed(undefined, reason);
  }
}
