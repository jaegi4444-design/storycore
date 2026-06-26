import { useState } from 'react';
import type { WorkOption } from '../../types/work';
import { createWorkOption } from '../../types/work';
import { Button } from './Button';
import { Input } from './Input';

type WorkCategoryEditorProps = {
  label: string;
  description?: string;
  options: WorkOption[];
  onChange: (options: WorkOption[]) => void;
  placeholder?: string;
  accent?: 'violet' | 'sky' | 'emerald' | 'default';
};

const accentStyles = {
  default: {
    border: 'border-surface-border',
    badge: 'bg-surface-border text-gray-200',
    header: 'text-gray-200',
    count: 'bg-surface-overlay text-gray-400',
  },
  violet: {
    border: 'border-violet-500/30',
    badge: 'bg-violet-500/20 text-violet-200',
    header: 'text-violet-200',
    count: 'bg-violet-500/10 text-violet-300',
  },
  sky: {
    border: 'border-sky-500/30',
    badge: 'bg-sky-500/20 text-sky-200',
    header: 'text-sky-200',
    count: 'bg-sky-500/10 text-sky-300',
  },
  emerald: {
    border: 'border-emerald-500/30',
    badge: 'bg-emerald-500/20 text-emerald-200',
    header: 'text-emerald-200',
    count: 'bg-emerald-500/10 text-emerald-300',
  },
};

export function WorkCategoryEditor({
  label,
  description,
  options,
  onChange,
  placeholder = '항목 이름',
  accent = 'default',
}: WorkCategoryEditorProps) {
  const [draft, setDraft] = useState('');
  const [duplicateError, setDuplicateError] = useState(false);
  const styles = accentStyles[accent];

  const addOption = () => {
    const name = draft.trim();
    if (!name) return;
    if (options.some((o) => o.name === name)) {
      setDuplicateError(true);
      return;
    }
    onChange([...options, createWorkOption(name)]);
    setDraft('');
    setDuplicateError(false);
  };

  const removeOption = (id: string) => {
    onChange(options.filter((o) => o.id !== id));
  };

  return (
    <div className={`flex h-full flex-col rounded-lg border bg-surface-overlay/40 p-4 ${styles.border}`}>
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h4 className={`text-sm font-semibold ${styles.header}`}>{label}</h4>
            <span className={`rounded-full px-2 py-0.5 text-xs ${styles.count}`}>
              {options.length}개
            </span>
          </div>
          {description && <p className="mt-1 text-xs text-gray-500">{description}</p>}
        </div>
      </div>

      <div className="min-h-[72px] flex-1">
        <div className="flex flex-wrap gap-2">
          {options.map((option) => (
            <span
              key={option.id}
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm ${styles.badge}`}
            >
              {option.name}
              <button
                type="button"
                onClick={() => removeOption(option.id)}
                className="opacity-70 hover:text-red-400 hover:opacity-100"
                aria-label={`${option.name} 삭제`}
              >
                ×
              </button>
            </span>
          ))}
          {options.length === 0 && (
            <span className="text-xs text-amber-400">등록된 {label}이 없습니다 (필수)</span>
          )}
        </div>
      </div>

      <div className="mt-3 space-y-2 border-t border-surface-border/60 pt-3">
        <Input
          label={`${label} 추가`}
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value);
            setDuplicateError(false);
          }}
          placeholder={placeholder}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addOption();
            }
          }}
        />
        {duplicateError && (
          <p className="text-xs text-red-400">이미 등록된 {label}입니다.</p>
        )}
        <Button type="button" variant="secondary" onClick={addOption} className="w-full">
          + {label} 추가
        </Button>
      </div>
    </div>
  );
}
