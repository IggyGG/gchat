import type { NativeShell } from './native-shell';

// The native installer separately checks other windows and daemon activity.
// This guard owns only transient UI state, which the daemon cannot observe.
export class IdleUpdates {
  private quietSince: number;
  private retryAt = 0;
  private checking = false;
  constructor(private readonly now: () => number = () => performance.now(),
              private readonly activation: (active: boolean) => void = () => {}) {
    this.quietSince = now();
  }
  activity() { this.quietSince = this.now(); }
  async poll(updates: NativeShell['updates'], busy: () => boolean) {
    if (busy()) { this.activity(); return; }
    if (!updates || this.checking || this.now() - this.quietSince < 30_000 || this.now() < this.retryAt) return;
    this.checking = true;
    try {
      const status = await updates.status();
      // Input or a new operation can arrive while the native request is pending.
      if (busy() || this.now() - this.quietSince < 30_000) return;
      if (['ready', 'deferred'].includes(status.state)) {
        this.retryAt = this.now() + 60_000;
        this.activation(true);
        await updates.install();
      }
    } catch {
      // Native status retains the concrete deferral. Retry after activity clears.
      this.retryAt = this.now() + 60_000;
    } finally { this.activation(false); this.checking = false; }
  }
}
