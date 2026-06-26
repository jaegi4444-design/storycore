import { useMemo, useState } from 'react';
import type { Character } from '../../types/character';
import type { Episode } from '../../types/episode';
import type {
  WorldSetting,
  WorldSettingCategory,
  WorldSettingInput,
} from '../../types/worldSetting';
import { WORLD_SETTING_CATEGORY_LABELS } from '../../types/worldSetting';
import { Button } from '../common/Button';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { EmptyState } from '../common/EmptyState';
import { WorldSettingDetail } from './WorldSettingDetail';
import { WorldSettingForm } from './WorldSettingForm';

type WorldSettingListProps = {
  workId: string | null;
  settings: WorldSetting[];
  characters: Character[];
  episodes: Episode[];
  onAdd: (data: WorldSettingInput) => void;
  onUpdate: (id: string, data: WorldSettingInput) => void;
  onDelete: (id: string) => void;
};

export function WorldSettingList({
  workId,
  settings,
  characters,
  episodes,
  onAdd,
  onUpdate,
  onDelete,
}: WorldSettingListProps) {
  const [formOpen, setFormOpen] = useState(false);
  const [editingSetting, setEditingSetting] = useState<WorldSetting | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<WorldSetting | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<WorldSettingCategory | 'all'>('all');

  const filteredSettings = useMemo(() => {
    if (categoryFilter === 'all') return settings;
    return settings.filter((s) => s.category === categoryFilter);
  }, [settings, categoryFilter]);

  const selectedSetting = settings.find((s) => s.id === selectedId);

  if (!workId) {
    return (
      <EmptyState
        title="작품을 먼저 선택해주세요"
        description="세계관 설정을 관리하려면 작품 관리에서 작품을 선택하세요."
      />
    );
  }

  const categories = (
    Object.keys(WORLD_SETTING_CATEGORY_LABELS) as WorldSettingCategory[]
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-100">세계관 설정</h2>
          <p className="mt-1 text-sm text-gray-500">총 {settings.length}개 설정</p>
        </div>
        <Button
          onClick={() => {
            setEditingSetting(null);
            setFormOpen(true);
          }}
        >
          + 새 설정
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        <FilterChip
          active={categoryFilter === 'all'}
          onClick={() => setCategoryFilter('all')}
          label="전체"
        />
        {categories.map((cat) => (
          <FilterChip
            key={cat}
            active={categoryFilter === cat}
            onClick={() => setCategoryFilter(cat)}
            label={WORLD_SETTING_CATEGORY_LABELS[cat]}
          />
        ))}
      </div>

      {settings.length === 0 ? (
        <EmptyState
          title="등록된 세계관 설정이 없습니다"
          description="용어, 조직, 지역 등 세계관 요소를 추가해보세요."
          action={<Button onClick={() => setFormOpen(true)}>설정 추가</Button>}
        />
      ) : filteredSettings.length === 0 ? (
        <EmptyState
          title="해당 카테고리에 설정이 없습니다"
          description="다른 카테고리를 선택하거나 새 설정을 추가하세요."
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="grid gap-3 sm:grid-cols-2 lg:col-span-2 lg:grid-cols-1">
            {filteredSettings.map((setting) => (
              <div
                key={setting.id}
                className={`cursor-pointer rounded-xl border p-4 transition-all hover:border-accent/40 ${
                  selectedId === setting.id
                    ? 'border-accent bg-accent/5 ring-1 ring-accent/30'
                    : 'border-surface-border bg-surface-raised'
                }`}
                onClick={() => setSelectedId(setting.id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <span className="text-xs font-medium text-accent-hover">
                      {WORLD_SETTING_CATEGORY_LABELS[setting.category]}
                    </span>
                    <h3 className="truncate font-semibold text-gray-100">
                      {setting.name}
                    </h3>
                    <p className="mt-1 line-clamp-2 text-sm text-gray-500">
                      {setting.description}
                    </p>
                  </div>
                </div>
                <div
                  className="mt-3 flex gap-2"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() => {
                      setEditingSetting(setting);
                      setFormOpen(true);
                    }}
                    className="rounded-lg px-3 py-1 text-xs text-gray-400 hover:bg-surface-overlay hover:text-gray-200"
                  >
                    수정
                  </button>
                  <button
                    onClick={() => setDeleteTarget(setting)}
                    className="rounded-lg px-3 py-1 text-xs text-red-400 hover:bg-red-500/10"
                  >
                    삭제
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="lg:col-span-3">
            {selectedSetting ? (
              <div className="rounded-xl border border-surface-border bg-surface-raised p-6">
                <WorldSettingDetail
                  setting={selectedSetting}
                  characters={characters}
                  episodes={episodes}
                />
              </div>
            ) : (
              <EmptyState
                title="설정을 선택하세요"
                description="목록에서 세계관 설정을 클릭하면 상세 정보를 볼 수 있습니다."
              />
            )}
          </div>
        </div>
      )}

      <WorldSettingForm
        isOpen={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditingSetting(null);
        }}
        workId={workId}
        characters={characters}
        episodes={episodes}
        setting={editingSetting}
        onSubmit={(data) => {
          if (editingSetting) {
            onUpdate(editingSetting.id, data);
          } else {
            onAdd(data);
          }
          setFormOpen(false);
          setEditingSetting(null);
        }}
      />

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && onDelete(deleteTarget.id)}
        title="세계관 설정 삭제"
        message={`"${deleteTarget?.name}" 설정을 삭제하시겠습니까?`}
      />
    </div>
  );
}

function FilterChip({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
        active
          ? 'bg-accent/20 text-accent-hover'
          : 'bg-surface-overlay text-gray-400 hover:text-gray-200'
      }`}
    >
      {label}
    </button>
  );
}
