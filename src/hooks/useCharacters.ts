import { useCallback } from 'react';
import type { Character, CharacterInput } from '../types/character';
import { generateId, nowISO } from '../utils/id';
import { STORAGE_KEYS } from '../utils/storageKeys';
import { useLocalStorage } from './useLocalStorage';

export function useCharacters() {
  const [characters, setCharacters] = useLocalStorage<Character[]>(
    STORAGE_KEYS.characters,
    [],
  );

  const addCharacter = useCallback(
    (input: CharacterInput) => {
      const now = nowISO();
      const character: Character = {
        ...input,
        id: generateId(),
        createdAt: now,
        updatedAt: now,
      };
      setCharacters((prev) => [...prev, character]);
      return character;
    },
    [setCharacters],
  );

  const updateCharacter = useCallback(
    (id: string, input: CharacterInput) => {
      setCharacters((prev) =>
        prev.map((c) =>
          c.id === id ? { ...c, ...input, updatedAt: nowISO() } : c,
        ),
      );
    },
    [setCharacters],
  );

  const deleteCharacter = useCallback(
    (id: string) => {
      setCharacters((prev) => prev.filter((c) => c.id !== id));
    },
    [setCharacters],
  );

  const getCharactersByWorkId = useCallback(
    (workId: string) => characters.filter((c) => c.workId === workId),
    [characters],
  );

  const getCharacterById = useCallback(
    (id: string) => characters.find((c) => c.id === id),
    [characters],
  );

  return {
    characters,
    addCharacter,
    updateCharacter,
    deleteCharacter,
    getCharactersByWorkId,
    getCharacterById,
  };
}
