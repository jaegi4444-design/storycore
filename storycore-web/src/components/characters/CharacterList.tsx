import { useMemo, useState } from 'react';

import type { Character, CharacterSubmitPayload } from '../../types/character';

import type { Work } from '../../types/work';

import { hasRequiredWorkCategories, toSelectOptions } from '../../types/work';

import { Button } from '../common/Button';

import { ConfirmDialog } from '../common/ConfirmDialog';

import { EmptyState } from '../common/EmptyState';

import { Select } from '../common/Select';

import { CharacterCard } from './CharacterCard';

import { CharacterDetail } from './CharacterDetail';

import { CharacterForm } from './CharacterForm';



type CharacterListProps = {

  work: Work | null;

  characters: Character[];

  onAdd: (payload: CharacterSubmitPayload) => void | Promise<void>;

  onUpdate: (id: string, payload: CharacterSubmitPayload) => void | Promise<void>;

  onDelete: (character: Character) => void | Promise<void>;

};



const ALL_VALUE = '';



export function CharacterList({

  work,

  characters,

  onAdd,

  onUpdate,

  onDelete,

}: CharacterListProps) {

  const [formOpen, setFormOpen] = useState(false);

  const [editingCharacter, setEditingCharacter] = useState<Character | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [deleteTarget, setDeleteTarget] = useState<Character | null>(null);

  const [filterRank, setFilterRank] = useState(ALL_VALUE);

  const [filterJob, setFilterJob] = useState(ALL_VALUE);

  const [filterAffiliation, setFilterAffiliation] = useState(ALL_VALUE);



  const selectedCharacter = characters.find((c) => c.id === selectedId);



  const categoriesReady = work ? hasRequiredWorkCategories(work) : false;



  const rankFilterOptions = useMemo(

    () => [{ value: ALL_VALUE, label: '전체 등급' }, ...(work ? toSelectOptions(work.ranks) : [])],

    [work],

  );

  const jobFilterOptions = useMemo(

    () => [{ value: ALL_VALUE, label: '전체 직업' }, ...(work ? toSelectOptions(work.jobs) : [])],

    [work],

  );

  const affiliationFilterOptions = useMemo(

    () => [

      { value: ALL_VALUE, label: '전체 소속' },

      ...(work ? toSelectOptions(work.affiliations) : []),

    ],

    [work],

  );



  const filteredCharacters = useMemo(() => {

    return characters.filter((c) => {

      if (filterRank && c.rank !== filterRank) return false;

      if (filterJob && c.job !== filterJob) return false;

      if (filterAffiliation && c.affiliation !== filterAffiliation) return false;

      return true;

    });

  }, [characters, filterRank, filterJob, filterAffiliation]);



  const hasActiveFilter = !!(filterRank || filterJob || filterAffiliation);



  const clearFilters = () => {

    setFilterRank(ALL_VALUE);

    setFilterJob(ALL_VALUE);

    setFilterAffiliation(ALL_VALUE);

  };



  if (!work) {

    return (

      <EmptyState

        title="작품을 먼저 선택해주세요"

        description="캐릭터를 관리하려면 작품 관리에서 작품을 선택하세요."

      />

    );

  }



  const handleAddClick = () => {

    setEditingCharacter(null);

    setFormOpen(true);

  };



  return (

    <div className="space-y-6">

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

        <div>

          <h2 className="text-xl font-semibold text-gray-100">캐릭터 관리</h2>

          <p className="mt-1 text-sm text-gray-500">

            총 {characters.length}명

            {hasActiveFilter && ` · 조회 ${filteredCharacters.length}명`}

          </p>

        </div>

        <Button onClick={handleAddClick}>+ 새 캐릭터</Button>

      </div>



      {characters.length > 0 && (

        <div className="rounded-xl border border-surface-border bg-surface-raised p-4">

          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">

            <h3 className="text-sm font-semibold text-gray-200">목록 조회</h3>

            {hasActiveFilter && (

              <button

                type="button"

                onClick={clearFilters}

                className="text-xs text-accent-hover hover:underline"

              >

                필터 초기화

              </button>

            )}

          </div>

          {categoriesReady ? (

            <div className="grid gap-3 sm:grid-cols-3">

              <Select

                label="등급"

                value={filterRank}

                onChange={(e) => setFilterRank(e.target.value)}

                options={rankFilterOptions}

              />

              <Select

                label="직업"

                value={filterJob}

                onChange={(e) => setFilterJob(e.target.value)}

                options={jobFilterOptions}

              />

              <Select

                label="소속"

                value={filterAffiliation}

                onChange={(e) => setFilterAffiliation(e.target.value)}

                options={affiliationFilterOptions}

              />

            </div>

          ) : (

            <p className="text-sm text-gray-500">

              등급·직업·소속으로 조회하려면 작품 관리에서 카테고리를 먼저 등록해주세요.

            </p>

          )}

        </div>

      )}



      {characters.length === 0 ? (

        <EmptyState

          title="등록된 캐릭터가 없습니다"

          description="작품에 등장하는 캐릭터를 추가해보세요."

          action={<Button onClick={handleAddClick}>캐릭터 추가</Button>}

        />

      ) : filteredCharacters.length === 0 ? (

        <EmptyState

          title="조건에 맞는 캐릭터가 없습니다"

          description="다른 등급·직업·소속을 선택하거나 필터를 초기화해보세요."

          action={

            <Button variant="secondary" onClick={clearFilters}>

              필터 초기화

            </Button>

          }

        />

      ) : (

        <div className="grid gap-6 lg:grid-cols-5">

          <div className="grid gap-4 sm:grid-cols-2 lg:col-span-2 lg:grid-cols-1">

            {filteredCharacters.map((character) => (

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

            {selectedCharacter && filteredCharacters.some((c) => c.id === selectedId) ? (

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

        work={work}

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


