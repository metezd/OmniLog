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

/** Newest first. */
export function getDiary(): Promise<DiaryEntry[]> {
  return authedFetch<DiaryEntry[]>("/diary");
}
