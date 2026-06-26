import { useEffect, useState } from 'react';
import type { Work } from '../../types/work';
import { Input } from '../common/Input';
import { Modal, ModalFooter } from '../common/Modal';
import { Textarea } from '../common/Textarea';

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
};

export function WorkForm({ isOpen, onClose, work, onSubmit }: WorkFormProps) {
  const [form, setForm] = useState<WorkFormData>(emptyForm);

  useEffect(() => {
    if (work) {
      setForm({
        title: work.title,
        genre: work.genre,
        oneLineSummary: work.oneLineSummary,
        synopsis: work.synopsis,
        authorNote: work.authorNote,
      });
    } else {
      setForm(emptyForm);
    }
  }, [work, isOpen]);

  const handleSubmit = () => {
    if (!form.title.trim()) return;
    onSubmit(form);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={work ? '작품 수정' : '새 작품'} size="lg">
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
      </div>
      <ModalFooter onCancel={onClose} onConfirm={handleSubmit} confirmLabel={work ? '수정' : '추가'} />
    </Modal>
  );
}
