import type { Response } from './api';

/** Optional native OS credential storage. The browser never reads saved keys. */
export type DeviceUnlock = {
  unlock(passphrase: string, create: boolean, remember: boolean): Promise<{ response: Response; warning?: string | null }>;
};
