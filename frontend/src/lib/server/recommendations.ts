import "server-only";

import type { MediaType, RecommendationItem } from "@/types/api";
import { authedFetch } from "./authed";

// Cross-media recommendations (US-13).

export function getRecommendations(target?: MediaType): Promise<RecommendationItem[]> {
  const query = target ? `?target=${encodeURIComponent(target)}` : "";
  return authedFetch<RecommendationItem[]>(`/recommendations${query}`);
}
