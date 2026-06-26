import type { Character } from '../types/character';
import type { Episode } from '../types/episode';
import type { Work } from '../types/work';
import type { WorldSetting } from '../types/worldSetting';
import { WORLD_SETTING_CATEGORY_LABELS } from '../types/worldSetting';

type PromptBuilderInput = {
  work: Work;
  episodes: Episode[];
  characters: Character[];
  worldSettings: WorldSetting[];
  targetEpisode: Episode;
};

const CAUTION_NOTES = `주의사항:
- 기존 설정과 충돌하지 않게 작성해줘.
- 인물의 성격과 말투를 유지해줘.
- 독자가 아직 모르는 비밀 설정은 직접적으로 노출하지 말고 암시만 해줘.
- 웹소설 문체로 가독성 좋게 작성해줘.`;

export function buildWritingPrompt({
  work,
  episodes,
  characters,
  worldSettings,
  targetEpisode,
}: PromptBuilderInput): string {
  const sortedEpisodes = [...episodes].sort((a, b) => a.episodeNumber - b.episodeNumber);
  const recentEpisodes = sortedEpisodes
    .filter((ep) => ep.episodeNumber < targetEpisode.episodeNumber)
    .slice(-3);

  const episodeCharacters = characters.filter((c) =>
    targetEpisode.characterIds.includes(c.id),
  );

  const sections: string[] = [];

  sections.push('# 작품 정보');
  sections.push(`- 제목: ${work.title}`);
  sections.push(`- 장르: ${work.genre}`);
  sections.push(`- 한 줄 소개: ${work.oneLineSummary}`);

  sections.push('');
  sections.push('# 전체 줄거리');
  sections.push(work.synopsis || '(없음)');

  sections.push('');
  sections.push('# 최근 3화 요약');
  if (recentEpisodes.length === 0) {
    sections.push('(이전 회차 없음)');
  } else {
    for (const ep of recentEpisodes) {
      sections.push(`## ${ep.episodeNumber}화: ${ep.title}`);
      sections.push(ep.summary || '(요약 없음)');
      sections.push('');
    }
  }

  sections.push('# 이번 회차 정보');
  sections.push(`- 회차: ${targetEpisode.episodeNumber}화`);
  sections.push(`- 제목: ${targetEpisode.title}`);
  sections.push(`- 요약: ${targetEpisode.summary || '(없음)'}`);
  sections.push(`- 등장 장소: ${targetEpisode.locations.length > 0 ? targetEpisode.locations.join(', ') : '(없음)'}`);
  sections.push(`- 새로 공개된 설정: ${targetEpisode.revealedSettings || '(없음)'}`);
  sections.push(`- 떡밥: ${targetEpisode.foreshadows || '(없음)'}`);
  sections.push(`- 회수한 떡밥: ${targetEpisode.resolvedForeshadows || '(없음)'}`);

  sections.push('');
  sections.push('# 이번 회차 등장 인물');
  if (episodeCharacters.length === 0) {
    sections.push('(등장 인물 없음)');
  } else {
    for (const character of episodeCharacters) {
      sections.push(`## ${character.name}${character.alias ? ` (${character.alias})` : ''}`);
      sections.push(`- 역할: ${character.role || '(없음)'}`);
      sections.push(`- 소속: ${character.affiliation || '(없음)'}`);
      sections.push(`- 등급/직업: ${character.rankOrJob || '(없음)'}`);
      sections.push(`- 능력: ${character.abilities || '(없음)'}`);
      sections.push(`- 성격: ${character.personality || '(없음)'}`);
      sections.push(`- 외형: ${character.appearance || '(없음)'}`);
      sections.push(`- 독자 공개 설정: ${character.publicInfo || '(없음)'}`);
      sections.push('');
    }
  }

  sections.push('# 세계관 설정');
  if (worldSettings.length === 0) {
    sections.push('(세계관 설정 없음)');
  } else {
    for (const setting of worldSettings) {
      sections.push(
        `## [${WORLD_SETTING_CATEGORY_LABELS[setting.category]}] ${setting.name}`,
      );
      sections.push(setting.description || '(설명 없음)');
      sections.push('');
    }
  }

  sections.push('# 주의사항');
  sections.push(CAUTION_NOTES);

  return sections.join('\n');
}
