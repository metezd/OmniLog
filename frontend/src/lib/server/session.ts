import "server-only";

import { cookies } from "next/headers";

import { hasLiveToken, SESSION_COOKIE, tokenExpiry } from "@/lib/auth/token";

// The login token is kept in an httpOnly cookie, so the JavaScript of the page can never read it.
// Only server code (Server Actions and Server Components) reads it and sends it to the backend.

// Both live in a file without server-only code, because the proxy needs them too. They are
// exported again here, so the server code keeps one place to import from.
export { SESSION_COOKIE, tokenExpiry };

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
  // The browser removes the cookie when it ends. This also covers a cookie that is still sent
  // a moment too long.
  return hasLiveToken(token) ? token : undefined;
}

/** Log out: remove the session cookie. Only works in a Server Action or a Route Handler. */
export async function destroySession(): Promise<void> {
  (await cookies()).delete(SESSION_COOKIE);
}
