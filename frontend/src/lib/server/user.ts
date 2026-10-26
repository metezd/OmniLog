import "server-only";

import { cache } from "react";

import type { CurrentUser } from "@/types/api";
import { BackendError, backendFetch } from "./backend";
import { getSessionToken } from "./session";

/**
 * The logged-in user, or null. It never redirects, because the layout calls it on every page,
 * including the public ones. Null means: no login, a token that the backend refused, or a
 * backend that cannot be reached. The pages that need data show their own error for the last
 * case.
 *
 * cache() makes several calls during one request share one backend call.
 */
export const getCurrentUser = cache(async (): Promise<CurrentUser | null> => {
  const token = await getSessionToken();
  if (!token) return null;

  try {
    return await backendFetch<CurrentUser>("/auth/me", { token });
  } catch (error) {
    if (error instanceof BackendError) return null;
    throw error; // a mistake of the setup (BACKEND_URL) must stay visible
  }
});
