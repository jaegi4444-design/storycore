import type { Character } from '../types/character';
import type { Episode } from '../types/episode';
import type { Work } from '../types/work';
import type { WorldSetting } from '../types/worldSetting';
import { nowISO } from '../utils/id';

const timestamp = nowISO();

export const SAMPLE_WORK_ID = 'sample-work-1';
export const SAMPLE_CHARACTER_IDS = {
  gaon: 'sample-char-gaon',
  sehoon: 'sample-char-sehoon',
  serin: 'sample-char-serin',
} as const;

export const SAMPLE_EPISODE_IDS = {
  ep1: 'sample-ep-1',
  ep8: 'sample-ep-8',
  ep11: 'sample-ep-11',
  ep17: 'sample-ep-17',
} as const;

export const SAMPLE_WORLD_SETTING_IDS = {
  gate: 'sample-ws-gate',
  doubleGate: 'sample-ws-double-gate',
  seoulTeam: 'sample-ws-seoul-team',
  abyssEye: 'sample-ws-abyss-eye',
} as const;

export const sampleWork: Work = {
  id: SAMPLE_WORK_ID,
  title: '이세계 20년 후 귀환',
  genre: '현대판타지',
  oneLineSummary:
    '마왕을 토벌한 남자가 20년 만에 지구로 돌아와 D급 각성자로 위장한다.',
  synopsis:
    '김가온은 야근 중 모니터에서 열린 균열에 빨려 들어가 이세계로 이동한다. 20년 동안 살아남아 마왕을 토벌한 뒤 지구로 귀환하지만, 지구에도 게이트와 각성자가 존재하게 되었다. 그는 자신의 힘을 감추고 D급 각성자로 위장한 채 한국의 게이트 사건에 휘말린다.',
  authorNote: '',
  createdAt: timestamp,
  updatedAt: timestamp,
};

export const sampleCharacters: Character[] = [
  {
    id: SAMPLE_CHARACTER_IDS.gaon,
    workId: SAMPLE_WORK_ID,
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
    currentStatus: 'active',
    publicInfo: 'D급으로 등록된 귀환자.',
    secretInfo: '이세계에서 마왕을 토벌한 실제 SSS급 강자.',
    memo: '',
    createdAt: timestamp,
    updatedAt: timestamp,
  },
  {
    id: SAMPLE_CHARACTER_IDS.sehoon,
    workId: SAMPLE_WORK_ID,
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
    currentStatus: 'active',
    publicInfo: '국가 각성자 서울팀의 팀장.',
    secretInfo: '김가온의 힘을 의심하기 시작한다.',
    memo: '',
    createdAt: timestamp,
    updatedAt: timestamp,
  },
  {
    id: SAMPLE_CHARACTER_IDS.serin,
    workId: SAMPLE_WORK_ID,
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
    currentStatus: 'active',
    publicInfo: '대한민국 대표 S급 각성자 중 한 명.',
    secretInfo: '김가온에게 흥미를 느낀다.',
    memo: '',
    createdAt: timestamp,
    updatedAt: timestamp,
  },
];

export const sampleEpisodes: Episode[] = [
  {
    id: SAMPLE_EPISODE_IDS.ep1,
    workId: SAMPLE_WORK_ID,
    episodeNumber: 1,
    title: '야근 중 열린 균열',
    summary:
      '김가온은 대한화학 SI 프로젝트 야근 중 모니터에서 열린 균열에 빨려 들어간다.',
    characterIds: [SAMPLE_CHARACTER_IDS.gaon],
    locations: [],
    revealedSettings: '',
    foreshadows: '',
    resolvedForeshadows: '',
    draft: '',
    authorNote: '',
    createdAt: timestamp,
    updatedAt: timestamp,
  },
  {
    id: SAMPLE_EPISODE_IDS.ep8,
    workId: SAMPLE_WORK_ID,
    episodeNumber: 8,
    title: '데스나이트 조우',
    summary:
      '김가온은 이중 게이트 내부에서 데스나이트와 조우하고, 일행을 대피시킨 뒤 단독으로 격파한다.',
    characterIds: [SAMPLE_CHARACTER_IDS.gaon],
    locations: [],
    revealedSettings: '',
    foreshadows: '',
    resolvedForeshadows: '',
    draft: '',
    authorNote: '',
    createdAt: timestamp,
    updatedAt: timestamp,
  },
  {
    id: SAMPLE_EPISODE_IDS.ep11,
    workId: SAMPLE_WORK_ID,
    episodeNumber: 11,
    title: '가족 재회와 국가 각성자 회의',
    summary:
      '김가온은 가족과 재회하고, 국가 각성자 조직과 협상하게 된다.',
    characterIds: [SAMPLE_CHARACTER_IDS.gaon, SAMPLE_CHARACTER_IDS.sehoon],
    locations: [],
    revealedSettings: '',
    foreshadows: '',
    resolvedForeshadows: '',
    draft: '',
    authorNote: '',
    createdAt: timestamp,
    updatedAt: timestamp,
  },
  {
    id: SAMPLE_EPISODE_IDS.ep17,
    workId: SAMPLE_WORK_ID,
    episodeNumber: 17,
    title: '서울팀 출근 전 하루',
    summary:
      '김가온은 서울팀 정식 출근 전 하루 휴식을 보내며, 다음 사건의 전조를 마주한다.',
    characterIds: [SAMPLE_CHARACTER_IDS.gaon, SAMPLE_CHARACTER_IDS.sehoon],
    locations: [],
    revealedSettings: '',
    foreshadows: '',
    resolvedForeshadows: '',
    draft: '',
    authorNote: '',
    createdAt: timestamp,
    updatedAt: timestamp,
  },
];

export const sampleWorldSettings: WorldSetting[] = [
  {
    id: SAMPLE_WORLD_SETTING_IDS.gate,
    workId: SAMPLE_WORK_ID,
    name: '게이트',
    category: 'term',
    description:
      '몬스터와 미궁이 등장하는 초자연적 통로. 색상에 따라 위험도가 다르다.',
    relatedCharacterIds: [],
    relatedEpisodeIds: [],
    memo: '',
    createdAt: timestamp,
    updatedAt: timestamp,
  },
  {
    id: SAMPLE_WORLD_SETTING_IDS.doubleGate,
    workId: SAMPLE_WORK_ID,
    name: '이중 게이트',
    category: 'term',
    description:
      '게이트 내부에 또 다른 게이트 구조가 존재하는 희소 현상. 균열화 가능성이 높다.',
    relatedCharacterIds: [],
    relatedEpisodeIds: [SAMPLE_EPISODE_IDS.ep8],
    memo: '',
    createdAt: timestamp,
    updatedAt: timestamp,
  },
  {
    id: SAMPLE_WORLD_SETTING_IDS.seoulTeam,
    workId: SAMPLE_WORK_ID,
    name: '국가 각성자 서울팀',
    category: 'organization',
    description: '대한민국 국가 각성자 조직의 서울 담당 전투팀.',
    relatedCharacterIds: [SAMPLE_CHARACTER_IDS.gaon, SAMPLE_CHARACTER_IDS.sehoon],
    relatedEpisodeIds: [SAMPLE_EPISODE_IDS.ep11, SAMPLE_EPISODE_IDS.ep17],
    memo: '',
    createdAt: timestamp,
    updatedAt: timestamp,
  },
  {
    id: SAMPLE_WORLD_SETTING_IDS.abyssEye,
    workId: SAMPLE_WORK_ID,
    name: 'Abyss Eye',
    category: 'ability',
    description:
      '김가온이 사용하는 심연 계열 감지 능력. 적의 흐름과 약점을 파악할 수 있다.',
    relatedCharacterIds: [SAMPLE_CHARACTER_IDS.gaon],
    relatedEpisodeIds: [],
    memo: '',
    createdAt: timestamp,
    updatedAt: timestamp,
  },
];

export function createSampleData() {
  return {
    works: [sampleWork],
    characters: sampleCharacters,
    episodes: sampleEpisodes,
    worldSettings: sampleWorldSettings,
    selectedWorkId: SAMPLE_WORK_ID,
  };
}

export function isStorageEmpty(): boolean {
  return !localStorage.getItem('storycore_works');
}

export function initializeSampleDataIfEmpty(): void {
  if (!isStorageEmpty()) return;

  const data = createSampleData();
  localStorage.setItem('storycore_works', JSON.stringify(data.works));
  localStorage.setItem('storycore_characters', JSON.stringify(data.characters));
  localStorage.setItem('storycore_episodes', JSON.stringify(data.episodes));
  localStorage.setItem(
    'storycore_world_settings',
    JSON.stringify(data.worldSettings),
  );
  localStorage.setItem('storycore_selected_work_id', data.selectedWorkId);
}
