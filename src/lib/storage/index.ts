import { JsonFileStorageAdapter } from './json-adapter';
import { S3StorageAdapter } from './s3-adapter';
import type { StorageAdapter } from './types';

export type { StorageAdapter } from './types';

export function getStorageAdapter(): StorageAdapter {
  const backend = process.env.STORAGE_BACKEND || 'json';
  if (backend === 's3') {
    return new S3StorageAdapter();
  }
  const baseDir = process.env.JSON_STORAGE_DIR;
  return new JsonFileStorageAdapter(baseDir);
}





