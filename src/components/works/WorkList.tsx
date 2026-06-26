import { useState } from 'react';
import type { Work } from '../../types/work';
import { Button } from '../common/Button';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { EmptyState } from '../common/EmptyState';
import { WorkForm } from './WorkForm';

type WorkListProps = {
  works: Work[];
  selectedWorkId: string | null;
  onSelect: (id: string) => void;
  onAdd: (data: Omit<Work, 'id' | 'createdAt' | 'updatedAt'>) => void;
  onUpdate: (id: string, data: Omit<Work, 'id' | 'createdAt' | 'updatedAt'>) => void;
  onDelete: (id: string) => void;
};

export function WorkList({
  works,
  selectedWorkId,
  onSelect,
  onAdd,
  onUpdate,
  onDelete,
}: WorkListProps) {
  const [formOpen, setFormOpen] = useState(false);
  const [editingWork, setEditingWork] = useState<Work | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Work | null>(null);
  const [viewingWork, setViewingWork] = useState<Work | null>(null);

  const handleEdit = (work: Work) => {
    setEditingWork(work);
    setFormOpen(true);
  };

  const handleFormClose = () => {
    setFormOpen(false);
    setEditingWork(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-100">작품 관리</h2>
          <p className="mt-1 text-sm text-gray-500">작품을 생성하고 선택하여 설정을 관리하세요.</p>
        </div>
        <Button onClick={() => setFormOpen(true)}>+ 새 작품</Button>
      </div>

      {works.length === 0 ? (
        <EmptyState
          title="등록된 작품이 없습니다"
          description="첫 작품을 추가하고 캐릭터, 회차, 세계관 설정을 관리해보세요."
          action={<Button onClick={() => setFormOpen(true)}>작품 추가</Button>}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {works.map((work) => (
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
              <div className="mt-4 flex flex-wrap gap-2">
                <Button
                  variant={selectedWorkId === work.id ? 'secondary' : 'primary'}
                  className="flex-1 text-xs sm:flex-none"
                  onClick={() => onSelect(work.id)}
                >
                  {selectedWorkId === work.id ? '선택됨' : '선택'}
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
          ))}
        </div>
      )}

      <WorkForm
        isOpen={formOpen}
        onClose={handleFormClose}
        work={editingWork}
        onSubmit={(data) => {
          if (editingWork) {
            onUpdate(editingWork.id, data);
          } else {
            onAdd(data);
          }
          handleFormClose();
        }}
      />

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
