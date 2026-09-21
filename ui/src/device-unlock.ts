import type { Response } from './api';

/** Optional native OS credential storage. The browser never reads saved keys. */
export type MobilePushStatus = { enabled: boolean; permission: string; registered: boolean; message: string };
export type DeviceUnlock = {
  notifications?: {
    status(): Promise<MobilePushStatus>;
    configure(enabled: boolean): Promise<MobilePushStatus>;
  };
  unlock(passphrase: string, create: boolean, remember: boolean): Promise<{ response: Response; warning?: string | null }>;
};
