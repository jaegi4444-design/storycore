import type { StoryCoreData } from './storycoreApi';
import {
  isLocalStorageEmpty,
  sampleCharacters,
  sampleEpisodes,
  sampleWorldSettings,
  sampleWork,
  seedLocalSampleData,
} from '../data/sampleData';
import { fileToDataUrl } from './characterImage';
import type { Character, CharacterSubmitPayload } from '../types/character';
import type { Episode, EpisodeInput } from '../types/episode';
import type { Work, WorkInput } from '../types/work';
import { MAX_WORKS_PER_USER } from '../types/work';
import type { WorldSetting, WorldSettingInput } from '../types/worldSetting';
import { generateId, nowISO } from '../utils/id';

const KEYS = {
  works: 'storycore_works',
  characters: 'storycore_characters',
  episodes: 'storycore_episodes',
  worldSettings: 'storycore_world_settings',
  selectedWorkId: 'storycore_selected_work_id',
} as const;

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function write<T>(key: string, value: T): void {
  localStorage.setItem(key, JSON.stringify(value));
}

function migrateWork(work: Work & { ranks?: Work['ranks']; jobs?: Work['jobs']; affiliations?: Work['affiliations'] }): Work {
  return {
    ...work,
    ranks: work.ranks ?? [],
    jobs: work.jobs ?? [],
    affiliations: work.affiliations ?? [],
  };
}

function migrateCharacter(raw: Character & { rankOrJob?: string }): Character {
  if ('rankOrJob' in raw && raw.rankOrJob !== undefined) {
    const { rankOrJob, ...rest } = raw;
    return {
      ...rest,
      rank: rest.rank || rankOrJob || '',
      job: rest.job ?? '',
      affiliationDetail: rest.affiliationDetail ?? '',
    };
  }
  return {
    ...raw,
    rank: raw.rank ?? '',
    job: raw.job ?? '',
    affiliationDetail: raw.affiliationDetail ?? '',
  };
}

export function fetchLocalData(): StoryCoreData {
  if (isLocalStorageEmpty()) {
    seedLocalSampleData();
  }

  return {
    works: read<Work[]>(KEYS.works, [sampleWork]).map(migrateWork),
    characters: read<Character[]>(KEYS.characters, sampleCharacters).map(migrateCharacter),
    episodes: read<Episode[]>(KEYS.episodes, sampleEpisodes),
    worldSettings: read<WorldSetting[]>(KEYS.worldSettings, sampleWorldSettings),
    selectedWorkId: localStorage.getItem(KEYS.selectedWorkId),
  };
}

export function upsertLocalSelectedWork(workId: string | null): void {
  if (workId === null) {
    localStorage.removeItem(KEYS.selectedWorkId);
  } else {
    localStorage.setItem(KEYS.selectedWorkId, workId);
  }
}

export function createLocalWork(input: WorkInput): Work {
  const works = read<Work[]>(KEYS.works, []);
  if (works.length >= MAX_WORKS_PER_USER) {
    throw new Error('작품은 1개만 등록할 수 있습니다.');
  }
  const now = nowISO();
  const work: Work = { ...input, id: generateId(), createdAt: now, updatedAt: now };
  write(KEYS.works, [...works, work]);
  return work;
}

export function updateLocalWork(id: string, input: WorkInput): Work {
  const works = read<Work[]>(KEYS.works, []);
  const updated = works.map((w) =>
    w.id === id ? { ...w, ...input, updatedAt: nowISO() } : w,
  );
  write(KEYS.works, updated);
  return updated.find((w) => w.id === id)!;
}

export function deleteLocalWork(id: string): void {
  write(
    KEYS.works,
    read<Work[]>(KEYS.works, []).filter((w) => w.id !== id),
  );
}

async function resolveImageUrl(
  payload: CharacterSubmitPayload,
  existingUrl: string | null,
): Promise<string | null> {
  if (payload.removeImage) return null;
  if (payload.imageFile) return fileToDataUrl(payload.imageFile);
  return payload.data.imageUrl ?? existingUrl;
}

export async function createLocalCharacter(payload: CharacterSubmitPayload): Promise<Character> {
  const now = nowISO();
  const id = generateId();
  const imageUrl = await resolveImageUrl(payload, null);
  const character: Character = {
    ...payload.data,
    id,
    imageUrl,
    createdAt: now,
    updatedAt: now,
  };
  const characters = read<Character[]>(KEYS.characters, []);
  write(KEYS.characters, [...characters, character]);
  return character;
}

export async function updateLocalCharacter(
  id: string,
  payload: CharacterSubmitPayload,
  existingImageUrl: string | null,
): Promise<Character> {
  const imageUrl = await resolveImageUrl(payload, existingImageUrl);
  const characters = read<Character[]>(KEYS.characters, []);
  const updated = characters.map((c) =>
    c.id === id
      ? { ...c, ...payload.data, imageUrl, updatedAt: nowISO() }
      : c,
  );
  write(KEYS.characters, updated);
  return updated.find((c) => c.id === id)!;
}

export function deleteLocalCharacter(id: string): void {
  write(
    KEYS.characters,
    read<Character[]>(KEYS.characters, []).filter((c) => c.id !== id),
  );
}

export function createLocalEpisode(input: EpisodeInput): Episode {
  const now = nowISO();
  const episode: Episode = { ...input, id: generateId(), createdAt: now, updatedAt: now };
  const episodes = read<Episode[]>(KEYS.episodes, []);
  write(KEYS.episodes, [...episodes, episode]);
  return episode;
}

export function updateLocalEpisode(id: string, input: EpisodeInput): Episode {
  const episodes = read<Episode[]>(KEYS.episodes, []);
  const updated = episodes.map((e) =>
    e.id === id ? { ...e, ...input, updatedAt: nowISO() } : e,
  );
  write(KEYS.episodes, updated);
  return updated.find((e) => e.id === id)!;
}

export function deleteLocalEpisode(id: string): void {
  write(
    KEYS.episodes,
    read<Episode[]>(KEYS.episodes, []).filter((e) => e.id !== id),
  );
}

export function createLocalWorldSetting(input: WorldSettingInput): WorldSetting {
  const now = nowISO();
  const setting: WorldSetting = {
    ...input,
    id: generateId(),
    createdAt: now,
    updatedAt: now,
  };
  const settings = read<WorldSetting[]>(KEYS.worldSettings, []);
  write(KEYS.worldSettings, [...settings, setting]);
  return setting;
}

export function updateLocalWorldSetting(id: string, input: WorldSettingInput): WorldSetting {
  const settings = read<WorldSetting[]>(KEYS.worldSettings, []);
  const updated = settings.map((s) =>
    s.id === id ? { ...s, ...input, updatedAt: nowISO() } : s,
  );
  write(KEYS.worldSettings, updated);
  return updated.find((s) => s.id === id)!;
}

export function deleteLocalWorldSetting(id: string): void {
  write(
    KEYS.worldSettings,
    read<WorldSetting[]>(KEYS.worldSettings, []).filter((s) => s.id !== id),
  );
}
