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
