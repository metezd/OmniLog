import "server-only";

import type { MediaDetail, MediaItem, MediaType } from "@/types/api";
import { authedFetch } from "./authed";

// Catalog search and title details (US-08, US-09).

/** Every result is saved in the catalog and has an id, so it can be added to the library. */
export function searchCatalog(query: string, type: MediaType): Promise<MediaItem[]> {
  const params = new URLSearchParams({ q: query, type });
  return authedFetch<MediaItem[]>(`/catalog/search?${params}`);
}

export function getTitleDetails(mediaId: number): Promise<MediaDetail> {
  return authedFetch<MediaDetail>(`/catalog/${mediaId}`);
}
