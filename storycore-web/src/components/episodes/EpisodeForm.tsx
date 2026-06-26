import { useEffect, useState } from 'react';
import type { Character } from '../../types/character';
import type { Episode, EpisodeInput } from '../../types/episode';
import { Input } from '../common/Input';
import { Modal, ModalFooter } from '../common/Modal';
import { Textarea } from '../common/Textarea';

type EpisodeFormProps = {
  isOpen: boolean;
  onClose: () => void;
  workId: string;
  characters: Character[];
  episode?: Episode | null;
  onSubmit: (data: EpisodeInput) => void;
};

const emptyForm = (workId: string): EpisodeInput => ({
  workId,
  episodeNumber: 1,
  title: '',
  summary: '',
  characterIds: [],
  locations: [],
  revealedSettings: '',
  foreshadows: '',
  resolvedForeshadows: '',
  draft: '',
  authorNote: '',
});

export function EpisodeForm({
  isOpen,
  onClose,
  workId,
  characters,
  episode,
  onSubmit,
}: EpisodeFormProps) {
  const [form, setForm] = useState<EpisodeInput>(emptyForm(workId));
  const [locationsText, setLocationsText] = useState('');

  useEffect(() => {
    if (episode) {
      const { id: _id, createdAt: _c, updatedAt: _u, ...rest } = episode;
      setForm(rest);
      setLocationsText(rest.locations.join(', '));
    } else {
      setForm(emptyForm(workId));
      setLocationsText('');
    }
  }, [episode, isOpen, workId]);

  const toggleCharacter = (characterId: string) => {
    setForm((prev) => ({
      ...prev,
      characterIds: prev.characterIds.includes(characterId)
        ? prev.characterIds.filter((id) => id !== characterId)
        : [...prev.characterIds, characterId],
    }));
  };

  const handleSubmit = () => {
    if (!form.title.trim()) return;
    onSubmit({
      ...form,
      locations: locationsText
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    });
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={episode ? '회차 수정' : '새 회차'}
      size="xl"
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="회차 번호"
          type="number"
          min={1}
          value={form.episodeNumber}
          onChange={(e) =>
            setForm({ ...form, episodeNumber: Number(e.target.value) || 1 })
          }
          required
        />
        <Input
          label="제목"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          required
        />
      </div>

      <div className="mt-4 space-y-4">
        <Textarea
          label="요약"
          value={form.summary}
          onChange={(e) => setForm({ ...form, summary: e.target.value })}
        />

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-300">
            등장 인물
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
                    form.characterIds.includes(char.id)
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

        <Input
          label="등장 장소 (쉼표로 구분)"
          value={locationsText}
          onChange={(e) => setLocationsText(e.target.value)}
          placeholder="예: 서울, 게이트 내부"
        />

        <Textarea
          label="새로 공개된 설정"
          value={form.revealedSettings}
          onChange={(e) => setForm({ ...form, revealedSettings: e.target.value })}
        />
        <Textarea
          label="떡밥"
          value={form.foreshadows}
          onChange={(e) => setForm({ ...form, foreshadows: e.target.value })}
        />
        <Textarea
          label="회수한 떡밥"
          value={form.resolvedForeshadows}
          onChange={(e) => setForm({ ...form, resolvedForeshadows: e.target.value })}
        />
        <Textarea
          label="본문 초안"
          value={form.draft}
          onChange={(e) => setForm({ ...form, draft: e.target.value })}
          rows={6}
        />
        <Textarea
          label="작가 메모"
          value={form.authorNote}
          onChange={(e) => setForm({ ...form, authorNote: e.target.value })}
          rows={2}
        />
      </div>

      <ModalFooter
        onCancel={onClose}
        onConfirm={handleSubmit}
        confirmLabel={episode ? '수정' : '추가'}
      />
    </Modal>
  );
}
