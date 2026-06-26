import { useEffect, useState } from 'react';
import type { Character } from '../../types/character';
import type { Episode } from '../../types/episode';
import type { WorldSetting, WorldSettingCategory, WorldSettingInput } from '../../types/worldSetting';
import { WORLD_SETTING_CATEGORY_LABELS } from '../../types/worldSetting';
import { Input } from '../common/Input';
import { Modal, ModalFooter } from '../common/Modal';
import { Select } from '../common/Select';
import { Textarea } from '../common/Textarea';

type WorldSettingFormProps = {
  isOpen: boolean;
  onClose: () => void;
  workId: string;
  characters: Character[];
  episodes: Episode[];
  setting?: WorldSetting | null;
  onSubmit: (data: WorldSettingInput) => void;
};

const categoryOptions = (
  Object.keys(WORLD_SETTING_CATEGORY_LABELS) as WorldSettingCategory[]
).map((key) => ({ value: key, label: WORLD_SETTING_CATEGORY_LABELS[key] }));

const emptyForm = (workId: string): WorldSettingInput => ({
  workId,
  name: '',
  category: 'term',
  description: '',
  relatedCharacterIds: [],
  relatedEpisodeIds: [],
  memo: '',
});

export function WorldSettingForm({
  isOpen,
  onClose,
  workId,
  characters,
  episodes,
  setting,
  onSubmit,
}: WorldSettingFormProps) {
  const [form, setForm] = useState<WorldSettingInput>(emptyForm(workId));

  useEffect(() => {
    if (setting) {
      const { id: _id, createdAt: _c, updatedAt: _u, ...rest } = setting;
      setForm(rest);
    } else {
      setForm(emptyForm(workId));
    }
  }, [setting, isOpen, workId]);

  const toggleCharacter = (id: string) => {
    setForm((prev) => ({
      ...prev,
      relatedCharacterIds: prev.relatedCharacterIds.includes(id)
        ? prev.relatedCharacterIds.filter((cid) => cid !== id)
        : [...prev.relatedCharacterIds, id],
    }));
  };

  const toggleEpisode = (id: string) => {
    setForm((prev) => ({
      ...prev,
      relatedEpisodeIds: prev.relatedEpisodeIds.includes(id)
        ? prev.relatedEpisodeIds.filter((eid) => eid !== id)
        : [...prev.relatedEpisodeIds, id],
    }));
  };

  const handleSubmit = () => {
    if (!form.name.trim()) return;
    onSubmit(form);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={setting ? '세계관 설정 수정' : '새 세계관 설정'}
      size="xl"
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="이름"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <Select
          label="카테고리"
          value={form.category}
          onChange={(e) =>
            setForm({ ...form, category: e.target.value as WorldSettingCategory })
          }
          options={categoryOptions}
        />
      </div>

      <div className="mt-4 space-y-4">
        <Textarea
          label="설명"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-300">
            관련 인물
          </label>
          {characters.length === 0 ? (
            <p className="text-sm text-gray-500">등록된 캐릭터가 없습니다.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {characters.map((char) => (
                <button
                  key={char.id}
                  type="button"
                  onClick={() => toggleCharacter(char.id)}
                  className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                    form.relatedCharacterIds.includes(char.id)
                      ? 'border-accent bg-accent/20 text-accent-hover'
                      : 'border-surface-border bg-surface-overlay text-gray-400 hover:border-gray-500'
                  }`}
                >
                  {char.name}
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-300">
            관련 회차
          </label>
          {episodes.length === 0 ? (
            <p className="text-sm text-gray-500">등록된 회차가 없습니다.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {episodes.map((ep) => (
                <button
                  key={ep.id}
                  type="button"
                  onClick={() => toggleEpisode(ep.id)}
                  className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                    form.relatedEpisodeIds.includes(ep.id)
                      ? 'border-accent bg-accent/20 text-accent-hover'
                      : 'border-surface-border bg-surface-overlay text-gray-400 hover:border-gray-500'
                  }`}
                >
                  {ep.episodeNumber}화
                </button>
              ))}
            </div>
          )}
        </div>

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
        confirmLabel={setting ? '수정' : '추가'}
      />
    </Modal>
  );
}
