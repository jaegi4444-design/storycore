import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { useAuth } from './AuthContext';
import {
  createLocalCharacter,
  createLocalEpisode,
  createLocalWork,
  createLocalWorldSetting,
  deleteLocalCharacter,
  deleteLocalEpisode,
  deleteLocalWork,
  deleteLocalWorldSetting,
  fetchLocalData,
  updateLocalCharacter,
  updateLocalEpisode,
  updateLocalWork,
  updateLocalWorldSetting,
  upsertLocalSelectedWork,
} from '../lib/localApi';
import {
  createCharacterWithImage,
  createEpisode,
  createWork,
  createWorldSetting,
  deleteCharacterRecord,
  deleteEpisodeRecord,
  deleteWorkRecord,
  deleteWorldSettingRecord,
  fetchAllUserData,
  reloadUserData,
  seedSampleData,
  updateCharacterWithImage,
  updateEpisodeRecord,
  updateWorkRecord,
  updateWorldSettingRecord,
  upsertSelectedWork,
  type StoryCoreData,
} from '../lib/storycoreApi';
import type { Character, CharacterSubmitPayload } from '../types/character';
import type { Episode, EpisodeInput } from '../types/episode';
import type { Work, WorkInput } from '../types/work';
import type { WorldSetting, WorldSettingInput } from '../types/worldSetting';

type DataContextValue = {
  loading: boolean;
  error: string | null;
  works: Work[];
  characters: Character[];
  episodes: Episode[];
  worldSettings: WorldSetting[];
  selectedWorkId: string | null;
  refresh: () => Promise<void>;
  selectWork: (id: string | null) => Promise<void>;
  addWork: (input: WorkInput) => Promise<void>;
  updateWork: (id: string, input: WorkInput) => Promise<void>;
  deleteWork: (id: string) => Promise<void>;
  addCharacter: (payload: CharacterSubmitPayload) => Promise<void>;
  updateCharacter: (id: string, payload: CharacterSubmitPayload) => Promise<void>;
  deleteCharacter: (character: Character) => Promise<void>;
  addEpisode: (input: EpisodeInput) => Promise<void>;
  updateEpisode: (id: string, input: EpisodeInput) => Promise<void>;
  deleteEpisode: (id: string) => Promise<void>;
  addWorldSetting: (input: WorldSettingInput) => Promise<void>;
  updateWorldSetting: (id: string, input: WorldSettingInput) => Promise<void>;
  deleteWorldSetting: (id: string) => Promise<void>;
  getWorkById: (id: string) => Work | undefined;
  getCharactersByWorkId: (workId: string) => Character[];
  getEpisodesByWorkId: (workId: string) => Episode[];
  getWorldSettingsByWorkId: (workId: string) => WorldSetting[];
};

const DataContext = createContext<DataContextValue | null>(null);

function applyData(setters: {
  setWorks: (v: Work[]) => void;
  setCharacters: (v: Character[]) => void;
  setEpisodes: (v: Episode[]) => void;
  setWorldSettings: (v: WorldSetting[]) => void;
  setSelectedWorkId: (v: string | null) => void;
}, data: StoryCoreData) {
  setters.setWorks(data.works);
  setters.setCharacters(data.characters);
  setters.setEpisodes(data.episodes);
  setters.setWorldSettings(data.worldSettings);
  setters.setSelectedWorkId(data.selectedWorkId);
}

export function DataProvider({ children }: { children: ReactNode }) {
  const { user, isLocalMode } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [works, setWorks] = useState<Work[]>([]);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [worldSettings, setWorldSettings] = useState<WorldSetting[]>([]);
  const [selectedWorkId, setSelectedWorkId] = useState<string | null>(null);

  const setters = useMemo(
    () => ({
      setWorks,
      setCharacters,
      setEpisodes,
      setWorldSettings,
      setSelectedWorkId,
    }),
    [],
  );

  const load = useCallback(async () => {
    if (!user) {
      setWorks([]);
      setCharacters([]);
      setEpisodes([]);
      setWorldSettings([]);
      setSelectedWorkId(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      if (isLocalMode) {
        applyData(setters, fetchLocalData());
      } else {
        let data = await fetchAllUserData(user.id);
        if (data.works.length === 0) {
          await seedSampleData(user.id);
          data = await fetchAllUserData(user.id);
        }
        applyData(setters, data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, [user, setters, isLocalMode]);

  useEffect(() => {
    load();
  }, [load]);

  const refresh = useCallback(async () => {
    if (!user) return;
    if (isLocalMode) {
      applyData(setters, fetchLocalData());
    } else {
      const data = await reloadUserData(user.id);
      applyData(setters, data);
    }
  }, [user, setters, isLocalMode]);

  const selectWork = useCallback(
    async (id: string | null) => {
      if (!user) return;
      setSelectedWorkId(id);
      if (isLocalMode) {
        upsertLocalSelectedWork(id);
      } else {
        await upsertSelectedWork(user.id, id);
      }
    },
    [user, isLocalMode],
  );

  const addWorkHandler = useCallback(
    async (input: WorkInput) => {
      if (!user) return;
      if (isLocalMode) {
        createLocalWork(input);
      } else {
        await createWork(user.id, input);
      }
      await refresh();
    },
    [user, refresh, isLocalMode],
  );

  const updateWorkHandler = useCallback(
    async (id: string, input: WorkInput) => {
      if (isLocalMode) {
        updateLocalWork(id, input);
      } else {
        await updateWorkRecord(id, input);
      }
      await refresh();
    },
    [refresh, isLocalMode],
  );

  const deleteWorkHandler = useCallback(
    async (id: string) => {
      if (isLocalMode) {
        deleteLocalWork(id);
      } else {
        await deleteWorkRecord(id);
      }
      if (selectedWorkId === id) {
        if (isLocalMode) {
          upsertLocalSelectedWork(null);
        } else if (user) {
          await upsertSelectedWork(user.id, null);
        }
        setSelectedWorkId(null);
      }
      await refresh();
    },
    [refresh, selectedWorkId, user, isLocalMode],
  );

  const addCharacterHandler = useCallback(
    async (payload: CharacterSubmitPayload) => {
      if (!user) return;
      if (isLocalMode) {
        await createLocalCharacter(payload);
      } else {
        await createCharacterWithImage(user.id, payload);
      }
      await refresh();
    },
    [user, refresh, isLocalMode],
  );

  const updateCharacterHandler = useCallback(
    async (id: string, payload: CharacterSubmitPayload) => {
      if (!user) return;
      const existing = characters.find((c) => c.id === id);
      if (isLocalMode) {
        await updateLocalCharacter(id, payload, existing?.imageUrl ?? null);
      } else {
        await updateCharacterWithImage(user.id, id, payload, existing?.imageUrl ?? null);
      }
      await refresh();
    },
    [user, characters, refresh, isLocalMode],
  );

  const deleteCharacterHandler = useCallback(
    async (character: Character) => {
      if (isLocalMode) {
        deleteLocalCharacter(character.id);
      } else {
        await deleteCharacterRecord(character);
      }
      await refresh();
    },
    [refresh, isLocalMode],
  );

  const addEpisodeHandler = useCallback(
    async (input: EpisodeInput) => {
      if (!user) return;
      if (isLocalMode) {
        createLocalEpisode(input);
      } else {
        await createEpisode(user.id, input);
      }
      await refresh();
    },
    [user, refresh, isLocalMode],
  );

  const updateEpisodeHandler = useCallback(
    async (id: string, input: EpisodeInput) => {
      if (isLocalMode) {
        updateLocalEpisode(id, input);
      } else {
        await updateEpisodeRecord(id, input);
      }
      await refresh();
    },
    [refresh, isLocalMode],
  );

  const deleteEpisodeHandler = useCallback(
    async (id: string) => {
      if (isLocalMode) {
        deleteLocalEpisode(id);
      } else {
        await deleteEpisodeRecord(id);
      }
      await refresh();
    },
    [refresh, isLocalMode],
  );

  const addWorldSettingHandler = useCallback(
    async (input: WorldSettingInput) => {
      if (!user) return;
      if (isLocalMode) {
        createLocalWorldSetting(input);
      } else {
        await createWorldSetting(user.id, input);
      }
      await refresh();
    },
    [user, refresh, isLocalMode],
  );

  const updateWorldSettingHandler = useCallback(
    async (id: string, input: WorldSettingInput) => {
      if (isLocalMode) {
        updateLocalWorldSetting(id, input);
      } else {
        await updateWorldSettingRecord(id, input);
      }
      await refresh();
    },
    [refresh, isLocalMode],
  );

  const deleteWorldSettingHandler = useCallback(
    async (id: string) => {
      if (isLocalMode) {
        deleteLocalWorldSetting(id);
      } else {
        await deleteWorldSettingRecord(id);
      }
      await refresh();
    },
    [refresh, isLocalMode],
  );

  const getWorkById = useCallback((id: string) => works.find((w) => w.id === id), [works]);

  const getCharactersByWorkId = useCallback(
    (workId: string) => characters.filter((c) => c.workId === workId),
    [characters],
  );

  const getEpisodesByWorkId = useCallback(
    (workId: string) =>
      episodes
        .filter((e) => e.workId === workId)
        .sort((a, b) => a.episodeNumber - b.episodeNumber),
    [episodes],
  );

  const getWorldSettingsByWorkId = useCallback(
    (workId: string) => worldSettings.filter((s) => s.workId === workId),
    [worldSettings],
  );

  const value = useMemo(
    () => ({
      loading,
      error,
      works,
      characters,
      episodes,
      worldSettings,
      selectedWorkId,
      refresh,
      selectWork,
      addWork: addWorkHandler,
      updateWork: updateWorkHandler,
      deleteWork: deleteWorkHandler,
      addCharacter: addCharacterHandler,
      updateCharacter: updateCharacterHandler,
      deleteCharacter: deleteCharacterHandler,
      addEpisode: addEpisodeHandler,
      updateEpisode: updateEpisodeHandler,
      deleteEpisode: deleteEpisodeHandler,
      addWorldSetting: addWorldSettingHandler,
      updateWorldSetting: updateWorldSettingHandler,
      deleteWorldSetting: deleteWorldSettingHandler,
      getWorkById,
      getCharactersByWorkId,
      getEpisodesByWorkId,
      getWorldSettingsByWorkId,
    }),
    [
      loading,
      error,
      works,
      characters,
      episodes,
      worldSettings,
      selectedWorkId,
      refresh,
      selectWork,
      addWorkHandler,
      updateWorkHandler,
      deleteWorkHandler,
      addCharacterHandler,
      updateCharacterHandler,
      deleteCharacterHandler,
      addEpisodeHandler,
      updateEpisodeHandler,
      deleteEpisodeHandler,
      addWorldSettingHandler,
      updateWorldSettingHandler,
      deleteWorldSettingHandler,
      getWorkById,
      getCharactersByWorkId,
      getEpisodesByWorkId,
      getWorldSettingsByWorkId,
    ],
  );

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
}

export function useStoryCore() {
  const ctx = useContext(DataContext);
  if (!ctx) throw new Error('useStoryCore must be used within DataProvider');
  return ctx;
}
