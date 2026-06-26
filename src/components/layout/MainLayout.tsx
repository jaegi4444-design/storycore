import type { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar, type NavItem } from './Sidebar';

type MainLayoutProps = {
  children: ReactNode;
  navItems: NavItem[];
  activeNavId: string;
  onNavigate: (id: string) => void;
  workTitle: string | null;
  sidebarOpen: boolean;
  onSidebarToggle: () => void;
  onSidebarClose: () => void;
};

export function MainLayout({
  children,
  navItems,
  activeNavId,
  onNavigate,
  workTitle,
  sidebarOpen,
  onSidebarToggle,
  onSidebarClose,
}: MainLayoutProps) {
  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar
        items={navItems}
        activeId={activeNavId}
        onNavigate={onNavigate}
        isOpen={sidebarOpen}
        onClose={onSidebarClose}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header workTitle={workTitle} onMenuToggle={onSidebarToggle} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}
