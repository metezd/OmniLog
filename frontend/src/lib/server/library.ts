import "server-only";

import type { LibraryEntry, WatchStatus } from "@/types/api";
import { authedFetch } from "./authed";

// Library of the logged-in user (US-04, US-05). Rating is 1 to 10.

export function getLibrary(): Promise<LibraryEntry[]> {
  return authedFetch<LibraryEntry[]>("/library");
}

export function addToLibrary(input: {
  mediaItemId: number;
  status?: WatchStatus;
  rating?: number | null;
}): Promise<LibraryEntry> {
  return authedFetch<LibraryEntry>("/library", {
    method: "POST",
    body: { media_item_id: input.mediaItemId, status: input.status, rating: input.rating },
  });
}

/** Omitted fields stay as they are. A rating of null clears the rating. */
export function updateLibraryEntry(
  entryId: number,
  changes: { status?: WatchStatus; rating?: number | null },
): Promise<LibraryEntry> {
  return authedFetch<LibraryEntry>(`/library/${entryId}`, { method: "PATCH", body: changes });
}

/**
 * Remove a title from the library. The chapter ratings, playtime and decisions that the user
 * logged for it are deleted with it, so ask the user to confirm before calling this. The backend
 * answers 404 when the entry does not exist or was already removed.
 */
export function removeFromLibrary(entryId: number): Promise<void> {
  return authedFetch<void>(`/library/${entryId}`, { method: "DELETE" });
}
