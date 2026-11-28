import "server-only";

import type { LibraryEntry, TitlePlaytimeLog, WatchStatus } from "@/types/api";
import { authedFetch } from "./authed";

// Library of the logged-in user (US-04, US-05). Rating is 1 to 10.

/** The largest page that the backend sends (`limit` 1 to 500). */
export const PAGE_SIZE = 500;

/**
 * The most pages that `readAllPages` reads: 20 pages of 500 are 10,000 rows (#448). A backend that
 * always answers a full page (a bug, or a user with a huge library) cannot keep a page in a loop.
 */
export const MAX_PAGES = 20;

/** The rows of a list endpoint, and whether more rows exist after the safe maximum. */
export type AllPages<T> = { rows: T[]; truncated: boolean };

/**
 * Reads every page of a list endpoint until a page is shorter than `PAGE_SIZE` (#418), at most
 * `MAX_PAGES` pages (#448). The backend sends only the first page (200 entries of the library,
 * 200 lists) when no `limit` is given, so a single call would silently miss the rest. When the
 * last allowed page is full, one more row is asked for, so `truncated` is only true when rows
 * were really left out.
 */
export async function readPages<T>(path: string): Promise<AllPages<T>> {
  const rows: T[] = [];
  for (let pages = 0; pages < MAX_PAGES; pages++) {
    const query = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(rows.length) });
    const page = await authedFetch<T[]>(`${path}?${query}`);
    rows.push(...page);
    if (page.length < PAGE_SIZE) return { rows, truncated: false };
  }
  const query = new URLSearchParams({ limit: "1", offset: String(rows.length) });
  const rest = await authedFetch<T[]>(`${path}?${query}`);
  return { rows, truncated: rest.length > 0 };
}

/** The rows of every page, up to the safe maximum (see `readPages`). */
export async function readAllPages<T>(path: string): Promise<T[]> {
  return (await readPages<T>(path)).rows;
}

/** The whole library of the user, oldest first, read page by page. */
export function getLibrary(): Promise<LibraryEntry[]> {
  return readAllPages<LibraryEntry>("/library");
}

/**
 * The whole library, and whether it is larger than the safe maximum (#448). The library page uses
 * it to tell the user that not every title is shown.
 */
export async function getFullLibrary(): Promise<{ entries: LibraryEntry[]; truncated: boolean }> {
  const { rows, truncated } = await readPages<LibraryEntry>("/library");
  return { entries: rows, truncated };
}

/** The library entry of one title, or null when the title is not in the library. One request. */
export async function getLibraryEntry(mediaItemId: number): Promise<LibraryEntry | null> {
  const query = new URLSearchParams({ media_item_id: String(mediaItemId) });
  const entries = await authedFetch<LibraryEntry[]>(`/library?${query}`);
  return entries[0] ?? null;
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

