"use server";

import { revalidatePath } from "next/cache";

import { toErrorState } from "@/lib/server/error-state";
import { addToLibrary } from "@/lib/server/library";

export type AddToLibraryState =
  | { status: "idle" }
  | { status: "added" }
  | { status: "error"; message: string };

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
    // A redirect (for example to the session-expired route) must not be swallowed
    const digest = (error as { digest?: unknown } | null)?.digest;
    if (typeof digest === "string" && digest.startsWith("NEXT_REDIRECT")) throw error;
    return { status: "error", message: toErrorState(error).message };
  }

  revalidatePath("/search");
  revalidatePath("/library");
  return { status: "added" };
}