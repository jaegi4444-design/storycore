import type { User } from '@supabase/supabase-js';
import { Button } from '../common/Button';

type HeaderProps = {
  workTitle: string | null;
  user: User;
  isLocalMode?: boolean;
  onMenuToggle: () => void;
  onSignOut: () => void;
};

export function Header({ workTitle, user, isLocalMode, onMenuToggle, onSignOut }: HeaderProps) {
  const avatarUrl = user.user_metadata?.avatar_url as string | undefined;
  const displayName =
    (user.user_metadata?.full_name as string | undefined) ??
    user.email?.split('@')[0] ??
    '사용자';

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-surface-border bg-surface/95 px-4 backdrop-blur-sm sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-surface-overlay hover:text-gray-200 lg:hidden"
          aria-label="메뉴 열기"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div>
          <p className="text-xs text-gray-500">현재 작품</p>
          <p className="text-sm font-semibold text-gray-100 sm:text-base">
            {workTitle ?? '작품을 선택해주세요'}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="hidden rounded-full bg-surface-overlay px-3 py-1 text-xs text-gray-500 sm:inline">
          {isLocalMode ? '로컬 저장' : '클라우드 저장'}
        </span>
        <div className="hidden items-center gap-2 sm:flex">
          {avatarUrl ? (
            <img src={avatarUrl} alt="" className="h-8 w-8 rounded-full object-cover" />
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/20 text-xs font-medium text-accent-hover">
              {displayName.charAt(0)}
            </div>
          )}
          <span className="max-w-[120px] truncate text-sm text-gray-300">{displayName}</span>
        </div>
        {!isLocalMode && (
          <Button variant="ghost" className="text-xs" onClick={onSignOut}>
            로그아웃
          </Button>
        )}
      </div>
    </header>
  );
}
