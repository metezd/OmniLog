import "server-only";

import { redirect } from "next/navigation";

import { LOGIN_PATH, SESSION_EXPIRED_PATH } from "@/lib/auth/routes";
import { BackendError, backendFetch, type BackendFetchOptions } from "./backend";
import { getSessionToken } from "./session";

/**
 * Call the backend for the logged-in user. This is the one way that Server Components and Server
 * Actions reach the protected endpoints.
 *
 * - No login (or an ended token): the user goes to the login page.
 * - The backend answers 401: the token is not valid anymore, so the user goes to /session-expired.
 *   That route removes the cookie, which a page cannot do while it is rendered.
 * - Any other failure is thrown as a BackendError, for the page to show (see error-state.ts).
 *
 * redirect() works by throwing, so a caller that catches errors must let it pass. toErrorState()
 * does that.
 */
export async function authedFetch<T = unknown>(
  path: string,
  options: Omit<BackendFetchOptions, "token"> = {},
): Promise<T> {
  const token = await getSessionToken();
  if (!token) redirect(LOGIN_PATH);

  try {
    return await backendFetch<T>(path, { ...options, token });
  } catch (error) {
    if (error instanceof BackendError && error.status === 401) redirect(SESSION_EXPIRED_PATH);
    throw error;
  }
}
