export interface KnowledgeEntryDTO {
    id: number;
    name: string;
    area: string;
    areaSecondary?: string;
    status: string;
    technologies: any[]; // O tipado estricto si ya lo tienes
    hasCoverImage: boolean;
  }