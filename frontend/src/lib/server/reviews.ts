import "server-only";

import type { Review } from "@/types/api";
import { authedFetch } from "./authed";

// Library entry reviews and spoiler moderation (US-14).

export function getReview(entryId: number): Promise<Review | null> {
  return authedFetch<Review | null>(`/library/${entryId}/review`);
}

export function submitReview(entryId: number, text: string): Promise<Review> {
  return authedFetch<Review>(`/library/${entryId}/review`, {
    method: "POST",
    body: { text },
  });
}
