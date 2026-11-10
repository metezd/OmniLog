"use server";

import { revalidatePath } from "next/cache";

import { toErrorState } from "@/lib/server/error-state";
import { addItemToList, createList, deleteList, removeItemFromList } from "@/lib/server/journal";

export type ListActionState =
  | { status: "idle" }
  | { status: "saved"; message?: string }
  | { status: "error"; message: string };

function rethrowIfRedirect(error: unknown): void {
  const digest = (error as { digest?: unknown } | null)?.digest;
  if (typeof digest === "string" && digest.startsWith("NEXT_REDIRECT")) throw error;
}

/** Creates a custom list for the logged-in user (US-06). */
export async function createListAction(
  _previous: ListActionState,
  formData: FormData,
): Promise<ListActionState> {
  const name = String(formData.get("name") ?? "").trim();
  if (!name) {
    return { status: "error", message: "List name cannot be empty." };
  }

  try {
    await createList(name);
  } catch (error) {
    rethrowIfRedirect(error);
    return { status: "error", message: toErrorState(error).message };
  }

  revalidatePath("/lists");
  revalidatePath("/diary");
  return { status: "saved", message: `Created "${name}".` };
}

/** Deletes a custom list (US-06). */
export async function deleteListAction(formData: FormData): Promise<void> {
  const listId = Number(formData.get("listId"));
  if (!Number.isInteger(listId) || listId <= 0) return;

  try {
    await deleteList(listId);
  } catch (error) {
    rethrowIfRedirect(error);
    return;
  }

  revalidatePath("/lists");
  revalidatePath("/diary");
}

/** Adds a catalog/library item to a custom list (US-06). */
export async function addItemToListAction(
  _previous: ListActionState,
  formData: FormData,
): Promise<ListActionState> {
  const listId = Number(formData.get("listId"));
  const mediaItemId = Number(formData.get("mediaItemId"));

  if (!Number.isInteger(listId) || listId <= 0 || !Number.isInteger(mediaItemId) || mediaItemId <= 0) {
    return { status: "error", message: "Please select a title to add." };
  }

  try {
    await addItemToList(listId, mediaItemId);
  } catch (error) {
    rethrowIfRedirect(error);
    return { status: "error", message: toErrorState(error).message };
  }

  revalidatePath("/lists");
  revalidatePath(`/lists/${listId}`);
  revalidatePath("/diary");
  return { status: "saved", message: "Title added to list." };
}

/** Removes a title from a custom list (US-06). */
export async function removeItemFromListAction(formData: FormData): Promise<void> {
  const listId = Number(formData.get("listId"));
  const mediaItemId = Number(formData.get("mediaItemId"));
  if (!Number.isInteger(listId) || listId <= 0 || !Number.isInteger(mediaItemId) || mediaItemId <= 0) return;

  try {
    await removeItemFromList(listId, mediaItemId);
  } catch (error) {
    rethrowIfRedirect(error);
    return;
  }

  revalidatePath("/lists");
  revalidatePath(`/lists/${listId}`);
  revalidatePath("/diary");
}
