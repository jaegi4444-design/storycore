import type { Work } from '../../types/work';

type WorkDetailProps = {
  work: Work;
};

export function WorkDetail({ work }: WorkDetailProps) {
  return (
    <div className="rounded-xl border border-surface-border bg-surface-raised p-6">
      <h3 className="text-xl font-semibold text-gray-100">{work.title}</h3>
      <span className="mt-2 inline-block rounded-full bg-surface-overlay px-3 py-1 text-xs text-gray-400">
        {work.genre}
      </span>
      <dl className="mt-6 space-y-4 text-sm">
        <div>
          <dt className="font-medium text-gray-400">한 줄 소개</dt>
          <dd className="mt-1 text-gray-200">{work.oneLineSummary || '(없음)'}</dd>
        </div>
        <div>
          <dt className="font-medium text-gray-400">전체 줄거리</dt>
          <dd className="mt-1 whitespace-pre-wrap text-gray-200">{work.synopsis || '(없음)'}</dd>
        </div>
        <div>
          <dt className="font-medium text-gray-400">작가 메모</dt>
          <dd className="mt-1 whitespace-pre-wrap text-gray-200">{work.authorNote || '(없음)'}</dd>
        </div>
      </dl>
    </div>
  );
}
