import { useCallback } from 'react';
import type { Episode, EpisodeInput } from '../types/episode';
import { generateId, nowISO } from '../utils/id';
import { STORAGE_KEYS } from '../utils/storageKeys';
import { useLocalStorage } from './useLocalStorage';

export function useEpisodes() {
  const [episodes, setEpisodes] = useLocalStorage<Episode[]>(
    STORAGE_KEYS.episodes,
    [],
  );

  const addEpisode = useCallback(
    (input: EpisodeInput) => {
      const now = nowISO();
      const episode: Episode = {
        ...input,
        id: generateId(),
        createdAt: now,
        updatedAt: now,
      };
      setEpisodes((prev) => [...prev, episode]);
      return episode;
    },
    [setEpisodes],
  );

  const updateEpisode = useCallback(
    (id: string, input: EpisodeInput) => {
      setEpisodes((prev) =>
        prev.map((e) =>
          e.id === id ? { ...e, ...input, updatedAt: nowISO() } : e,
        ),
      );
    },
    [setEpisodes],
  );

  const deleteEpisode = useCallback(
    (id: string) => {
      setEpisodes((prev) => prev.filter((e) => e.id !== id));
    },
    [setEpisodes],
  );

  const getEpisodesByWorkId = useCallback(
    (workId: string) =>
      episodes
        .filter((e) => e.workId === workId)
        .sort((a, b) => a.episodeNumber - b.episodeNumber),
    [episodes],
  );

  const getEpisodeById = useCallback(
    (id: string) => episodes.find((e) => e.id === id),
    [episodes],
  );

  return {
    episodes,
    addEpisode,
    updateEpisode,
    deleteEpisode,
    getEpisodesByWorkId,
    getEpisodeById,
  };
}
