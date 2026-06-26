export type Work = {
  id: string;
  title: string;
  genre: string;
  oneLineSummary: string;
  synopsis: string;
  authorNote: string;
  createdAt: string;
  updatedAt: string;
};

export type WorkInput = Omit<Work, 'id' | 'createdAt' | 'updatedAt'>;
