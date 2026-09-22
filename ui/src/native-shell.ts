export type ResizeDirection = 'East' | 'North' | 'NorthEast' | 'NorthWest' | 'South' | 'SouthEast' | 'SouthWest' | 'West';
export interface NativeShell {
  mac: boolean;
  minimize(): Promise<void>;
  maximize(): Promise<void>;
  close(): Promise<void>;
  resize(direction: ResizeDirection): Promise<void>;
  drag(): Promise<void>;
}
