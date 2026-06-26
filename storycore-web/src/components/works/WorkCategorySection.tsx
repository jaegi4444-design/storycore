import { useEffect, useState } from 'react';
import type { Work, WorkOption } from '../../types/work';
import { workCategoryError } from '../../types/work';
import { Button } from '../common/Button';
import { WorkCategoryEditor } from '../common/WorkCategoryEditor';

type CategoryFields = {
  ranks: WorkOption[];
  jobs: WorkOption[];
  affiliations: WorkOption[];
};

type WorkCategorySectionProps = {
  work: Work;
  onSave: (categories: CategoryFields) => void | Promise<void>;
  compact?: boolean;
};

export function WorkCategorySection({ work, onSave, compact }: WorkCategorySectionProps) {
  const [ranks, setRanks] = useState(work.ranks);
  const [jobs, setJobs] = useState(work.jobs);
  const [affiliations, setAffiliations] = useState(work.affiliations);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setRanks(work.ranks);
    setJobs(work.jobs);
    setAffiliations(work.affiliations);
    setError(null);
  }, [work.id, work.ranks, work.jobs, work.affiliations]);

  const isDirty =
    JSON.stringify(ranks) !== JSON.stringify(work.ranks) ||
    JSON.stringify(jobs) !== JSON.stringify(work.jobs) ||
    JSON.stringify(affiliations) !== JSON.stringify(work.affiliations);

  const handleSave = async () => {
    const categoryError = workCategoryError({ ranks, jobs, affiliations });
    if (categoryError) {
      setError(categoryError);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave({ ranks, jobs, affiliations });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={compact ? 'space-y-4' : 'rounded-xl border border-surface-border bg-surface-raised p-5 sm:p-6'}>
      {!compact && (
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-100">등급 · 직업 · 소속 관리</h3>
            <p className="mt-1 text-sm text-gray-500">
              <span className="font-medium text-gray-400">{work.title}</span> 작품의 카테고리를 각각 등록합니다.
              캐릭터 추가 시 아래 목록에서 선택할 수 있습니다.
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {isDirty && (
              <span className="text-xs text-amber-400">저장되지 않은 변경</span>
            )}
            <Button onClick={handleSave} disabled={!isDirty || saving}>
              {saving ? '저장 중...' : '카테고리 저장'}
            </Button>
          </div>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <WorkCategoryEditor
          label="등급"
          description="캐릭터 등급 (예: D급, A급, S급)"
          options={ranks}
          onChange={setRanks}
          placeholder="등급 입력 후 추가"
          accent="violet"
        />
        <WorkCategoryEditor
          label="직업"
          description="캐릭터 직업 (예: 각성자, 팀장, 검사)"
          options={jobs}
          onChange={setJobs}
          placeholder="직업 입력 후 추가"
          accent="sky"
        />
        <WorkCategoryEditor
          label="소속"
          description="캐릭터 소속 (예: 서울팀, 한빙그룹)"
          options={affiliations}
          onChange={setAffiliations}
          placeholder="소속 입력 후 추가"
          accent="emerald"
        />
      </div>

      {compact && (
        <div className="flex items-center justify-between gap-3 border-t border-surface-border pt-4">
          {error ? (
            <p className="text-sm text-red-400">{error}</p>
          ) : (
            <p className="text-xs text-gray-500">등급·직업·소속을 각각 1개 이상 등록해야 캐릭터를 추가할 수 있습니다.</p>
          )}
          <Button onClick={handleSave} disabled={!isDirty || saving} className="shrink-0">
            {saving ? '저장 중...' : '목록에 적용'}
          </Button>
        </div>
      )}

      {!compact && error && <p className="mt-4 text-sm text-red-400">{error}</p>}
    </div>
  );
}
