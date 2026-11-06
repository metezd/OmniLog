// Draft media types. Align with the FastAPI catalog schemas once confirmed.

export type MediaKind = "tv" | "game";

export type CatalogSource = "TMDB" | "IGDB";

export interface CatalogItem {
  id: string;
  title: string;
  kind: MediaKind;
  source: CatalogSource; // TMDB for series, IGDB for games
  year: number;
  rating: number; // 0-10
  summary: string;
  genres: string[];
  length: string; // e.g. "2 seasons • 18 episodes" or "~60h main story"
  imageUrl: string | null;
}