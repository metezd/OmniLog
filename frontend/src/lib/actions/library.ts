"use server";

import { revalidatePath } from "next/cache";

import { toErrorState } from "@/lib/server/error-state";
import { addToLibrary, removeFromLibrary, updateLibraryEntry } from "@/lib/server/library";
import { submitReview } from "@/lib/server/reviews";
import type { Review, WatchStatus } from "@/types/api";

export type AddToLibraryState =
  | { status: "idle" }
  | { status: "added" }
  | { status: "error"; message: string };

export type ActionState =
  | { status: "idle" }
  | { status: "saved"; message?: string }
  | { status: "error"; message: string };

export type ReviewActionState =
  | { status: "idle"; review?: Review | null }
  | { status: "saved"; review: Review }
  | { status: "error"; message: string };

const VALID_STATUSES: WatchStatus[] = ["WATCHING", "COMPLETED", "PLAN_TO_WATCH", "DROPPED"];

function rethrowIfRedirect(error: unknown): void {
  const digest = (error as { digest?: unknown } | null)?.digest;
  if (typeof digest === "string" && digest.startsWith("NEXT_REDIRECT")) throw error;
}

/** Adds one catalog title to the library of the logged-in user. Used by the Search page. */
export async function addToLibraryAction(
  _previous: AddToLibraryState,
  formData: FormData,
): Promise<AddToLibraryState> {
  const mediaItemId = Number(formData.get("mediaItemId"));
  if (!Number.isInteger(mediaItemId) || mediaItemId <= 0) {
    return { status: "error", message: "This title could not be added." };
  }

  try {
    await addToLibrary({ mediaItemId, status: "PLAN_TO_WATCH" });
  } catch (error) {
    rethrowIfRedirect(error);
    return { status: "error", message: toErrorState(error).message };
  }

  revalidatePath("/search");
  revalidatePath("/library");
  revalidatePath("/recommendations");
  revalidatePath(`/title/${mediaItemId}`);
  return { status: "added" };
}

/** Updates watch status and/or rating (1-10) for a library entry (US-04, US-05). */
export async function updateLibraryEntryAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const entryId = Number(formData.get("entryId"));
  const mediaItemId = Number(formData.get("mediaItemId"));
  const statusRaw = String(formData.get("status") ?? "");
  const ratingRaw = String(formData.get("rating") ?? "").trim();

  if (!Number.isInteger(entryId) || entryId <= 0) {
    return { status: "error", message: "Invalid library entry." };
  }

  const status = VALID_STATUSES.find((s) => s === statusRaw);
  let rating: number | null | undefined = undefined;
  if (ratingRaw === "") {
    rating = null;
  } else {
    const parsed = Number(ratingRaw);
    if (!Number.isInteger(parsed) || parsed < 1 || parsed > 10) {
      return { status: "error", message: "Rating must be between 1 and 10." };
    }
    rating = parsed;
  }

  try {
    await updateLibraryEntry(entryId, { status, rating });
  } catch (error) {
    rethrowIfRedirect(error);
    return { status: "error", message: toErrorState(error).message };
  }

  revalidatePath("/library");
  revalidatePath("/diary");
  revalidatePath("/stats");
  if (Number.isInteger(mediaItemId) && mediaItemId > 0) {
    revalidatePath(`/title/${mediaItemId}`);
  }
  return { status: "saved", message: "Library entry updated." };
}

/** Removes a title from the user's library (US-04). */
export async function removeLibraryEntryAction(formData: FormData): Promise<void> {
  const entryId = Number(formData.get("entryId"));
  const mediaItemId = Number(formData.get("mediaItemId"));
  if (!Number.isInteger(entryId) || entryId <= 0) return;

  try {
    await removeFromLibrary(entryId);
  } catch (error) {
    rethrowIfRedirect(error);
    return;
  }

  revalidatePath("/library");
  revalidatePath("/diary");
  revalidatePath("/stats");
  if (Number.isInteger(mediaItemId) && mediaItemId > 0) {
    revalidatePath(`/title/${mediaItemId}`);
  }
}

/** Submits a user review and runs automated NLP spoiler moderation (US-14). */
export async function submitReviewAction(
  _previous: ReviewActionState,
  formData: FormData,
): Promise<ReviewActionState> {
  const entryId = Number(formData.get("entryId"));
  const mediaItemId = Number(formData.get("mediaItemId"));
  const text = String(formData.get("text") ?? "").trim();

  if (!Number.isInteger(entryId) || entryId <= 0) {
    return { status: "error", message: "Invalid library entry." };
  }
  if (!text) {
    return { status: "error", message: "Review text cannot be empty." };
  }

  let review: Review;
  try {
    review = await submitReview(entryId, text);
  } catch (error) {
    rethrowIfRedirect(error);
    return { status: "error", message: toErrorState(error).message };
  }

  revalidatePath("/diary");
  if (Number.isInteger(mediaItemId) && mediaItemId > 0) {
    revalidatePath(`/title/${mediaItemId}`);
  }
  return { status: "saved", review };
}