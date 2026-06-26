export type WorldSettingCategory =
  | 'term'
  | 'organization'
  | 'location'
  | 'item'
  | 'ability'
  | 'monster'
  | 'event'
  | 'rankSystem';

export type WorldSetting = {
  id: string;
  workId: string;

  name: string;
  category: WorldSettingCategory;
  description: string;

  relatedCharacterIds: string[];
  relatedEpisodeIds: string[];

  memo: string;

  createdAt: string;
  updatedAt: string;
};

export type WorldSettingInput = Omit<WorldSetting, 'id' | 'createdAt' | 'updatedAt'>;

export const WORLD_SETTING_CATEGORY_LABELS: Record<WorldSettingCategory, string> = {
  term: '용어',
  organization: '조직',
  location: '지역',
  item: '아이템',
  ability: '능력',
  monster: '몬스터',
  event: '사건',
  rankSystem: '등급 체계',
};
