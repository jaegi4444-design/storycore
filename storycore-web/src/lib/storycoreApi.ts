import { supabase } from '../lib/supabase';
import {
  mapCharacter,
  mapEpisode,
  mapWork,
  mapWorldSetting,
  toCharacterInsert,
  toEpisodeInsert,
  toWorkInsert,
  toWorldSettingInsert,
} from '../lib/mappers';
import { deleteCharacterImageByUrl, uploadCharacterImage } from '../lib/characterImage';
import type { Character, CharacterSubmitPayload } from '../types/character';
import type { Episode, EpisodeInput } from '../types/episode';
import type { Work, WorkInput } from '../types/work';
import type { WorldSetting, WorldSettingInput } from '../types/worldSetting';

type SeedIds = {
  workId: string;
  characterIds: Record<string, string>;
  episodeIds: Record<string, string>;
};

export async function fetchAllUserData(userId: string) {
  const [worksRes, charactersRes, episodesRes, worldSettingsRes, prefsRes] = await Promise.all([
    supabase.from('works').select('*').eq('user_id', userId).order('created_at'),
    supabase.from('characters').select('*').eq('user_id', userId).order('created_at'),
    supabase.from('episodes').select('*').eq('user_id', userId).order('episode_number'),
    supabase.from('world_settings').select('*').eq('user_id', userId).order('created_at'),
    supabase.from('user_preferences').select('*').eq('user_id', userId).maybeSingle(),
  ]);

  if (worksRes.error) throw worksRes.error;
  if (charactersRes.error) throw charactersRes.error;
  if (episodesRes.error) throw episodesRes.error;
  if (worldSettingsRes.error) throw worldSettingsRes.error;
  if (prefsRes.error) throw prefsRes.error;

  return {
    works: worksRes.data.map(mapWork),
    characters: charactersRes.data.map(mapCharacter),
    episodes: episodesRes.data.map(mapEpisode),
    worldSettings: worldSettingsRes.data.map(mapWorldSetting),
    selectedWorkId: prefsRes.data?.selected_work_id ?? null,
  };
}

export async function seedSampleData(userId: string): Promise<SeedIds> {
  const { data: workRow, error: workError } = await supabase
    .from('works')
    .insert(
      toWorkInsert(userId, {
        title: '이세계 20년 후 귀환',
        genre: '현대판타지',
        oneLineSummary:
          '마왕을 토벌한 남자가 20년 만에 지구로 돌아와 D급 각성자로 위장한다.',
        synopsis:
          '김가온은 야근 중 모니터에서 열린 균열에 빨려 들어가 이세계로 이동한다. 20년 동안 살아남아 마왕을 토벌한 뒤 지구로 귀환하지만, 지구에도 게이트와 각성자가 존재하게 되었다. 그는 자신의 힘을 감추고 D급 각성자로 위장한 채 한국의 게이트 사건에 휘말린다.',
        authorNote: '',
      }),
    )
    .select('*')
    .single();

  if (workError) throw workError;
  const workId = workRow.id;

  const characterPayloads = [
    {
      key: 'gaon',
      data: {
        workId,
        name: '김가온',
        alias: '이클립스 워커',
        age: '31',
        gender: '남성',
        affiliation: '국가 각성자 서울팀',
        role: '주인공',
        rankOrJob: '외부 D급 / 실제 SSS급',
        abilities: 'Abyss Eye, Sense, Mapping, 어비스 쓰러스트',
        personality:
          '내성적이고 생각이 많다. 남에게 피해 주는 것을 싫어하고, 자신이 피해받는 것도 극도로 싫어한다.',
        appearance: '평범해 보이지만 전투 시 분위기가 달라진다.',
        firstAppearanceEpisode: 1,
        currentStatus: 'active' as const,
        publicInfo: 'D급으로 등록된 귀환자.',
        secretInfo: '이세계에서 마왕을 토벌한 실제 SSS급 강자.',
        memo: '',
        imageUrl: null,
      },
    },
    {
      key: 'sehoon',
      data: {
        workId,
        name: '오세훈',
        alias: '서울팀장',
        age: '38',
        gender: '남성',
        affiliation: '국가 각성자 서울팀',
        role: '팀장',
        rankOrJob: 'A급 기사계',
        abilities: '대검, 근접 전투, 지휘',
        personality: '진지하고 카리스마가 있다.',
        appearance: '185cm, 근육질, 숏컷.',
        firstAppearanceEpisode: 11,
        currentStatus: 'active' as const,
        publicInfo: '국가 각성자 서울팀의 팀장.',
        secretInfo: '김가온의 힘을 의심하기 시작한다.',
        memo: '',
        imageUrl: null,
      },
    },
    {
      key: 'serin',
      data: {
        workId,
        name: '백세린',
        alias: '백야',
        age: '29',
        gender: '여성',
        affiliation: '한빙그룹',
        role: 'S급 각성자',
        rankOrJob: 'S급 빙결계 검사',
        abilities: '빙결, 검술',
        personality: '차갑고 이성적이다.',
        appearance: '단정하고 서늘한 인상.',
        firstAppearanceEpisode: 12,
        currentStatus: 'active' as const,
        publicInfo: '대한민국 대표 S급 각성자 중 한 명.',
        secretInfo: '김가온에게 흥미를 느낀다.',
        memo: '',
        imageUrl: null,
      },
    },
  ];

  const characterIds: Record<string, string> = {};
  for (const payload of characterPayloads) {
    const { data, error } = await supabase
      .from('characters')
      .insert(toCharacterInsert(userId, payload.data))
      .select('*')
      .single();
    if (error) throw error;
    characterIds[payload.key] = data.id;
  }

  const episodeDefs = [
    {
      key: 'ep1',
      episodeNumber: 1,
      title: '야근 중 열린 균열',
      summary:
        '김가온은 대한화학 SI 프로젝트 야근 중 모니터에서 열린 균열에 빨려 들어간다.',
      characterIds: [characterIds.gaon],
    },
    {
      key: 'ep8',
      episodeNumber: 8,
      title: '데스나이트 조우',
      summary:
        '김가온은 이중 게이트 내부에서 데스나이트와 조우하고, 일행을 대피시킨 뒤 단독으로 격파한다.',
      characterIds: [characterIds.gaon],
    },
    {
      key: 'ep11',
      episodeNumber: 11,
      title: '가족 재회와 국가 각성자 회의',
      summary: '김가온은 가족과 재회하고, 국가 각성자 조직과 협상하게 된다.',
      characterIds: [characterIds.gaon, characterIds.sehoon],
    },
    {
      key: 'ep17',
      episodeNumber: 17,
      title: '서울팀 출근 전 하루',
      summary:
        '김가온은 서울팀 정식 출근 전 하루 휴식을 보내며, 다음 사건의 전조를 마주한다.',
      characterIds: [characterIds.gaon, characterIds.sehoon],
    },
  ];

  const episodeIds: Record<string, string> = {};
  for (const ep of episodeDefs) {
    const { data, error } = await supabase
      .from('episodes')
      .insert(
        toEpisodeInsert(userId, {
          workId,
          episodeNumber: ep.episodeNumber,
          title: ep.title,
          summary: ep.summary,
          characterIds: ep.characterIds,
          locations: [],
          revealedSettings: '',
          foreshadows: '',
          resolvedForeshadows: '',
          draft: '',
          authorNote: '',
        }),
      )
      .select('*')
      .single();
    if (error) throw error;
    episodeIds[ep.key] = data.id;
  }

  const worldSettings = [
    {
      name: '게이트',
      category: 'term' as const,
      description:
        '몬스터와 미궁이 등장하는 초자연적 통로. 색상에 따라 위험도가 다르다.',
      relatedCharacterIds: [] as string[],
      relatedEpisodeIds: [] as string[],
    },
    {
      name: '이중 게이트',
      category: 'term' as const,
      description:
        '게이트 내부에 또 다른 게이트 구조가 존재하는 희소 현상. 균열화 가능성이 높다.',
      relatedCharacterIds: [],
      relatedEpisodeIds: [episodeIds.ep8],
    },
    {
      name: '국가 각성자 서울팀',
      category: 'organization' as const,
      description: '대한민국 국가 각성자 조직의 서울 담당 전투팀.',
      relatedCharacterIds: [characterIds.gaon, characterIds.sehoon],
      relatedEpisodeIds: [episodeIds.ep11, episodeIds.ep17],
    },
    {
      name: 'Abyss Eye',
      category: 'ability' as const,
      description:
        '김가온이 사용하는 심연 계열 감지 능력. 적의 흐름과 약점을 파악할 수 있다.',
      relatedCharacterIds: [characterIds.gaon],
      relatedEpisodeIds: [],
    },
  ];

  for (const ws of worldSettings) {
    const { error } = await supabase.from('world_settings').insert(
      toWorldSettingInsert(userId, {
        workId,
        name: ws.name,
        category: ws.category,
        description: ws.description,
        relatedCharacterIds: ws.relatedCharacterIds,
        relatedEpisodeIds: ws.relatedEpisodeIds,
        memo: '',
      }),
    );
    if (error) throw error;
  }

  await supabase.from('user_preferences').upsert({
    user_id: userId,
    selected_work_id: workId,
  });

  return { workId, characterIds, episodeIds };
}

export async function upsertSelectedWork(userId: string, workId: string | null) {
  const { error } = await supabase.from('user_preferences').upsert({
    user_id: userId,
    selected_work_id: workId,
    updated_at: new Date().toISOString(),
  });
  if (error) throw error;
}

export async function createWork(userId: string, input: WorkInput): Promise<Work> {
  const { data, error } = await supabase
    .from('works')
    .insert(toWorkInsert(userId, input))
    .select('*')
    .single();
  if (error) throw error;
  return mapWork(data);
}

export async function updateWorkRecord(id: string, input: WorkInput): Promise<Work> {
  const { data, error } = await supabase
    .from('works')
    .update({
      title: input.title,
      genre: input.genre,
      one_line_summary: input.oneLineSummary,
      synopsis: input.synopsis,
      author_note: input.authorNote,
      updated_at: new Date().toISOString(),
    })
    .eq('id', id)
    .select('*')
    .single();
  if (error) throw error;
  return mapWork(data);
}

export async function deleteWorkRecord(id: string) {
  const { error } = await supabase.from('works').delete().eq('id', id);
  if (error) throw error;
}

export async function createCharacterWithImage(
  userId: string,
  payload: CharacterSubmitPayload,
): Promise<Character> {
  const { data, error } = await supabase
    .from('characters')
    .insert(toCharacterInsert(userId, { ...payload.data, imageUrl: null }))
    .select('*')
    .single();
  if (error) throw error;

  let imageUrl: string | null = null;
  if (payload.imageFile) {
    imageUrl = await uploadCharacterImage(userId, data.id, payload.imageFile);
    const { data: updated, error: updateError } = await supabase
      .from('characters')
      .update({ image_url: imageUrl, updated_at: new Date().toISOString() })
      .eq('id', data.id)
      .select('*')
      .single();
    if (updateError) throw updateError;
    return mapCharacter(updated);
  }

  return mapCharacter(data);
}

export async function updateCharacterWithImage(
  userId: string,
  id: string,
  payload: CharacterSubmitPayload,
  existingImageUrl: string | null,
): Promise<Character> {
  let imageUrl = payload.removeImage ? null : (payload.data.imageUrl ?? existingImageUrl);

  if (payload.imageFile) {
    imageUrl = await uploadCharacterImage(userId, id, payload.imageFile);
  } else if (payload.removeImage && existingImageUrl) {
    await deleteCharacterImageByUrl(existingImageUrl).catch(() => undefined);
  }

  const { data, error } = await supabase
    .from('characters')
    .update({
      ...toCharacterInsert(userId, { ...payload.data, imageUrl }),
      updated_at: new Date().toISOString(),
    })
    .eq('id', id)
    .select('*')
    .single();
  if (error) throw error;
  return mapCharacter(data);
}

export async function deleteCharacterRecord(character: Character) {
  if (character.imageUrl) {
    await deleteCharacterImageByUrl(character.imageUrl).catch(() => undefined);
  }
  const { error } = await supabase.from('characters').delete().eq('id', character.id);
  if (error) throw error;
}

export async function createEpisode(userId: string, input: EpisodeInput): Promise<Episode> {
  const { data, error } = await supabase
    .from('episodes')
    .insert(toEpisodeInsert(userId, input))
    .select('*')
    .single();
  if (error) throw error;
  return mapEpisode(data);
}

export async function updateEpisodeRecord(id: string, input: EpisodeInput): Promise<Episode> {
  const row = toEpisodeInsert('', input);
  const { data, error } = await supabase
    .from('episodes')
    .update({
      episode_number: row.episode_number,
      title: row.title,
      summary: row.summary,
      character_ids: row.character_ids,
      locations: row.locations,
      revealed_settings: row.revealed_settings,
      foreshadows: row.foreshadows,
      resolved_foreshadows: row.resolved_foreshadows,
      draft: row.draft,
      author_note: row.author_note,
      updated_at: new Date().toISOString(),
    })
    .eq('id', id)
    .select('*')
    .single();
  if (error) throw error;
  return mapEpisode(data);
}

export async function deleteEpisodeRecord(id: string) {
  const { error } = await supabase.from('episodes').delete().eq('id', id);
  if (error) throw error;
}

export async function createWorldSetting(
  userId: string,
  input: WorldSettingInput,
): Promise<WorldSetting> {
  const { data, error } = await supabase
    .from('world_settings')
    .insert(toWorldSettingInsert(userId, input))
    .select('*')
    .single();
  if (error) throw error;
  return mapWorldSetting(data);
}

export async function updateWorldSettingRecord(
  id: string,
  input: WorldSettingInput,
): Promise<WorldSetting> {
  const row = toWorldSettingInsert('', input);
  const { data, error } = await supabase
    .from('world_settings')
    .update({
      name: row.name,
      category: row.category,
      description: row.description,
      related_character_ids: row.related_character_ids,
      related_episode_ids: row.related_episode_ids,
      memo: row.memo,
      updated_at: new Date().toISOString(),
    })
    .eq('id', id)
    .select('*')
    .single();
  if (error) throw error;
  return mapWorldSetting(data);
}

export async function deleteWorldSettingRecord(id: string) {
  const { error } = await supabase.from('world_settings').delete().eq('id', id);
  if (error) throw error;
}

export type StoryCoreData = Awaited<ReturnType<typeof fetchAllUserData>>;

export async function reloadUserData(userId: string): Promise<StoryCoreData> {
  return fetchAllUserData(userId);
}
