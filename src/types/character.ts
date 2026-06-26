export type CharacterStatus = 'active' | 'dead' | 'missing' | 'unknown';

export type Character = {
  id: string;
  workId: string;

  name: string;
  alias: string;
  age: string;
  gender: string;
  affiliation: string;
  role: string;
  rankOrJob: string;

  abilities: string;
  personality: string;
  appearance: string;

  firstAppearanceEpisode: number | null;
  currentStatus: CharacterStatus;

  publicInfo: string;
  secretInfo: string;
  memo: string;

  createdAt: string;
  updatedAt: string;
};

export type CharacterInput = Omit<Character, 'id' | 'createdAt' | 'updatedAt'>;

export const CHARACTER_STATUS_LABELS: Record<CharacterStatus, string> = {
  active: '활동 중',
  dead: '사망',
  missing: '실종',
  unknown: '불명',
};
