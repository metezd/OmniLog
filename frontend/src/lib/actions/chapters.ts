"use server";

import { revalidatePath } from "next/cache";

import { logPlaytime, rateChapter, recordDecision } from "@/lib/server/chapters";
import { BackendError } from "@/lib/server/backend";
import { toErrorState } from "@/lib/server/error-state";

export type ChapterActionState =
  | { status: "idle" }
  | { status: "saved"; message: string }
  | { status: "error"; message: string };

function rethrowIfRedirect(error: unknown): void {
  const digest = (error as { digest?: unknown } | null)?.digest;
  if (typeof digest === "string" && digest.startsWith("NEXT_REDIRECT")) throw error;
}

/**
 * The message for a failed change (#411). A rule of the backend (422) is shown as it is, for
 * example that the total is too large. When the backend did not answer in time the change may
 * still be saved, so the user is asked to reload first instead of trying again at once.
 */
function chapterErrorMessage(error: unknown): string {
  if (error instanceof BackendError) {
    if (error.status === 422 && error.message) return error.message;
    if (error.status === 0 && error.cause instanceof DOMException && error.cause.name === "TimeoutError") {
      return "The server took too long to answer. Reload the page to see if it was saved before you try again.";
    }
  }
  return toErrorState(error).message;
}

/** Rates a chapter or episode from 1 to 5 stars (US-10). */
export async function rateChapterAction(
  _previous: ChapterActionState,
  formData: FormData,
): Promise<ChapterActionState> {
  const entryId = Number(formData.get("entryId"));
  const chapterId = Number(formData.get("chapterId"));
  const mediaItemId = Number(formData.get("mediaItemId"));
  const rating = Number(formData.get("rating"));

  if (!Number.isInteger(entryId) || !Number.isInteger(chapterId) || rating < 1 || rating > 5) {
    return { status: "error", message: "Rating must be between 1 and 5 stars." };
  }

  try {
    await rateChapter(entryId, chapterId, rating);
  } catch (error) {
    rethrowIfRedirect(error);
    return { status: "error", message: chapterErrorMessage(error) };
  }

  revalidatePath("/diary");
  if (Number.isInteger(mediaItemId) && mediaItemId > 0) {
    revalidatePath(`/title/${mediaItemId}`);
  }
  return { status: "saved", message: `Rated ${rating}/5 ★` };
}

/** Logs playtime in minutes for a chapter or episode (US-11). */
export async function logPlaytimeAction(
  _previous: ChapterActionState,
  formData: FormData,
): Promise<ChapterActionState> {
  const entryId = Number(formData.get("entryId"));
  const chapterId = Number(formData.get("chapterId"));
  const mediaItemId = Number(formData.get("mediaItemId"));
  const minutes = Number(formData.get("minutes"));

  if (!Number.isInteger(entryId) || !Number.isInteger(chapterId) || !Number.isInteger(minutes) || minutes <= 0) {
    return { status: "error", message: "Playtime must be a positive number of minutes." };
  }

  try {
    await logPlaytime(entryId, chapterId, minutes);
  } catch (error) {
    rethrowIfRedirect(error);
    return { status: "error", message: chapterErrorMessage(error) };
  }

  revalidatePath("/diary");
  revalidatePath("/stats");
  if (Number.isInteger(mediaItemId) && mediaItemId > 0) {
    revalidatePath(`/title/${mediaItemId}`);
  }
  return { status: "saved", message: `+${minutes}m logged` };
}

/** Records a branching narrative decision for a chapter (US-12). */
export async function recordDecisionAction(
  _previous: ChapterActionState,
  formData: FormData,
): Promise<ChapterActionState> {
  const entryId = Number(formData.get("entryId"));
  const chapterId = Number(formData.get("chapterId"));
  const mediaItemId = Number(formData.get("mediaItemId"));
  const choice = String(formData.get("choice") ?? "").trim();
  const dpRaw = formData.get("decisionPointId");
  const decisionPointId = dpRaw ? Number(dpRaw) : undefined;

  if (!Number.isInteger(entryId) || !Number.isInteger(chapterId) || !choice) {
    return { status: "error", message: "Please select a valid narrative choice." };
  }

  try {
    await recordDecision(entryId, chapterId, choice, decisionPointId);
  } catch (error) {
    rethrowIfRedirect(error);
    return { status: "error", message: chapterErrorMessage(error) };
  }

  revalidatePath("/diary");
  if (Number.isInteger(mediaItemId) && mediaItemId > 0) {
    revalidatePath(`/title/${mediaItemId}`);
  }
  return { status: "saved", message: `Choice "${choice}" saved` };
}
