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
};

export function WorkCategoryEditor({
  label,
  description,
  options,
  onChange,
  placeholder = '항목 이름',
}: WorkCategoryEditorProps) {
  const [draft, setDraft] = useState('');

  const addOption = () => {
    const name = draft.trim();
    if (!name) return;
    if (options.some((o) => o.name === name)) {
      setDraft('');
      return;
    }
    onChange([...options, createWorkOption(name)]);
    setDraft('');
  };

  const removeOption = (id: string) => {
    onChange(options.filter((o) => o.id !== id));
  };

  return (
    <div className="rounded-lg border border-surface-border bg-surface-overlay/40 p-4">
      <div className="mb-3">
        <h4 className="text-sm font-semibold text-gray-200">{label}</h4>
        {description && <p className="mt-1 text-xs text-gray-500">{description}</p>}
      </div>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <span
            key={option.id}
            className="inline-flex items-center gap-1 rounded-full bg-surface-border px-3 py-1 text-sm text-gray-200"
          >
            {option.name}
            <button
              type="button"
              onClick={() => removeOption(option.id)}
              className="text-gray-500 hover:text-red-400"
              aria-label={`${option.name} 삭제`}
            >
              ×
            </button>
          </span>
        ))}
        {options.length === 0 && (
          <span className="text-xs text-amber-400">등록된 항목이 없습니다 (필수)</span>
        )}
      </div>
      <div className="mt-3 flex gap-2">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={placeholder}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addOption();
            }
          }}
        />
        <Button type="button" variant="secondary" onClick={addOption} className="shrink-0">
          추가
        </Button>
      </div>
    </div>
  );
}
