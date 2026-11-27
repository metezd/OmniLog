import "server-only";

import type { LibraryEntry, TitlePlaytimeLog, WatchStatus } from "@/types/api";
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

/**
 * Adds one playtime entry to a whole game or movie, without a chapter (#413). The total of the
 * title is the sum of all entries. A series answers 422: its time is logged on the episodes.
 */
export function logTitlePlaytime(entryId: number, minutes: number): Promise<TitlePlaytimeLog> {
  return authedFetch<TitlePlaytimeLog>(`/library/${entryId}/playtime`, {
    method: "POST",
    body: { minutes },
  });
}

/**
 * Removes the newest playtime entry of a whole game or movie (#427), for example a typing mistake.
 * Answers the library entry with the new total. 404 when the title has no such entry.
 */
export function removeLastTitlePlaytime(entryId: number): Promise<LibraryEntry> {
  return authedFetch<LibraryEntry>(`/library/${entryId}/playtime/last`, { method: "DELETE" });
}

