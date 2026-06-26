import { useEffect, useState, type ReactNode } from 'react';
import type { Work } from '../../types/work';
import { workCategoryError } from '../../types/work';
import { Input } from '../common/Input';
import { Modal, ModalFooter } from '../common/Modal';
import { Textarea } from '../common/Textarea';
import { WorkCategorySection } from './WorkCategorySection';

type WorkFormData = Omit<Work, 'id' | 'createdAt' | 'updatedAt'>;

type WorkFormProps = {
  isOpen: boolean;
  onClose: () => void;
  work?: Work | null;
  onSubmit: (data: WorkFormData) => void;
  initialTab?: 'info' | 'categories';
};

const emptyForm: WorkFormData = {
  title: '',
  genre: '',
  oneLineSummary: '',
  synopsis: '',
  authorNote: '',
  ranks: [],
  jobs: [],
  affiliations: [],
};

type FormTab = 'info' | 'categories';

export function WorkForm({ isOpen, onClose, work, onSubmit, initialTab = 'info' }: WorkFormProps) {
  const [form, setForm] = useState<WorkFormData>(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<FormTab>(initialTab);

  useEffect(() => {
    if (work) {
      setForm({
        title: work.title,
        genre: work.genre,
        oneLineSummary: work.oneLineSummary,
        synopsis: work.synopsis,
        authorNote: work.authorNote,
        ranks: work.ranks,
        jobs: work.jobs,
        affiliations: work.affiliations,
      });
    } else {
      setForm(emptyForm);
    }
    setError(null);
    setTab(initialTab);
  }, [work, isOpen, initialTab]);

  const handleSubmit = () => {
    if (!form.title.trim()) {
      setError('작품명을 입력해주세요.');
      setTab('info');
      return;
    }
    const categoryError = workCategoryError(form);
    if (categoryError) {
      setError(categoryError);
      setTab('categories');
      return;
    }
    onSubmit(form);
  };

  const draftWork: Work = {
    id: work?.id ?? 'draft',
    ...form,
    createdAt: work?.createdAt ?? '',
    updatedAt: work?.updatedAt ?? '',
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={work ? '작품 수정' : '새 작품'} size="xl">
      <div className="mb-4 flex gap-1 rounded-lg border border-surface-border bg-surface-overlay/50 p-1">
        <TabButton active={tab === 'info'} onClick={() => setTab('info')}>
          기본 정보
        </TabButton>
        <TabButton active={tab === 'categories'} onClick={() => setTab('categories')}>
          등급 · 직업 · 소속
          {(form.ranks.length === 0 || form.jobs.length === 0 || form.affiliations.length === 0) && (
            <span className="ml-1.5 inline-block h-1.5 w-1.5 rounded-full bg-amber-400" />
          )}
        </TabButton>
      </div>

      {tab === 'info' ? (
        <div className="space-y-4">
          <Input
            label="작품명"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="작품 제목"
            required
          />
          <Input
            label="장르"
            value={form.genre}
            onChange={(e) => setForm({ ...form, genre: e.target.value })}
            placeholder="예: 현대판타지"
          />
          <Input
            label="한 줄 소개"
            value={form.oneLineSummary}
            onChange={(e) => setForm({ ...form, oneLineSummary: e.target.value })}
            placeholder="작품을 한 줄로 소개"
          />
          <Textarea
            label="전체 줄거리"
            value={form.synopsis}
            onChange={(e) => setForm({ ...form, synopsis: e.target.value })}
            rows={5}
          />
          <Textarea
            label="작가 메모"
            value={form.authorNote}
            onChange={(e) => setForm({ ...form, authorNote: e.target.value })}
            rows={3}
          />
          <p className="text-xs text-gray-500">
            다음 단계: <button type="button" className="text-accent-hover underline" onClick={() => setTab('categories')}>등급 · 직업 · 소속</button> 탭에서 카테고리를 등록하세요.
          </p>
        </div>
      ) : (
        <WorkCategorySection
          compact
          work={draftWork}
          onSave={async (categories) => {
            setForm((prev) => ({ ...prev, ...categories }));
            setError(null);
          }}
        />
      )}

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      <ModalFooter onCancel={onClose} onConfirm={handleSubmit} confirmLabel={work ? '수정' : '추가'} />
    </Modal>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
        active
          ? 'bg-accent text-white'
          : 'text-gray-400 hover:bg-surface-border hover:text-gray-200'
      }`}
    >
      {children}
    </button>
  );
}
