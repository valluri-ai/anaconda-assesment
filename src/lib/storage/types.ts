export type StorageResult = {
  /** Fully qualified location/URI where the artifact was stored */
  uri: string;
  /** Backend identifier (e.g., 'json', 's3') */
  backend: string;
  /** Key or path within the backend */
  key: string;
};

export type SaveEventsOptions = {
  /** Optional desired file name (without extension); adapter may modify */
  filenameBase?: string;
};

export interface StorageAdapter {
  /** Persist a list of events and return where they were stored */
  saveEvents(events: unknown[], options?: SaveEventsOptions): Promise<StorageResult>;
}





