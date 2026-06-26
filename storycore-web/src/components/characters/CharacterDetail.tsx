import type { ReactNode } from 'react';
import type { Character } from '../../types/character';
import { CHARACTER_STATUS_LABELS } from '../../types/character';
import { CharacterAvatar } from '../common/CharacterAvatar';

type CharacterDetailProps = {
  character: Character;
};

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-surface-border bg-surface-overlay/50 p-4">
      <h4 className="mb-3 text-sm font-semibold text-accent-hover">{title}</h4>
      {children}
    </section>
  );
}

function Field({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div>
      <dt className="text-xs text-gray-500">{label}</dt>
      <dd className="mt-0.5 text-sm text-gray-200">{value ?? '(없음)'}</dd>
    </div>
  );
}

export function CharacterDetail({ character }: CharacterDetailProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start">
        <CharacterAvatar name={character.name} imageUrl={character.imageUrl} size="lg" />
        <div className="text-center sm:text-left">
          <h3 className="text-2xl font-semibold text-gray-100">{character.name}</h3>
          {character.alias && (
            <span className="text-lg text-gray-500">{character.alias}</span>
          )}
        </div>
      </div>

      <Section title="기본 정보">
        <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="나이" value={character.age} />
          <Field label="성별" value={character.gender} />
          <Field label="등급" value={character.rank} />
          <Field label="직업" value={character.job} />
          <Field label="소속" value={character.affiliation} />
          <Field label="소속 상세" value={character.affiliationDetail} />
          <Field label="역할" value={character.role} />
          <Field label="첫 등장 회차" value={character.firstAppearanceEpisode} />
          <Field
            label="현재 상태"
            value={CHARACTER_STATUS_LABELS[character.currentStatus]}
          />
        </dl>
      </Section>

      <Section title="능력">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {character.abilities || '(없음)'}
        </p>
      </Section>

      <Section title="성격">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {character.personality || '(없음)'}
        </p>
      </Section>

      <Section title="외형">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {character.appearance || '(없음)'}
        </p>
      </Section>

      <Section title="독자 공개 설정">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {character.publicInfo || '(없음)'}
        </p>
      </Section>

      <Section title="작가 비밀 설정">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {character.secretInfo || '(없음)'}
        </p>
      </Section>

      <Section title="메모">
        <p className="whitespace-pre-wrap text-sm text-gray-200">
          {character.memo || '(없음)'}
        </p>
      </Section>
    </div>
  );
}
