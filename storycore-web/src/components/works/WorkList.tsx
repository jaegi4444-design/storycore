import { useMemo, useState } from 'react';
import type { Work } from '../../types/work';
import { hasRequiredWorkCategories, MAX_WORKS_PER_USER } from '../../types/work';
import { Button } from '../common/Button';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { EmptyState } from '../common/EmptyState';
import { Modal } from '../common/Modal';
import { WorkCategorySection } from './WorkCategorySection';
import { WorkForm } from './WorkForm';

type WorkListProps = {
  works: Work[];
  selectedWorkId: string | null;
  onSelect: (id: string) => void;
  onAdd: (data: Omit<Work, 'id' | 'createdAt' | 'updatedAt'>) => void;
  onUpdate: (id: string, data: Omit<Work, 'id' | 'createdAt' | 'updatedAt'>) => void;
  onDelete: (id: string) => void;
};

function toWorkInput(work: Work): Omit<Work, 'id' | 'createdAt' | 'updatedAt'> {
  return {
    title: work.title,
    genre: work.genre,
    oneLineSummary: work.oneLineSummary,
    synopsis: work.synopsis,
    authorNote: work.authorNote,
    ranks: work.ranks,
    jobs: work.jobs,
    affiliations: work.affiliations,
  };
}

export function WorkList({
  works,
  selectedWorkId,
  onSelect,
  onAdd,
  onUpdate,
  onDelete,
}: WorkListProps) {
  const [formOpen, setFormOpen] = useState(false);
  const [formInitialTab, setFormInitialTab] = useState<'info' | 'categories'>('info');
  const [editingWork, setEditingWork] = useState<Work | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Work | null>(null);
  const [viewingWork, setViewingWork] = useState<Work | null>(null);
  const [limitWarningOpen, setLimitWarningOpen] = useState(false);

  const categoryWork = useMemo(() => {
    if (selectedWorkId) {
      return works.find((w) => w.id === selectedWorkId) ?? null;
    }
    return works[0] ?? null;
  }, [works, selectedWorkId]);

  const handleEdit = (work: Work, tab: 'info' | 'categories' = 'info') => {
    setEditingWork(work);
    setFormInitialTab(tab);
    setFormOpen(true);
  };

  const handleFormClose = () => {
    setFormOpen(false);
    setEditingWork(null);
    setFormInitialTab('info');
  };

  const handleAddClick = () => {
    if (works.length >= MAX_WORKS_PER_USER) {
      setLimitWarningOpen(true);
      return;
    }
    setEditingWork(null);
    setFormInitialTab('info');
    setFormOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-100">작품 관리</h2>
          <p className="mt-1 text-sm text-gray-500">
            현재 {works.length}/{MAX_WORKS_PER_USER}개 작품 · 등급·직업·소속을 각각 등록합니다.
          </p>
        </div>
        <Button onClick={handleAddClick}>+ 새 작품</Button>
      </div>

      {works.length === 0 ? (
        <EmptyState
          title="등록된 작품이 없습니다"
          description="첫 작품을 추가하고 등급·직업·소속 카테고리를 설정해보세요."
          action={<Button onClick={handleAddClick}>작품 추가</Button>}
        />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {works.map((work) => {
              const categoriesReady = hasRequiredWorkCategories(work);
              return (
                <div
                  key={work.id}
                  className={`group rounded-xl border bg-surface-raised p-5 transition-all hover:border-accent/40 ${
                    selectedWorkId === work.id
                      ? 'border-accent ring-1 ring-accent/30'
                      : 'border-surface-border'
                  }`}
                >
                  <div className="mb-3 flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <h3 className="truncate font-semibold text-gray-100">{work.title}</h3>
                      <span className="mt-1 inline-block rounded-full bg-surface-overlay px-2 py-0.5 text-xs text-gray-400">
                        {work.genre}
                      </span>
                    </div>
                    {selectedWorkId === work.id && (
                      <span className="shrink-0 rounded-full bg-accent/20 px-2 py-0.5 text-xs font-medium text-accent-hover">
                        선택됨
                      </span>
                    )}
                  </div>
                  <p className="line-clamp-2 text-sm text-gray-400">{work.oneLineSummary}</p>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    <CategoryBadge label="등급" count={work.ranks.length} tone="violet" />
                    <CategoryBadge label="직업" count={work.jobs.length} tone="sky" />
                    <CategoryBadge label="소속" count={work.affiliations.length} tone="emerald" />
                  </div>
                  {!categoriesReady && (
                    <p className="mt-2 text-xs text-amber-400">등급·직업·소속 등록 필요</p>
                  )}
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Button
                      variant={selectedWorkId === work.id ? 'secondary' : 'primary'}
                      className="flex-1 text-xs sm:flex-none"
                      onClick={() => onSelect(work.id)}
                    >
                      {selectedWorkId === work.id ? '선택됨' : '선택'}
                    </Button>
                    <Button
                      variant="ghost"
                      className="text-xs text-accent-hover"
                      onClick={() => handleEdit(work, 'categories')}
                    >
                      카테고리
                    </Button>
                    <Button variant="ghost" className="text-xs" onClick={() => setViewingWork(work)}>
                      상세
                    </Button>
                    <Button variant="ghost" className="text-xs" onClick={() => handleEdit(work)}>
                      수정
                    </Button>
                    <Button variant="ghost" className="text-xs text-red-400" onClick={() => setDeleteTarget(work)}>
                      삭제
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>

          {categoryWork && (
            <WorkCategorySection
              work={categoryWork}
              onSave={async (categories) => {
                onUpdate(categoryWork.id, {
                  ...toWorkInput(categoryWork),
                  ...categories,
                });
              }}
            />
          )}

          {!selectedWorkId && works.length > 0 && (
            <p className="text-center text-xs text-gray-500">
              작품을 선택하면 해당 작품의 카테고리를 관리할 수 있습니다. (현재: {categoryWork?.title})
            </p>
          )}
        </>
      )}

      <WorkForm
        isOpen={formOpen}
        onClose={handleFormClose}
        work={editingWork}
        initialTab={formInitialTab}
        onSubmit={(data) => {
          if (editingWork) {
            onUpdate(editingWork.id, data);
          } else {
            onAdd(data);
          }
          handleFormClose();
        }}
      />

      <Modal isOpen={limitWarningOpen} onClose={() => setLimitWarningOpen(false)} title="작품 개수 제한" size="md">
        <p className="text-sm text-gray-400">
          현재는 작품을 1개만 등록할 수 있습니다. 여러 작품 관리 기능은 추후 업데이트에서 지원할 예정입니다.
        </p>
        <div className="mt-6 flex justify-end">
          <Button variant="secondary" onClick={() => setLimitWarningOpen(false)}>
            확인
          </Button>
        </div>
      </Modal>

      {viewingWork && (
        <div className="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
          <div className="absolute inset-0 bg-black/60" onClick={() => setViewingWork(null)} />
          <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-surface-border bg-surface-raised p-6 shadow-2xl">
            <h3 className="text-xl font-semibold text-gray-100">{viewingWork.title}</h3>
            <div className="mt-4 space-y-4 text-sm">
              <DetailRow label="장르" value={viewingWork.genre} />
              <DetailRow label="한 줄 소개" value={viewingWork.oneLineSummary} />
              <DetailRow label="전체 줄거리" value={viewingWork.synopsis} multiline />
              <DetailRow label="작가 메모" value={viewingWork.authorNote} multiline />
              <CategoryRow label="등급" items={viewingWork.ranks.map((r) => r.name)} />
              <CategoryRow label="직업" items={viewingWork.jobs.map((j) => j.name)} />
              <CategoryRow label="소속" items={viewingWork.affiliations.map((a) => a.name)} />
            </div>
            <div className="mt-6 flex justify-end">
              <Button variant="secondary" onClick={() => setViewingWork(null)}>
                닫기
              </Button>
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && onDelete(deleteTarget.id)}
        title="작품 삭제"
        message={`"${deleteTarget?.title}" 작품을 삭제하시겠습니까? 관련 캐릭터, 회차, 세계관 데이터는 유지되지만 더 이상 이 작품에 연결되지 않을 수 있습니다.`}
      />
    </div>
  );
}

function CategoryBadge({
  label,
  count,
  tone,
}: {
  label: string;
  count: number;
  tone: 'violet' | 'sky' | 'emerald';
}) {
  const toneClass = {
    violet: count > 0 ? 'bg-violet-500/15 text-violet-300' : 'bg-surface-overlay text-gray-500',
    sky: count > 0 ? 'bg-sky-500/15 text-sky-300' : 'bg-surface-overlay text-gray-500',
    emerald: count > 0 ? 'bg-emerald-500/15 text-emerald-300' : 'bg-surface-overlay text-gray-500',
  }[tone];

  return (
    <span className={`rounded-full px-2 py-0.5 ${toneClass}`}>
      {label} {count}
    </span>
  );
}

function DetailRow({
  label,
  value,
  multiline,
}: {
  label: string;
  value: string;
  multiline?: boolean;
}) {
  return (
    <div>
      <dt className="font-medium text-gray-400">{label}</dt>
      <dd className={`mt-1 text-gray-200 ${multiline ? 'whitespace-pre-wrap' : ''}`}>
        {value || '(없음)'}
      </dd>
    </div>
  );
}

function CategoryRow({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <dt className="font-medium text-gray-400">{label}</dt>
      <dd className="mt-2 flex flex-wrap gap-2">
        {items.length === 0 ? (
          <span className="text-gray-500">(없음)</span>
        ) : (
          items.map((item) => (
            <span key={item} className="rounded-full bg-surface-overlay px-2 py-0.5 text-xs text-gray-300">
              {item}
            </span>
          ))
        )}
      </dd>
    </div>
  );
}
