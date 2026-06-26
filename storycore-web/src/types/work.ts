import { generateId } from '../utils/id';

export type WorkOption = {
  id: string;
  name: string;
};

export type Work = {
  id: string;
  title: string;
  genre: string;
  oneLineSummary: string;
  synopsis: string;
  authorNote: string;

  ranks: WorkOption[];
  jobs: WorkOption[];
  affiliations: WorkOption[];

  createdAt: string;
  updatedAt: string;
};

export type WorkInput = Omit<Work, 'id' | 'createdAt' | 'updatedAt'>;

export const MAX_WORKS_PER_USER = 1;

export function createWorkOption(name: string): WorkOption {
  return { id: generateId(), name: name.trim() };
}

export function hasRequiredWorkCategories(work: Pick<Work, 'ranks' | 'jobs' | 'affiliations'>): boolean {
  return work.ranks.length > 0 && work.jobs.length > 0 && work.affiliations.length > 0;
}

export function workCategoryError(work: Pick<Work, 'ranks' | 'jobs' | 'affiliations'>): string | null {
  if (work.ranks.length === 0) return '작품에 등급을 1개 이상 등록해주세요.';
  if (work.jobs.length === 0) return '작품에 직업을 1개 이상 등록해주세요.';
  if (work.affiliations.length === 0) return '작품에 소속을 1개 이상 등록해주세요.';
  return null;
}

export function toSelectOptions(options: WorkOption[]) {
  return options.map((o) => ({ value: o.name, label: o.name }));
}

/** 캐릭터 폼 셀렉트 — 작품 카테고리 + 기존 저장값(레거시) 포함 */
export function toCharacterSelectOptions(options: WorkOption[], currentValue = '') {
  const names = new Set<string>();
  for (const option of options) {
    if (option.name.trim()) names.add(option.name.trim());
  }
  if (currentValue.trim()) names.add(currentValue.trim());
  return Array.from(names)
    .sort((a, b) => a.localeCompare(b, 'ko'))
    .map((name) => ({ value: name, label: name }));
}

export function buildFilterOptions(
  workOptions: WorkOption[],
  characterValues: string[],
  allLabel: string,
) {
  const names = new Set<string>();
  for (const option of workOptions) {
    if (option.name.trim()) names.add(option.name.trim());
  }
  for (const value of characterValues) {
    if (value.trim()) names.add(value.trim());
  }
  return [
    { value: '', label: allLabel },
    ...Array.from(names)
      .sort((a, b) => a.localeCompare(b, 'ko'))
      .map((name) => ({ value: name, label: name })),
  ];
}
