import { useMemo } from 'react';
import type { Character } from '../../types/character';
import type { Conflict } from '../../types/conflict';
import type { Episode } from '../../types/episode';
import { checkConflicts } from '../../utils/conflictChecker';
import { EmptyState } from '../common/EmptyState';

type ConflictCheckerProps = {
  workId: string | null;
  characters: Character[];
  episodes: Episode[];
};

export function ConflictChecker({ workId, characters, episodes }: ConflictCheckerProps) {
  const conflicts = useMemo(() => {
    if (!workId) return [];
    return checkConflicts({ characters, episodes });
  }, [workId, characters, episodes]);

  const errors = conflicts.filter((c) => c.level === 'error');
  const warnings = conflicts.filter((c) => c.level === 'warning');

  if (!workId) {
    return (
      <EmptyState
        title="작품을 먼저 선택해주세요"
        description="설정 충돌을 확인하려면 작품 관리에서 작품을 선택하세요."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">설정 충돌 체크</h2>
        <p className="mt-1 text-sm text-gray-500">
          캐릭터와 회차 데이터 간의 설정 충돌을 자동으로 검사합니다.
        </p>
      </div>

      {conflicts.length === 0 ? (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-lg font-medium text-emerald-300">
            현재 발견된 설정 충돌이 없습니다.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {errors.length > 0 && (
            <ConflictSection
              title="오류"
              subtitle={`${errors.length}건의 심각한 충돌`}
              conflicts={errors}
              variant="error"
            />
          )}
          {warnings.length > 0 && (
            <ConflictSection
              title="경고"
              subtitle={`${warnings.length}건의 주의 필요`}
              conflicts={warnings}
              variant="warning"
            />
          )}
        </div>
      )}
    </div>
  );
}

function ConflictSection({
  title,
  subtitle,
  conflicts,
  variant,
}: {
  title: string;
  subtitle: string;
  conflicts: Conflict[];
  variant: 'error' | 'warning';
}) {
  const colors =
    variant === 'error'
      ? {
          border: 'border-red-500/30',
          bg: 'bg-red-500/10',
          badge: 'bg-red-500/20 text-red-400',
          icon: 'text-red-400',
        }
      : {
          border: 'border-amber-500/30',
          bg: 'bg-amber-500/10',
          badge: 'bg-amber-500/20 text-amber-400',
          icon: 'text-amber-400',
        };

  return (
    <section>
      <div className="mb-3 flex items-center gap-3">
        <h3 className="text-lg font-semibold text-gray-100">{title}</h3>
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colors.badge}`}>
          {subtitle}
        </span>
      </div>
      <div className="space-y-3">
        {conflicts.map((conflict) => (
          <div
            key={conflict.id}
            className={`rounded-xl border p-4 ${colors.border} ${colors.bg}`}
          >
            <div className="flex items-start gap-3">
              <div className={`mt-0.5 shrink-0 ${colors.icon}`}>
                {variant === 'error' ? (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                ) : (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                )}
              </div>
              <div>
                <h4 className="font-medium text-gray-100">{conflict.title}</h4>
                <p className="mt-1 text-sm text-gray-400">{conflict.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
