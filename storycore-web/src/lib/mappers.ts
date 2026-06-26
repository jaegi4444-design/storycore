import type { Character, CharacterStatus } from '../types/character';
import type { Episode } from '../types/episode';
import type { Work, WorkOption } from '../types/work';
import type { WorldSetting, WorldSettingCategory } from '../types/worldSetting';

type WorkRow = {
  id: string;
  title: string;
  genre: string;
  one_line_summary: string;
  synopsis: string;
  author_note: string;
  ranks: WorkOption[] | null;
  jobs: WorkOption[] | null;
  affiliations: WorkOption[] | null;
  created_at: string;
  updated_at: string;
};

type CharacterRow = {
  id: string;
  work_id: string;
  name: string;
  alias: string;
  age: string;
  gender: string;
  affiliation: string;
  affiliation_detail: string;
  role: string;
  rank: string;
  job: string;
  rank_or_job?: string;
  abilities: string;
  personality: string;
  appearance: string;
  first_appearance_episode: number | null;
  current_status: string;
  public_info: string;
  secret_info: string;
  memo: string;
  image_url: string | null;
  created_at: string;
  updated_at: string;
};

type EpisodeRow = {
  id: string;
  work_id: string;
  episode_number: number;
  title: string;
  summary: string;
  character_ids: string[];
  locations: string[];
  revealed_settings: string;
  foreshadows: string;
  resolved_foreshadows: string;
  draft: string;
  author_note: string;
  created_at: string;
  updated_at: string;
};

type WorldSettingRow = {
  id: string;
  work_id: string;
  name: string;
  category: string;
  description: string;
  related_character_ids: string[];
  related_episode_ids: string[];
  memo: string;
  created_at: string;
  updated_at: string;
};

export function mapWork(row: WorkRow): Work {
  return {
    id: row.id,
    title: row.title,
    genre: row.genre,
    oneLineSummary: row.one_line_summary,
    synopsis: row.synopsis,
    authorNote: row.author_note,
    ranks: row.ranks ?? [],
    jobs: row.jobs ?? [],
    affiliations: row.affiliations ?? [],
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

export function mapCharacter(row: CharacterRow): Character {
  return {
    id: row.id,
    workId: row.work_id,
    name: row.name,
    alias: row.alias,
    age: row.age,
    gender: row.gender,
    affiliation: row.affiliation,
    affiliationDetail: row.affiliation_detail ?? '',
    role: row.role,
    rank: row.rank || row.rank_or_job || '',
    job: row.job ?? '',
    abilities: row.abilities,
    personality: row.personality,
    appearance: row.appearance,
    firstAppearanceEpisode: row.first_appearance_episode,
    currentStatus: row.current_status as CharacterStatus,
    publicInfo: row.public_info,
    secretInfo: row.secret_info,
    memo: row.memo,
    imageUrl: row.image_url,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

export function mapEpisode(row: EpisodeRow): Episode {
  return {
    id: row.id,
    workId: row.work_id,
    episodeNumber: row.episode_number,
    title: row.title,
    summary: row.summary,
    characterIds: row.character_ids,
    locations: row.locations,
    revealedSettings: row.revealed_settings,
    foreshadows: row.foreshadows,
    resolvedForeshadows: row.resolved_foreshadows,
    draft: row.draft,
    authorNote: row.author_note,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

export function mapWorldSetting(row: WorldSettingRow): WorldSetting {
  return {
    id: row.id,
    workId: row.work_id,
    name: row.name,
    category: row.category as WorldSettingCategory,
    description: row.description,
    relatedCharacterIds: row.related_character_ids,
    relatedEpisodeIds: row.related_episode_ids,
    memo: row.memo,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

export function toWorkInsert(userId: string, input: Omit<Work, 'id' | 'createdAt' | 'updatedAt'>) {
  return {
    user_id: userId,
    title: input.title,
    genre: input.genre,
    one_line_summary: input.oneLineSummary,
    synopsis: input.synopsis,
    author_note: input.authorNote,
    ranks: input.ranks,
    jobs: input.jobs,
    affiliations: input.affiliations,
  };
}

export function toWorkUpdate(input: Omit<Work, 'id' | 'createdAt' | 'updatedAt'>) {
  return {
    title: input.title,
    genre: input.genre,
    one_line_summary: input.oneLineSummary,
    synopsis: input.synopsis,
    author_note: input.authorNote,
    ranks: input.ranks,
    jobs: input.jobs,
    affiliations: input.affiliations,
    updated_at: new Date().toISOString(),
  };
}

export function toCharacterInsert(
  userId: string,
  input: Omit<Character, 'id' | 'createdAt' | 'updatedAt'>,
) {
  return {
    user_id: userId,
    work_id: input.workId,
    name: input.name,
    alias: input.alias,
    age: input.age,
    gender: input.gender,
    affiliation: input.affiliation,
    affiliation_detail: input.affiliationDetail,
    role: input.role,
    rank: input.rank,
    job: input.job,
    abilities: input.abilities,
    personality: input.personality,
    appearance: input.appearance,
    first_appearance_episode: input.firstAppearanceEpisode,
    current_status: input.currentStatus,
    public_info: input.publicInfo,
    secret_info: input.secretInfo,
    memo: input.memo,
    image_url: input.imageUrl,
  };
}

export function toEpisodeInsert(
  userId: string,
  input: Omit<Episode, 'id' | 'createdAt' | 'updatedAt'>,
) {
  return {
    user_id: userId,
    work_id: input.workId,
    episode_number: input.episodeNumber,
    title: input.title,
    summary: input.summary,
    character_ids: input.characterIds,
    locations: input.locations,
    revealed_settings: input.revealedSettings,
    foreshadows: input.foreshadows,
    resolved_foreshadows: input.resolvedForeshadows,
    draft: input.draft,
    author_note: input.authorNote,
  };
}

export function toWorldSettingInsert(
  userId: string,
  input: Omit<WorldSetting, 'id' | 'createdAt' | 'updatedAt'>,
) {
  return {
    user_id: userId,
    work_id: input.workId,
    name: input.name,
    category: input.category,
    description: input.description,
    related_character_ids: input.relatedCharacterIds,
    related_episode_ids: input.relatedEpisodeIds,
    memo: input.memo,
  };
}
