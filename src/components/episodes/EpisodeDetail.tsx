import type { ReactNode } from 'react';
import type { Character } from '../../types/character';
import type { Episode } from '../../types/episode';

type EpisodeDetailProps = {
  episode: Episode;
  characters: Character[];
};

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-surface-border bg-surface-overlay/50 p-4">
      <h4 className="mb-3 text-sm font-semibold text-accent-hover">{title}</h4>
      {children}
    </section>
  );
}

export function EpisodeDetail({ episode, characters }: EpisodeDetailProps) {
  const episodeCharacters = characters.filter((c) =>
    episode.characterIds.includes(c.id),
  );

  return (
    <div className="space-y-4">
      <div>
        <span className="text-sm text-gray-500">{episode.episodeNumber}화</span>
        <h3 className="text-2xl font-semibold text-gray-100">{episode.title}</h3>
      </div>

      <Section title="요약">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {episode.summary || '(없음)'}
        </p>
      </Section>

      <Section title="등장 인물">
        {episodeCharacters.length === 0 ? (
          <p className="text-sm text-gray-400">(없음)</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {episodeCharacters.map((c) => (
              <span
                key={c.id}
                className="rounded-full bg-surface-border px-3 py-1 text-sm text-gray-200"
              >
                {c.name}
              </span>
            ))}
          </div>
        )}
      </Section>

      <Section title="등장 장소">
        <p className="text-sm text-gray-200">
          {episode.locations.length > 0 ? episode.locations.join(', ') : '(없음)'}
        </p>
      </Section>

      <Section title="새로 공개된 설정">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {episode.revealedSettings || '(없음)'}
        </p>
      </Section>

      <Section title="떡밥">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {episode.foreshadows || '(없음)'}
        </p>
      </Section>

      <Section title="회수한 떡밥">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {episode.resolvedForeshadows || '(없음)'}
        </p>
      </Section>

      <Section title="본문 초안">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {episode.draft || '(없음)'}
        </p>
      </Section>

      <Section title="작가 메모">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {episode.authorNote || '(없음)'}
        </p>
      </Section>
    </div>
  );
}
