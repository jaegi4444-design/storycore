import { useCallback } from 'react';
import type { Work, WorkInput } from '../types/work';
import { generateId, nowISO } from '../utils/id';
import { STORAGE_KEYS } from '../utils/storageKeys';
import { useLocalStorage } from './useLocalStorage';

export function useWorks() {
  const [works, setWorks] = useLocalStorage<Work[]>(STORAGE_KEYS.works, []);

  const addWork = useCallback(
    (input: WorkInput) => {
      const now = nowISO();
      const work: Work = { ...input, id: generateId(), createdAt: now, updatedAt: now };
      setWorks((prev) => [...prev, work]);
      return work;
    },
    [setWorks],
  );

  const updateWork = useCallback(
    (id: string, input: WorkInput) => {
      setWorks((prev) =>
        prev.map((w) =>
          w.id === id ? { ...w, ...input, updatedAt: nowISO() } : w,
        ),
      );
    },
    [setWorks],
  );

  const deleteWork = useCallback(
    (id: string) => {
      setWorks((prev) => prev.filter((w) => w.id !== id));
    },
    [setWorks],
  );

  const getWorkById = useCallback(
    (id: string) => works.find((w) => w.id === id),
    [works],
  );

  return { works, addWork, updateWork, deleteWork, getWorkById };
}
