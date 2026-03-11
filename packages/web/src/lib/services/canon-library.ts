export interface CanonRecord {
  id: string;
  title: string;
  category: 'trait' | 'lore' | 'relationship' | 'setting';
  summary: string;
}

export const canonLibrarySeedRecords: CanonRecord[] = [];

export function getCanonLibrarySeedRecords(): CanonRecord[] {
  return canonLibrarySeedRecords;
}