import fs from 'fs/promises';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { StorageAdapter, StorageResult, SaveEventsOptions } from './types';

export class JsonFileStorageAdapter implements StorageAdapter {
  private readonly baseDir: string;

  constructor(baseDir: string = path.join(process.cwd(), 'storage')) {
    this.baseDir = baseDir;
  }

  async saveEvents(events: unknown[], options?: SaveEventsOptions): Promise<StorageResult> {
    const filenameBase = options?.filenameBase || `events-${uuidv4()}`;
    const filename = `${filenameBase}.json`;
    const dir = this.baseDir;
    const fullPath = path.join(dir, filename);

    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(fullPath, JSON.stringify(events, null, 2), 'utf-8');

    return {
      uri: `file://${fullPath}`,
      backend: 'json',
      key: filename,
    };
  }
}





