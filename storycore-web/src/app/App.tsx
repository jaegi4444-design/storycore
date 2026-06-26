import { useMemo, useState } from 'react';
import { LoginPage } from '../components/auth/LoginPage';
import { MainLayout } from '../components/layout/MainLayout';
import type { NavItem } from '../components/layout/Sidebar';
import { WorkList } from '../components/works/WorkList';
import { CharacterList } from '../components/characters/CharacterList';
import { EpisodeList } from '../components/episodes/EpisodeList';
import { WorldSettingList } from '../components/worldbuilding/WorldSettingList';
import { ConflictChecker } from '../components/conflict/ConflictChecker';
import { PromptGenerator } from '../components/prompt/PromptGenerator';
import { useAuth } from '../contexts/AuthContext';
import { useStoryCore } from '../contexts/DataContext';

type PageId =
  | 'works'
  | 'characters'
  | 'episodes'
  | 'worldbuilding'
  | 'conflict'
  | 'prompt';

const navItems: NavItem[] = [
  {
    id: 'works',
    label: '작품',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
  },
  {
    id: 'characters',
    label: '캐릭터',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
  {
    id: 'episodes',
    label: '회차',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    id: 'worldbuilding',
    label: '세계관',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    id: 'conflict',
    label: '충돌 체크',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
  },
  {
    id: 'prompt',
    label: '프롬프트 생성',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
];

function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface">
      <div className="text-center">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        <p className="mt-4 text-sm text-gray-500">불러오는 중...</p>
      </div>
    </div>
  );
}

export function App() {
  const { user, loading: authLoading, signOut, isLocalMode } = useAuth();
  const {
    loading: dataLoading,
    error,
    works,
    selectedWorkId,
    selectWork,
    addWork,
    updateWork,
    deleteWork,
    addCharacter,
    updateCharacter,
    deleteCharacter,
    addEpisode,
    updateEpisode,
    deleteEpisode,
    addWorldSetting,
    updateWorldSetting,
    deleteWorldSetting,
    getWorkById,
    getCharactersByWorkId,
    getEpisodesByWorkId,
    getWorldSettingsByWorkId,
  } = useStoryCore();

  const [activePage, setActivePage] = useState<PageId>('works');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const selectedWork = selectedWorkId ? getWorkById(selectedWorkId) : undefined;

  const workCharacters = useMemo(
    () => (selectedWorkId ? getCharactersByWorkId(selectedWorkId) : []),
    [selectedWorkId, getCharactersByWorkId],
  );

  const workEpisodes = useMemo(
    () => (selectedWorkId ? getEpisodesByWorkId(selectedWorkId) : []),
    [selectedWorkId, getEpisodesByWorkId],
  );

  const workWorldSettings = useMemo(
    () => (selectedWorkId ? getWorldSettingsByWorkId(selectedWorkId) : []),
    [selectedWorkId, getWorldSettingsByWorkId],
  );

  if (authLoading) return <LoadingScreen />;
  if (!user) return <LoginPage />;

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch {
      alert('로그아웃에 실패했습니다.');
    }
  };

  const renderPage = () => {
    if (dataLoading) return <LoadingScreen />;

    if (error) {
      return (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-center">
          <p className="text-red-300">{error}</p>
        </div>
      );
    }

    switch (activePage) {
      case 'works':
        return (
          <WorkList
            works={works}
            selectedWorkId={selectedWorkId}
            onSelect={(id) => void selectWork(id)}
            onAdd={(data) => void addWork(data)}
            onUpdate={(id, data) => void updateWork(id, data)}
            onDelete={(id) => void deleteWork(id)}
          />
        );
      case 'characters':
        return (
          <CharacterList
            workId={selectedWorkId}
            characters={workCharacters}
            onAdd={addCharacter}
            onUpdate={updateCharacter}
            onDelete={deleteCharacter}
          />
        );
      case 'episodes':
        return (
          <EpisodeList
            workId={selectedWorkId}
            episodes={workEpisodes}
            characters={workCharacters}
            onAdd={(data) => void addEpisode(data)}
            onUpdate={(id, data) => void updateEpisode(id, data)}
            onDelete={(id) => void deleteEpisode(id)}
          />
        );
      case 'worldbuilding':
        return (
          <WorldSettingList
            workId={selectedWorkId}
            settings={workWorldSettings}
            characters={workCharacters}
            episodes={workEpisodes}
            onAdd={(data) => void addWorldSetting(data)}
            onUpdate={(id, data) => void updateWorldSetting(id, data)}
            onDelete={(id) => void deleteWorldSetting(id)}
          />
        );
      case 'conflict':
        return (
          <ConflictChecker
            workId={selectedWorkId}
            characters={workCharacters}
            episodes={workEpisodes}
          />
        );
      case 'prompt':
        return (
          <PromptGenerator
            work={selectedWork ?? null}
            episodes={workEpisodes}
            characters={workCharacters}
            worldSettings={workWorldSettings}
          />
        );
      default:
        return null;
    }
  };

  return (
    <MainLayout
      navItems={navItems}
      activeNavId={activePage}
      onNavigate={(id) => setActivePage(id as PageId)}
      workTitle={selectedWork?.title ?? null}
      user={user}
      isLocalMode={isLocalMode}
      onSignOut={() => void handleSignOut()}
      sidebarOpen={sidebarOpen}
      onSidebarToggle={() => setSidebarOpen((prev) => !prev)}
      onSidebarClose={() => setSidebarOpen(false)}
    >
      {renderPage()}
    </MainLayout>
  );
}
