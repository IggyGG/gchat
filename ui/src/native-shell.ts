export type ResizeDirection = 'East' | 'North' | 'NorthEast' | 'NorthWest' | 'South' | 'SouthEast' | 'SouthWest' | 'West';
export interface NativeShell {
  mac: boolean;
  updates?: {
    status(): Promise<UpdateStatus>;
    check(): Promise<UpdateStatus>;
    install(): Promise<void>;
  };
  minimize(): Promise<void>;
  maximize(): Promise<void>;
  close(): Promise<void>;
  resize(direction: ResizeDirection): Promise<void>;
  drag(): Promise<void>;
}

export interface UpdateStatus {
  state: string;
  /** Only a verified target may survive a deferred installation attempt. */
  installable?: boolean;
  version?: string;
  downloaded: number;
  total?: number;
  message: string;
  running?: { version: string; releaseId: string; gchatCommit: string; gcomsCommit: string };
}

export function canInstallUpdate(status: UpdateStatus | undefined): boolean {
  // Older native clients explicitly reported verified targets as ready, but a
  // deferred status alone also represented a timed-out startup check.
  return status?.state === 'ready' ? status.installable !== false
    : status?.state === 'deferred' && status.installable === true;
}
