import "server-only";

import type { MediaItem, MediaType } from "@/types/api";
import { authedFetch } from "./authed";

// Cross-media recommendations (US-13). The backend requires `target` (returns 422 without it).

export function getRecommendations(target: MediaType, limit?: number): Promise<MediaItem[]> {
  const params = new URLSearchParams({ target });
  if (limit !== undefined) params.set("limit", String(limit));
  return authedFetch<MediaItem[]>(`/recommendations?${params}`);
}
