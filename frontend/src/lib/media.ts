import type { MediaType, WatchStatus } from "@/types/api";

export const STATUS_LABELS: Record<WatchStatus, string> = {
  PLAN_TO_WATCH: "Plan to watch",
  IN_PROGRESS: "In progress",
  COMPLETED: "Completed",
  DROPPED: "Dropped",
};

export const MEDIA_TYPE_LABELS: Record<MediaType, string> = {
  GAME: "Game",
  SERIES: "TV Series",
  MOVIE: "Movie",
};

/** The year at the start of a release date such as "2015-01-30", or null. */
export function releaseYear(releaseDate: string | null): string | null {
  const match = releaseDate?.match(/^\d{4}/);
  return match ? match[0] : null;
}
