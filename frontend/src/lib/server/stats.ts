import "server-only";

import type { StatsResponse } from "@/types/api";
import { authedFetch } from "./authed";

// Personal analytics and statistics (US-15).

export function getStats(): Promise<StatsResponse> {
  return authedFetch<StatsResponse>("/stats");
}
