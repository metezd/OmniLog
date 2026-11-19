import "server-only";

import type { CustomList, CustomListItem, DiaryEntry } from "@/types/api";
import { authedFetch } from "./authed";

// Custom lists (US-06) and the activity diary (US-07).

export function getLists(): Promise<CustomList[]> {
  return authedFetch<CustomList[]>("/lists");
}

export function getList(listId: number): Promise<CustomList> {
  return authedFetch<CustomList>(`/lists/${listId}`);
}

/** The name must be unique for the user. The backend answers 409 when it is not. */
export function createList(name: string): Promise<CustomList> {
  return authedFetch<CustomList>("/lists", { method: "POST", body: { name } });
}

/** The backend answers 201 for a new item and 200 when the title was already in the list. */
export function addItemToList(listId: number, mediaItemId: number): Promise<CustomListItem> {
  return authedFetch<CustomListItem>(`/lists/${listId}/items`, {
    method: "POST",
    body: { media_item_id: mediaItemId },
  });
}

/** Take a title out of a list. The title stays in the catalog and in the library. 404 when it is not in the list. */
export function removeItemFromList(listId: number, mediaItemId: number): Promise<void> {
  return authedFetch<void>(`/lists/${listId}/items/${mediaItemId}`, { method: "DELETE" });
}

/** Delete a list with its items. The titles are not touched, and the name can be used again. */
export function deleteList(listId: number): Promise<void> {
  return authedFetch<void>(`/lists/${listId}`, { method: "DELETE" });
}

/** Paging of a long list. The backend answers 422 for a limit above 500 or below 1. */
export interface PageOptions {
  /** 1 to 500. The backend default is 100 for the diary. */
  limit?: number;
  /** The number of rows to skip. The backend default is 0. */
  offset?: number;
}

/**
 * Newest first. The backend sends at most 100 events when no `limit` is given, so a screen reads
 * with a `limit` and asks for the next page with `offset` (the number of events it already has).
 * A page with fewer events than `limit` is the last one.
 */
export function getDiary({ limit, offset }: PageOptions = {}): Promise<DiaryEntry[]> {
  const query = new URLSearchParams();
  if (limit !== undefined) query.set("limit", String(limit));
  if (offset !== undefined) query.set("offset", String(offset));
  const suffix = query.size > 0 ? `?${query}` : "";
  return authedFetch<DiaryEntry[]>(`/diary${suffix}`);
}
