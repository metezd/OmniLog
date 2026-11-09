// Plain helpers for the login token and its cookie. They hold no secrets and use no server-only
// API, so both the proxy and the server code can import them.

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
 * True when there is a token that has not ended yet. A token without a readable end time counts
 * as live, because the backend is the one that decides. This is an optimistic check for redirects,
 * never a proof that the user may see data.
 */
export function hasLiveToken(token: string | undefined | null): token is string {
  if (!token) return false;
  const expiry = tokenExpiry(token);
  return expiry === null || expiry.getTime() > Date.now();
}
