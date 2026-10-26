import "server-only";

import { cookies } from "next/headers";

// The login token is kept in an httpOnly cookie, so the JavaScript of the page can never read it.
// Only server code (Server Actions and Server Components) reads it and sends it to the backend.

export const SESSION_COOKIE = "omnilog_session";

/**
 * When a login token ends, read from its exp claim. Returns null when the token has no readable
 * end time.
 *
 * The signature is NOT checked here. Only the backend can do that, and it does on every call.
 * The date is only used to give the cookie the same lifetime as the token.
 */
export function tokenExpiry(token: string): Date | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    const claims: unknown = JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8"));
    const exp = typeof claims === "object" && claims !== null ? (claims as { exp?: unknown }).exp : undefined;
    return typeof exp === "number" && Number.isFinite(exp) && exp > 0 ? new Date(exp * 1000) : null;
  } catch {
    return null;
  }
}

/**
 * Save the login token in the session cookie. The cookie ends when the token ends. A token
 * without a readable end time gives a cookie that ends when the browser is closed.
 *
 * Only works in a Server Action or a Route Handler, because Next.js cannot set cookies while a
 * page is rendered.
 */
export async function createSession(token: string): Promise<void> {
  const expiry = tokenExpiry(token);
  // maxAge counts from the moment the browser gets the cookie, so a wrong clock on the
  // computer of the user cannot make the cookie live too long or too short
  const maxAge = expiry ? Math.floor((expiry.getTime() - Date.now()) / 1000) : undefined;
  if (maxAge !== undefined && maxAge <= 0) {
    throw new Error("The login token has already expired");
  }

  const cookieStore = await cookies();
  cookieStore.set(SESSION_COOKIE, token, {
    httpOnly: true,
    // Plain http://localhost must work in development
    secure: process.env.NODE_ENV === "production",
    // The cookie is sent when the user follows a link to the site, and not with a form or a
    // request from another site
    sameSite: "lax",
    path: "/",
    ...(maxAge === undefined ? {} : { maxAge }),
  });
}

/** The login token of this request, or undefined when nobody is logged in. */
export async function getSessionToken(): Promise<string | undefined> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return undefined;

  // The browser removes the cookie when it ends. This also covers a cookie that is still sent
  // a moment too long.
  const expiry = tokenExpiry(token);
  if (expiry && expiry.getTime() <= Date.now()) return undefined;

  return token;
}

/** Log out: remove the session cookie. Only works in a Server Action or a Route Handler. */
export async function destroySession(): Promise<void> {
  (await cookies()).delete(SESSION_COOKIE);
}
