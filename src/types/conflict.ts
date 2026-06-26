export type ConflictLevel = 'warning' | 'error';

export type Conflict = {
  id: string;
  level: ConflictLevel;
  title: string;
  description: string;
  relatedType: 'character' | 'episode' | 'worldSetting';
  relatedIds: string[];
};
