import type { Character } from '../types/character';
import type { Conflict } from '../types/conflict';
import type { Episode } from '../types/episode';
import { generateId } from './id';

type ConflictCheckInput = {
  characters: Character[];
  episodes: Episode[];
};

export function checkConflicts({ characters, episodes }: ConflictCheckInput): Conflict[] {
  const conflicts: Conflict[] = [];

  checkDuplicateCharacterNames(characters, conflicts);
  checkEarlyAppearance(characters, episodes, conflicts);
  checkDeadCharacterAppearance(characters, episodes, conflicts);

  return conflicts;
}

function checkDuplicateCharacterNames(characters: Character[], conflicts: Conflict[]): void {
  const nameMap = new Map<string, Character[]>();

  for (const character of characters) {
    const key = character.name.trim().toLowerCase();
    if (!key) continue;
    const existing = nameMap.get(key) ?? [];
    existing.push(character);
    nameMap.set(key, existing);
  }

  for (const [, group] of nameMap) {
    if (group.length >= 2) {
      conflicts.push({
        id: generateId(),
        level: 'warning',
        title: `중복 캐릭터 이름: "${group[0].name}"`,
        description: `같은 작품 안에서 "${group[0].name}" 이름의 캐릭터가 ${group.length}명 있습니다.`,
        relatedType: 'character',
        relatedIds: group.map((c) => c.id),
      });
    }
  }
}

function checkEarlyAppearance(
  characters: Character[],
  episodes: Episode[],
  conflicts: Conflict[],
): void {
  for (const character of characters) {
    if (character.firstAppearanceEpisode === null) continue;

    for (const episode of episodes) {
      if (
        episode.characterIds.includes(character.id) &&
        episode.episodeNumber < character.firstAppearanceEpisode
      ) {
        conflicts.push({
          id: generateId(),
          level: 'error',
          title: `첫 등장 회차 불일치: ${character.name}`,
          description: `${character.name}의 첫 등장 회차는 ${character.firstAppearanceEpisode}화이지만, ${episode.episodeNumber}화 "${episode.title}"에 등장 인물로 등록되어 있습니다.`,
          relatedType: 'character',
          relatedIds: [character.id, episode.id],
        });
      }
    }
  }
}

function checkDeadCharacterAppearance(
  characters: Character[],
  episodes: Episode[],
  conflicts: Conflict[],
): void {
  const deadCharacters = characters.filter((c) => c.currentStatus === 'dead');

  for (const character of deadCharacters) {
    for (const episode of episodes) {
      if (episode.characterIds.includes(character.id)) {
        conflicts.push({
          id: generateId(),
          level: 'warning',
          title: `사망 캐릭터 등장: ${character.name}`,
          description: `현재 상태가 "사망"인 ${character.name}이(가) ${episode.episodeNumber}화 "${episode.title}" 등장 인물에 포함되어 있습니다.`,
          relatedType: 'character',
          relatedIds: [character.id, episode.id],
        });
      }
    }
  }
}
