"use server";

import { revalidatePath } from "next/cache";

import { formatPlaytime } from "@/lib/media";
import { BackendError } from "@/lib/server/backend";
import { toErrorState } from "@/lib/server/error-state";
import {
  addToLibrary,
  logTitlePlaytime,
  removeFromLibrary,
  updateLibraryEntry,
} from "@/lib/server/library";
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

export type ReviewErrorCode = "validation" | "not_found" | "unavailable" | "error";

export type ReviewActionState =
  | { status: "idle"; review?: Review | null }
  | { status: "saved"; review: Review }
  | {
      status: "error";
      code: ReviewErrorCode;
      message: string;
      review?: Review | null;
      draft?: string;
    };

const VALID_STATUSES: WatchStatus[] = ["IN_PROGRESS", "COMPLETED", "PLAN_TO_WATCH", "DROPPED"];

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

// One entry is at most 100,000 minutes, like the limit of the backend (PlaytimeCreate)
const MAX_SESSION_MINUTES = 100_000;

function wholeNumber(raw: FormDataEntryValue | null): number | null {
  const text = String(raw ?? "").trim();
  if (text === "") return 0;
  const value = Number(text);
  return Number.isInteger(value) && value >= 0 ? value : null;
}

/** Logs one playtime session of a whole game or movie in hours and minutes (US-11, #413). */
export async function logTitlePlaytimeAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const entryId = Number(formData.get("entryId"));
  const mediaItemId = Number(formData.get("mediaItemId"));
  const hours = wholeNumber(formData.get("hours"));
  const minutesPart = wholeNumber(formData.get("minutes"));

  if (!Number.isInteger(entryId) || entryId <= 0) {
    return { status: "error", message: "Invalid library entry." };
  }
  if (hours === null || minutesPart === null) {
    return { status: "error", message: "Hours and minutes must be whole numbers." };
  }
  const minutes = hours * 60 + minutesPart;
  if (minutes <= 0) {
    return { status: "error", message: "Playtime must be at least 1 minute." };
  }
  if (minutes > MAX_SESSION_MINUTES) {
    return { status: "error", message: "One session can be at most 100,000 minutes." };
  }

  try {
    await logTitlePlaytime(entryId, minutes);
  } catch (error) {
    rethrowIfRedirect(error);
    return { status: "error", message: toErrorState(error).message };
  }

  revalidatePath("/diary");
  revalidatePath("/stats");
  revalidatePath("/library");
  if (Number.isInteger(mediaItemId) && mediaItemId > 0) {
    revalidatePath(`/title/${mediaItemId}`);
  }
  return { status: "saved", message: `+${formatPlaytime(minutes)} logged` };
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
  previous: ReviewActionState,
  formData: FormData,
): Promise<ReviewActionState> {
  const entryId = Number(formData.get("entryId"));
  const mediaItemId = Number(formData.get("mediaItemId"));
  const rawText = String(formData.get("text") ?? "");
  const text = rawText.trim();
  const previousReview = previous.review ?? null;

  if (!Number.isInteger(entryId) || entryId <= 0) {
    return {
      status: "error",
      code: "not_found",
      message: "This title or library entry could not be found.",
      review: previousReview,
      draft: rawText,
    };
  }
  if (!text) {
    return {
      status: "error",
      code: "validation",
      message: "Review text cannot be empty.",
      review: previousReview,
      draft: rawText,
    };
  }

  let review: Review;
  try {
    review = await submitReview(entryId, text);
  } catch (error) {
    rethrowIfRedirect(error);
    if (error instanceof BackendError) {
      if (error.status === 404) {
        return {
          status: "error",
          code: "not_found",
          message: "This title or library entry could not be found.",
          review: previousReview,
          draft: rawText,
        };
      }
      if (error.status === 422) {
        const validationMessage =
          error.fieldErrors.text ??
          Object.values(error.fieldErrors)[0] ??
          error.message;
        return {
          status: "error",
          code: "validation",
          message: validationMessage || "Review text cannot be empty.",
          review: previousReview,
          draft: rawText,
        };
      }
      if (error.status === 503) {
        return {
          status: "error",
          code: "unavailable",
          message:
            "The AI moderation service is unavailable right now. Your review was not saved. Please try again.",
          review: previousReview,
          draft: rawText,
        };
      }
      if (error.status === 0) {
        return {
          status: "error",
          code: "unavailable",
          message:
            "The server could not be reached. Your review was not saved. Please try again.",
          review: previousReview,
          draft: rawText,
        };
      }
    }
    return {
      status: "error",
      code: "error",
      message: toErrorState(error).message,
      review: previousReview,
      draft: rawText,
    };
  }

  revalidatePath("/diary");
  if (Number.isInteger(mediaItemId) && mediaItemId > 0) {
    revalidatePath(`/title/${mediaItemId}`);
  }
  return { status: "saved", review };
}