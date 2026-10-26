// Which pages need a login. The proxy reads this list, so a new protected page is added here only.

export const LOGIN_PATH = "/login";

/** Where a request goes when the backend says the token is not valid anymore. */
export const SESSION_EXPIRED_PATH = "/session-expired";

/** A page is protected when its path is one of these or starts with one of these plus a slash. */
export const PROTECTED_PREFIXES = [
  "/library",
  "/search",
  "/title",
  "/lists",
  "/diary",
  "/recommendations",
  "/stats",
  "/profile",
] as const;

export function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}
