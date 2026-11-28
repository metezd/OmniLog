import "server-only";

import type { Review } from "@/types/api";
import { authedFetch } from "./authed";
import { BackendError } from "./backend";

// Library entry reviews and spoiler moderation (US-14).

export async function getReview(entryId: number): Promise<Review | null> {
  try {
    return await authedFetch<Review | null>(`/library/${entryId}/review`);
  } catch (error) {
    // The backend returns 404 "Review not found" when an entry has no review yet,
    // while 404 "Library entry not found" means the entry itself is missing.
    if (error instanceof BackendError && error.status === 404 && error.message !== "Library entry not found") {
      return null;
    }
    throw error;
  }
}

export function submitReview(entryId: number, text: string): Promise<Review> {
  return authedFetch<Review>(`/library/${entryId}/review`, {
    method: "POST",
    body: { text },
  });
}

/** Removes the review of a library entry (#427). 404 when there is no review. */
export function deleteReview(entryId: number): Promise<void> {
  return authedFetch<void>(`/library/${entryId}/review`, { method: "DELETE" });
}

