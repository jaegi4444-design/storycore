import type { ReactNode } from 'react';
import type { Character } from '../../types/character';
import type { Episode } from '../../types/episode';
import type { WorldSetting } from '../../types/worldSetting';
import { WORLD_SETTING_CATEGORY_LABELS } from '../../types/worldSetting';

type WorldSettingDetailProps = {
  setting: WorldSetting;
  characters: Character[];
  episodes: Episode[];
};

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-surface-border bg-surface-overlay/50 p-4">
      <h4 className="mb-3 text-sm font-semibold text-accent-hover">{title}</h4>
      {children}
    </section>
  );
}

export function WorldSettingDetail({
  setting,
  characters,
  episodes,
}: WorldSettingDetailProps) {
  const relatedCharacters = characters.filter((c) =>
    setting.relatedCharacterIds.includes(c.id),
  );
  const relatedEpisodes = episodes.filter((e) =>
    setting.relatedEpisodeIds.includes(e.id),
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h3 className="text-2xl font-semibold text-gray-100">{setting.name}</h3>
        <span className="rounded-full bg-accent/20 px-3 py-1 text-xs font-medium text-accent-hover">
          {WORLD_SETTING_CATEGORY_LABELS[setting.category]}
        </span>
      </div>

      <Section title="설명">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {setting.description || '(없음)'}
        </p>
      </Section>

      <Section title="관련 인물">
        {relatedCharacters.length === 0 ? (
          <p className="text-sm text-gray-400">(없음)</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {relatedCharacters.map((c) => (
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

      <Section title="관련 회차">
        {relatedEpisodes.length === 0 ? (
          <p className="text-sm text-gray-400">(없음)</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {relatedEpisodes.map((e) => (
              <span
                key={e.id}
                className="rounded-full bg-surface-border px-3 py-1 text-sm text-gray-200"
              >
                {e.episodeNumber}화: {e.title}
              </span>
            ))}
          </div>
        )}
      </Section>

      <Section title="메모">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {setting.memo || '(없음)'}
        </p>
      </Section>
    </div>
  );
}
