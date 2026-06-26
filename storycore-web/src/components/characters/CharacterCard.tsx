import type { Character } from '../../types/character';
import { CHARACTER_STATUS_LABELS } from '../../types/character';
import { CharacterAvatar } from '../common/CharacterAvatar';

type CharacterCardProps = {
  character: Character;
  isSelected?: boolean;
  onClick: () => void;
  onEdit: () => void;
  onDelete: () => void;
  highlightRank?: string;
  highlightJob?: string;
  highlightAffiliation?: string;
};

const statusColors: Record<Character['currentStatus'], string> = {
  active: 'bg-emerald-500/20 text-emerald-400',
  dead: 'bg-red-500/20 text-red-400',
  missing: 'bg-amber-500/20 text-amber-400',
  unknown: 'bg-gray-500/20 text-gray-400',
};

function CategoryCell({
  label,
  value,
  tone,
  highlighted,
}: {
  label: string;
  value: string;
  tone: 'violet' | 'sky' | 'emerald';
  highlighted?: boolean;
}) {
  const toneClass = {
    violet: highlighted
      ? 'border-violet-500/50 bg-violet-500/15 text-violet-200'
      : 'border-surface-border/60 bg-surface-overlay/40 text-gray-200',
    sky: highlighted
      ? 'border-sky-500/50 bg-sky-500/15 text-sky-200'
      : 'border-surface-border/60 bg-surface-overlay/40 text-gray-200',
    emerald: highlighted
      ? 'border-emerald-500/50 bg-emerald-500/15 text-emerald-200'
      : 'border-surface-border/60 bg-surface-overlay/40 text-gray-200',
  }[tone];

  return (
    <div className={`rounded-lg border px-2.5 py-2 ${toneClass}`}>
      <p className="text-[10px] font-medium uppercase tracking-wide text-gray-500">{label}</p>
      <p className="mt-0.5 truncate text-sm">{value || '-'}</p>
    </div>
  );
}

export function CharacterCard({
  character,
  isSelected,
  onClick,
  onEdit,
  onDelete,
  highlightRank,
  highlightJob,
  highlightAffiliation,
}: CharacterCardProps) {
  return (
    <div
      className={`cursor-pointer rounded-xl border bg-surface-raised p-4 transition-all hover:border-accent/40 ${
        isSelected ? 'border-accent ring-1 ring-accent/30' : 'border-surface-border'
      }`}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <CharacterAvatar name={character.name} imageUrl={character.imageUrl} size="sm" />
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h3 className="truncate font-semibold text-gray-100">{character.name}</h3>
              {character.alias && (
                <p className="text-sm text-gray-500">{character.alias}</p>
              )}
            </div>
            <span
              className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[character.currentStatus]}`}
            >
              {CHARACTER_STATUS_LABELS[character.currentStatus]}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2">
        <CategoryCell
          label="등급"
          value={character.rank}
          tone="violet"
          highlighted={!!highlightRank && character.rank === highlightRank}
        />
        <CategoryCell
          label="직업"
          value={character.job}
          tone="sky"
          highlighted={!!highlightJob && character.job === highlightJob}
        />
        <CategoryCell
          label="소속"
          value={character.affiliation}
          tone="emerald"
          highlighted={!!highlightAffiliation && character.affiliation === highlightAffiliation}
        />
      </div>

      <div className="mt-4 flex gap-2" onClick={(e) => e.stopPropagation()}>
        <button
          onClick={onEdit}
          className="rounded-lg px-3 py-1 text-xs text-gray-400 transition-colors hover:bg-surface-overlay hover:text-gray-200"
        >
          수정
        </button>
        <button
          onClick={onDelete}
          className="rounded-lg px-3 py-1 text-xs text-red-400 transition-colors hover:bg-red-500/10"
        >
          삭제
        </button>
      </div>
    </div>
  );
}
