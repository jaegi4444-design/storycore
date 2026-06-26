import { useEffect, useState } from 'react';
import type { Character, CharacterInput, CharacterStatus } from '../../types/character';
import { CHARACTER_STATUS_LABELS } from '../../types/character';
import { Input } from '../common/Input';
import { Modal, ModalFooter } from '../common/Modal';
import { Select } from '../common/Select';
import { Textarea } from '../common/Textarea';

type CharacterFormProps = {
  isOpen: boolean;
  onClose: () => void;
  workId: string;
  character?: Character | null;
  onSubmit: (data: CharacterInput) => void;
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
  role: '',
  rankOrJob: '',
  abilities: '',
  personality: '',
  appearance: '',
  firstAppearanceEpisode: null,
  currentStatus: 'active',
  publicInfo: '',
  secretInfo: '',
  memo: '',
});

export function CharacterForm({
  isOpen,
  onClose,
  workId,
  character,
  onSubmit,
}: CharacterFormProps) {
  const [form, setForm] = useState<CharacterInput>(emptyForm(workId));

  useEffect(() => {
    if (character) {
      const { id: _id, createdAt: _c, updatedAt: _u, ...rest } = character;
      setForm(rest);
    } else {
      setForm(emptyForm(workId));
    }
  }, [character, isOpen, workId]);

  const handleSubmit = () => {
    if (!form.name.trim()) return;
    onSubmit(form);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={character ? '캐릭터 수정' : '새 캐릭터'}
      size="xl"
    >
      <div className="grid gap-4 sm:grid-cols-2">
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
        <Input
          label="소속"
          value={form.affiliation}
          onChange={(e) => setForm({ ...form, affiliation: e.target.value })}
        />
        <Input
          label="역할"
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
        />
        <Input
          label="등급/직업"
          value={form.rankOrJob}
          onChange={(e) => setForm({ ...form, rankOrJob: e.target.value })}
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
      <ModalFooter
        onCancel={onClose}
        onConfirm={handleSubmit}
        confirmLabel={character ? '수정' : '추가'}
      />
    </Modal>
  );
}
