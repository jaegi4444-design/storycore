import { useMemo, useState } from 'react';
import type { Character } from '../../types/character';
import type { Episode } from '../../types/episode';
import type { Work } from '../../types/work';
import type { WorldSetting } from '../../types/worldSetting';
import { buildWritingPrompt } from '../../utils/promptBuilder';
import { Button } from '../common/Button';
import { EmptyState } from '../common/EmptyState';
import { Select } from '../common/Select';
import { Textarea } from '../common/Textarea';

type PromptGeneratorProps = {
  work: Work | null;
  episodes: Episode[];
  characters: Character[];
  worldSettings: WorldSetting[];
};

export function PromptGenerator({
  work,
  episodes,
  characters,
  worldSettings,
}: PromptGeneratorProps) {
  const [selectedEpisodeId, setSelectedEpisodeId] = useState('');
  const [copied, setCopied] = useState(false);

  const selectedEpisode = episodes.find((e) => e.id === selectedEpisodeId);

  const prompt = useMemo(() => {
    if (!work || !selectedEpisode) return '';
    return buildWritingPrompt({
      work,
      episodes,
      characters,
      worldSettings,
      targetEpisode: selectedEpisode,
    });
  }, [work, selectedEpisode, episodes, characters, worldSettings]);

  const handleCopy = async () => {
    if (!prompt) return;
    try {
      await navigator.clipboard.writeText(prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard may be unavailable */
    }
  };

  if (!work) {
    return (
      <EmptyState
        title="작품을 먼저 선택해주세요"
        description="프롬프트를 생성하려면 작품 관리에서 작품을 선택하세요."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">AI 프롬프트 생성</h2>
        <p className="mt-1 text-sm text-gray-500">
          회차를 선택하면 글쓰기용 프롬프트를 자동으로 생성합니다.
        </p>
      </div>

      {episodes.length === 0 ? (
        <EmptyState
          title="등록된 회차가 없습니다"
          description="회차를 먼저 추가한 후 프롬프트를 생성하세요."
        />
      ) : (
        <>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
            <div className="flex-1">
              <Select
                label="회차 선택"
                value={selectedEpisodeId}
                onChange={(e) => setSelectedEpisodeId(e.target.value)}
                placeholder="회차를 선택하세요"
                options={episodes.map((ep) => ({
                  value: ep.id,
                  label: `${ep.episodeNumber}화: ${ep.title}`,
                }))}
              />
            </div>
            <Button
              variant="secondary"
              onClick={handleCopy}
              disabled={!prompt}
              className="shrink-0"
            >
              {copied ? '복사됨!' : '클립보드 복사'}
            </Button>
          </div>

          {prompt ? (
            <Textarea
              label="생성된 프롬프트"
              value={prompt}
              readOnly
              rows={24}
              className="font-mono text-xs leading-relaxed"
            />
          ) : (
            <EmptyState
              title="회차를 선택하세요"
              description="위에서 회차를 선택하면 프롬프트가 생성됩니다."
            />
          )}
        </>
      )}
    </div>
  );
}
