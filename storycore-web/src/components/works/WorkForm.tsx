import { useEffect, useState } from 'react';
import type { Work } from '../../types/work';
import { workCategoryError } from '../../types/work';
import { Input } from '../common/Input';
import { Modal, ModalFooter } from '../common/Modal';
import { Textarea } from '../common/Textarea';
import { WorkCategoryEditor } from '../common/WorkCategoryEditor';

type WorkFormData = Omit<Work, 'id' | 'createdAt' | 'updatedAt'>;

type WorkFormProps = {
  isOpen: boolean;
  onClose: () => void;
  work?: Work | null;
  onSubmit: (data: WorkFormData) => void;
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

export function WorkForm({ isOpen, onClose, work, onSubmit }: WorkFormProps) {
  const [form, setForm] = useState<WorkFormData>(emptyForm);
  const [error, setError] = useState<string | null>(null);

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
  }, [work, isOpen]);

  const handleSubmit = () => {
    if (!form.title.trim()) return;
    const categoryError = workCategoryError(form);
    if (categoryError) {
      setError(categoryError);
      return;
    }
    onSubmit(form);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={work ? '작품 수정' : '새 작품'} size="xl">
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

        <div className="border-t border-surface-border pt-4">
          <h3 className="mb-1 text-sm font-semibold text-gray-200">작품 카테고리 (필수)</h3>
          <p className="mb-4 text-xs text-gray-500">
            캐릭터 등록 시 등급·직업·소속을 선택할 수 있도록 작품별 목록을 설정합니다.
          </p>
          <div className="space-y-4">
            <WorkCategoryEditor
              label="등급"
              description="예: D급, A급, S급"
              options={form.ranks}
              onChange={(ranks) => setForm({ ...form, ranks })}
              placeholder="등급 이름"
            />
            <WorkCategoryEditor
              label="직업"
              description="예: 각성자, 팀장, 검사"
              options={form.jobs}
              onChange={(jobs) => setForm({ ...form, jobs })}
              placeholder="직업 이름"
            />
            <WorkCategoryEditor
              label="소속"
              description="예: 국가 각성자 서울팀, 한빙그룹"
              options={form.affiliations}
              onChange={(affiliations) => setForm({ ...form, affiliations })}
              placeholder="소속 이름"
            />
          </div>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}
      </div>
      <ModalFooter onCancel={onClose} onConfirm={handleSubmit} confirmLabel={work ? '수정' : '추가'} />
    </Modal>
  );
}
