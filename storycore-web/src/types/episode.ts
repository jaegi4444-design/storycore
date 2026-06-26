export type Episode = {
  id: string;
  workId: string;

  episodeNumber: number;
  title: string;
  summary: string;

  characterIds: string[];
  locations: string[];

  revealedSettings: string;
  foreshadows: string;
  resolvedForeshadows: string;

  draft: string;
  authorNote: string;

  createdAt: string;
  updatedAt: string;
};

export type EpisodeInput = Omit<Episode, 'id' | 'createdAt' | 'updatedAt'>;
