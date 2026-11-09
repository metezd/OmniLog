import "server-only";

import type { ErrorKind } from "@/types/state";
import { BackendError } from "./backend";

/** What a page shows when a backend call failed. */
export type ErrorState = {
  kind: ErrorKind;
  message: string;
};

/**
 * Turn a failed backend call into something a page can show. Use it in the catch block of a
 * Server Component:
 *
 *   try { data = await getLibrary(); } catch (error) { state = toErrorState(error); }
 *
 * Anything that is not a BackendError is thrown again. That keeps redirect() (used by
 * authedFetch for 401) and mistakes of the setup working.
 */
export function toErrorState(error: unknown): ErrorState {
  if (!(error instanceof BackendError)) throw error;

  if (error.status === 404) {
    return { kind: "not_found", message: "We could not find what you were looking for." };
  }
  if (error.status === 0 || error.status === 503) {
    return { kind: "unavailable", message: "The data service is not available right now. Please try again." };
  }
  // The text of a server error is not for the user
  return { kind: "error", message: "Something went wrong. Please try again." };
}
