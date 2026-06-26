import { useState } from 'react';
import type { Character } from '../../types/character';
import type { Episode, EpisodeInput } from '../../types/episode';
import { Button } from '../common/Button';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { EmptyState } from '../common/EmptyState';
import { EpisodeDetail } from './EpisodeDetail';
import { EpisodeForm } from './EpisodeForm';

type EpisodeListProps = {
  workId: string | null;
  episodes: Episode[];
  characters: Character[];
  onAdd: (data: EpisodeInput) => void;
  onUpdate: (id: string, data: EpisodeInput) => void;
  onDelete: (id: string) => void;
};

export function EpisodeList({
  workId,
  episodes,
  characters,
  onAdd,
  onUpdate,
  onDelete,
}: EpisodeListProps) {
  const [formOpen, setFormOpen] = useState(false);
  const [editingEpisode, setEditingEpisode] = useState<Episode | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Episode | null>(null);

  const selectedEpisode = episodes.find((e) => e.id === selectedId);

  if (!workId) {
    return (
      <EmptyState
        title="작품을 먼저 선택해주세요"
        description="회차를 관리하려면 작품 관리에서 작품을 선택하세요."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-100">회차 관리</h2>
          <p className="mt-1 text-sm text-gray-500">총 {episodes.length}화</p>
        </div>
        <Button
          onClick={() => {
            setEditingEpisode(null);
            setFormOpen(true);
          }}
        >
          + 새 회차
        </Button>
      </div>

      {episodes.length === 0 ? (
        <EmptyState
          title="등록된 회차가 없습니다"
          description="작품의 회차를 추가해보세요."
          action={<Button onClick={() => setFormOpen(true)}>회차 추가</Button>}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="space-y-2 lg:col-span-2">
            {episodes.map((episode) => (
              <div
                key={episode.id}
                className={`cursor-pointer rounded-xl border p-4 transition-all hover:border-accent/40 ${
                  selectedId === episode.id
                    ? 'border-accent bg-accent/5 ring-1 ring-accent/30'
                    : 'border-surface-border bg-surface-raised'
                }`}
                onClick={() => setSelectedId(episode.id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <span className="text-xs font-medium text-accent-hover">
                      {episode.episodeNumber}화
                    </span>
                    <h3 className="truncate font-semibold text-gray-100">
                      {episode.title}
                    </h3>
                    <p className="mt-1 line-clamp-2 text-sm text-gray-500">
                      {episode.summary}
                    </p>
                  </div>
                </div>
                <div
                  className="mt-3 flex gap-2"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() => {
                      setEditingEpisode(episode);
                      setFormOpen(true);
                    }}
                    className="rounded-lg px-3 py-1 text-xs text-gray-400 hover:bg-surface-overlay hover:text-gray-200"
                  >
                    수정
                  </button>
                  <button
                    onClick={() => setDeleteTarget(episode)}
                    className="rounded-lg px-3 py-1 text-xs text-red-400 hover:bg-red-500/10"
                  >
                    삭제
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="lg:col-span-3">
            {selectedEpisode ? (
              <div className="rounded-xl border border-surface-border bg-surface-raised p-6">
                <EpisodeDetail episode={selectedEpisode} characters={characters} />
              </div>
            ) : (
              <EmptyState
                title="회차를 선택하세요"
                description="목록에서 회차를 클릭하면 상세 정보를 볼 수 있습니다."
              />
            )}
          </div>
        </div>
      )}

      <EpisodeForm
        isOpen={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditingEpisode(null);
        }}
        workId={workId}
        characters={characters}
        episode={editingEpisode}
        onSubmit={(data) => {
          if (editingEpisode) {
            onUpdate(editingEpisode.id, data);
          } else {
            onAdd(data);
          }
          setFormOpen(false);
          setEditingEpisode(null);
        }}
      />

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && onDelete(deleteTarget.id)}
        title="회차 삭제"
        message={`${deleteTarget?.episodeNumber}화 "${deleteTarget?.title}"을(를) 삭제하시겠습니까?`}
      />
    </div>
  );
}
