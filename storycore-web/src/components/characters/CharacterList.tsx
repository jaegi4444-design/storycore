import { useState } from 'react';
import type { Character, CharacterSubmitPayload } from '../../types/character';
import { Button } from '../common/Button';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { EmptyState } from '../common/EmptyState';
import { CharacterCard } from './CharacterCard';
import { CharacterDetail } from './CharacterDetail';
import { CharacterForm } from './CharacterForm';

type CharacterListProps = {
  workId: string | null;
  characters: Character[];
  onAdd: (payload: CharacterSubmitPayload) => void | Promise<void>;
  onUpdate: (id: string, payload: CharacterSubmitPayload) => void | Promise<void>;
  onDelete: (character: Character) => void | Promise<void>;
};

export function CharacterList({
  workId,
  characters,
  onAdd,
  onUpdate,
  onDelete,
}: CharacterListProps) {
  const [formOpen, setFormOpen] = useState(false);
  const [editingCharacter, setEditingCharacter] = useState<Character | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Character | null>(null);

  const selectedCharacter = characters.find((c) => c.id === selectedId);

  if (!workId) {
    return (
      <EmptyState
        title="작품을 먼저 선택해주세요"
        description="캐릭터를 관리하려면 작품 관리에서 작품을 선택하세요."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-100">캐릭터 관리</h2>
          <p className="mt-1 text-sm text-gray-500">총 {characters.length}명의 캐릭터</p>
        </div>
        <Button
          onClick={() => {
            setEditingCharacter(null);
            setFormOpen(true);
          }}
        >
          + 새 캐릭터
        </Button>
      </div>

      {characters.length === 0 ? (
        <EmptyState
          title="등록된 캐릭터가 없습니다"
          description="작품에 등장하는 캐릭터를 추가해보세요."
          action={<Button onClick={() => setFormOpen(true)}>캐릭터 추가</Button>}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="grid gap-4 sm:grid-cols-2 lg:col-span-2 lg:grid-cols-1">
            {characters.map((character) => (
              <CharacterCard
                key={character.id}
                character={character}
                isSelected={selectedId === character.id}
                onClick={() => setSelectedId(character.id)}
                onEdit={() => {
                  setEditingCharacter(character);
                  setFormOpen(true);
                }}
                onDelete={() => setDeleteTarget(character)}
              />
            ))}
          </div>
          <div className="lg:col-span-3">
            {selectedCharacter ? (
              <div className="rounded-xl border border-surface-border bg-surface-raised p-6">
                <CharacterDetail character={selectedCharacter} />
              </div>
            ) : (
              <EmptyState
                title="캐릭터를 선택하세요"
                description="목록에서 캐릭터를 클릭하면 상세 정보를 볼 수 있습니다."
              />
            )}
          </div>
        </div>
      )}

      <CharacterForm
        isOpen={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditingCharacter(null);
        }}
        workId={workId}
        character={editingCharacter}
        onSubmit={async (payload) => {
          if (editingCharacter) {
            await onUpdate(editingCharacter.id, payload);
          } else {
            await onAdd(payload);
          }
          setFormOpen(false);
          setEditingCharacter(null);
        }}
      />

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && onDelete(deleteTarget)}
        title="캐릭터 삭제"
        message={`"${deleteTarget?.name}" 캐릭터를 삭제하시겠습니까?`}
      />
    </div>
  );
}
