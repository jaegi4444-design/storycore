import { useCallback } from 'react';
import type { WorldSetting, WorldSettingInput } from '../types/worldSetting';
import { generateId, nowISO } from '../utils/id';
import { STORAGE_KEYS } from '../utils/storageKeys';
import { useLocalStorage } from './useLocalStorage';

export function useWorldSettings() {
  const [worldSettings, setWorldSettings] = useLocalStorage<WorldSetting[]>(
    STORAGE_KEYS.worldSettings,
    [],
  );

  const addWorldSetting = useCallback(
    (input: WorldSettingInput) => {
      const now = nowISO();
      const setting: WorldSetting = {
        ...input,
        id: generateId(),
        createdAt: now,
        updatedAt: now,
      };
      setWorldSettings((prev) => [...prev, setting]);
      return setting;
    },
    [setWorldSettings],
  );

  const updateWorldSetting = useCallback(
    (id: string, input: WorldSettingInput) => {
      setWorldSettings((prev) =>
        prev.map((s) =>
          s.id === id ? { ...s, ...input, updatedAt: nowISO() } : s,
        ),
      );
    },
    [setWorldSettings],
  );

  const deleteWorldSetting = useCallback(
    (id: string) => {
      setWorldSettings((prev) => prev.filter((s) => s.id !== id));
    },
    [setWorldSettings],
  );

  const getWorldSettingsByWorkId = useCallback(
    (workId: string) => worldSettings.filter((s) => s.workId === workId),
    [worldSettings],
  );

  const getWorldSettingById = useCallback(
    (id: string) => worldSettings.find((s) => s.id === id),
    [worldSettings],
  );

  return {
    worldSettings,
    addWorldSetting,
    updateWorldSetting,
    deleteWorldSetting,
    getWorldSettingsByWorkId,
    getWorldSettingById,
  };
}
