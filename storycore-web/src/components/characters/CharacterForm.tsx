import { useEffect, useState } from 'react';
import type { Character, CharacterInput, CharacterStatus, CharacterSubmitPayload } from '../../types/character';
import { CHARACTER_STATUS_LABELS, characterCategoryError } from '../../types/character';
import type { Work } from '../../types/work';
import { ImageUpload } from '../common/ImageUpload';
import { Input } from '../common/Input';
import { Modal, ModalFooter } from '../common/Modal';
import { Select } from '../common/Select';
import { Textarea } from '../common/Textarea';

type CharacterFormProps = {
  isOpen: boolean;
  onClose: () => void;
  work: Work;
  character?: Character | null;
  onSubmit: (payload: CharacterSubmitPayload) => void | Promise<void>;
};

const statusOptions = (Object.keys(CHARACTER_STATUS_LABELS) as CharacterStatus[]).map(
  (key) => ({ value: key, label: CHARACTER_STATUS_LABELS[key] }),
);

const emptyForm = (workId: string): CharacterInput => ({
  workId,
  name: '',
  alias: '',
  age: '',
  gender: '',
  affiliation: '',
  affiliationDetail: '',
  role: '',
  rank: '',
  job: '',
  abilities: '',
  personality: '',
  appearance: '',
  firstAppearanceEpisode: null,
  currentStatus: 'active',
  publicInfo: '',
  secretInfo: '',
  memo: '',
  imageUrl: null,
});

export function CharacterForm({
  isOpen,
  onClose,
  work,
  character,
  onSubmit,
}: CharacterFormProps) {
  const [form, setForm] = useState<CharacterInput>(emptyForm(work.id));
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [removeImage, setRemoveImage] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (character) {
      const { id: _id, createdAt: _c, updatedAt: _u, ...rest } = character;
      setForm(rest);
    } else {
      setForm(emptyForm(work.id));
    }
    setImageFile(null);
    setRemoveImage(false);
    setError(null);
  }, [character, isOpen, work.id]);

  const handleImageChange = (file: File | null, remove: boolean) => {
    setImageFile(file);
    setRemoveImage(remove);
  };

  const handleSubmit = async () => {
    if (!form.name.trim() || submitting) return;
    const categoryError = characterCategoryError(form);
    if (categoryError) {
      setError(categoryError);
      return;
    }
    setSubmitting(true);
    try {
      await onSubmit({
        data: form,
        imageFile,
        removeImage,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={character ? '캐릭터 수정' : '새 캐릭터'}
      size="xl"
    >
      <ImageUpload
        currentImageUrl={character?.imageUrl}
        onChange={handleImageChange}
      />

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Input
          label="이름"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <Input
          label="별칭"
          value={form.alias}
          onChange={(e) => setForm({ ...form, alias: e.target.value })}
        />
        <Input
          label="나이"
          value={form.age}
          onChange={(e) => setForm({ ...form, age: e.target.value })}
        />
        <Input
          label="성별"
          value={form.gender}
          onChange={(e) => setForm({ ...form, gender: e.target.value })}
        />
      </div>

      <div className="mt-4 rounded-lg border border-surface-border bg-surface-overlay/30 p-4">
        <h4 className="mb-1 text-sm font-semibold text-gray-200">등급 · 직업 · 소속</h4>
        <p className="mb-4 text-xs text-gray-500">직접 텍스트로 입력합니다.</p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Input
            label="등급"
            value={form.rank}
            onChange={(e) => setForm({ ...form, rank: e.target.value })}
            placeholder="예: D급, S급"
            required
          />
          <Input
            label="직업"
            value={form.job}
            onChange={(e) => setForm({ ...form, job: e.target.value })}
            placeholder="예: 각성자, 팀장"
            required
          />
          <Input
            label="소속"
            value={form.affiliation}
            onChange={(e) => setForm({ ...form, affiliation: e.target.value })}
            placeholder="예: 국가 각성자 서울팀"
            required
          />
        </div>
        <div className="mt-4">
          <Textarea
            label="소속 상세"
            value={form.affiliationDetail}
            onChange={(e) => setForm({ ...form, affiliationDetail: e.target.value })}
            placeholder="예: 서울팀장 · 현장 지휘관"
            rows={2}
          />
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Input
          label="역할"
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
        />
        <Input
          label="첫 등장 회차"
          type="number"
          min={1}
          value={form.firstAppearanceEpisode ?? ''}
          onChange={(e) =>
            setForm({
              ...form,
              firstAppearanceEpisode: e.target.value ? Number(e.target.value) : null,
            })
          }
        />
        <Select
          label="현재 상태"
          value={form.currentStatus}
          onChange={(e) =>
            setForm({ ...form, currentStatus: e.target.value as CharacterStatus })
          }
          options={statusOptions}
        />
      </div>
      <div className="mt-4 space-y-4">
        <Textarea
          label="능력"
          value={form.abilities}
          onChange={(e) => setForm({ ...form, abilities: e.target.value })}
        />
        <Textarea
          label="성격"
          value={form.personality}
          onChange={(e) => setForm({ ...form, personality: e.target.value })}
        />
        <Textarea
          label="외형"
          value={form.appearance}
          onChange={(e) => setForm({ ...form, appearance: e.target.value })}
        />
        <Textarea
          label="독자 공개 설정"
          value={form.publicInfo}
          onChange={(e) => setForm({ ...form, publicInfo: e.target.value })}
        />
        <Textarea
          label="작가 비밀 설정"
          value={form.secretInfo}
          onChange={(e) => setForm({ ...form, secretInfo: e.target.value })}
        />
        <Textarea
          label="메모"
          value={form.memo}
          onChange={(e) => setForm({ ...form, memo: e.target.value })}
          rows={2}
        />
      </div>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      <ModalFooter
        onCancel={onClose}
        onConfirm={handleSubmit}
        confirmLabel={character ? '수정' : '추가'}
        isLoading={submitting}
      />
    </Modal>
  );
}
