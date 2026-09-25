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
  version?: string;
  downloaded: number;
  total?: number;
  message: string;
  running?: { version: string; releaseId: string; gchatCommit: string; gcomsCommit: string };
}
