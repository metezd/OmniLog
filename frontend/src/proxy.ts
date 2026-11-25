import { NextResponse, type NextRequest } from "next/server";

import { isProtectedPath, LOGIN_PATH } from "@/lib/auth/routes";
import { hasLiveToken, SESSION_COOKIE } from "@/lib/auth/token";

// Images come from this site (the poster proxy /api/poster), data: and blob: URLs, and the two
// image hosts that the backend allows in poster_url (#218, #303).
const IMAGE_SOURCES = ["'self'", "data:", "blob:", "https://image.tmdb.org", "https://images.igdb.com"];

/**
 * The Content-Security-Policy of every page (#303).
 *
 * Scripts need the nonce of this request. Next.js reads the policy from the request headers and
 * puts the nonce on its own scripts, so no 'unsafe-inline' is needed for scripts. 'strict-dynamic'
 * lets a trusted script load the chunks it needs. Styles keep 'unsafe-inline', because React and
 * Next.js write style attributes. The development server also needs eval and its websocket.
 */
export function contentSecurityPolicy(nonce: string, development = process.env.NODE_ENV === "development"): string {
  const directives: Record<string, string[]> = {
    "default-src": ["'self'"],
    "script-src": ["'self'", `'nonce-${nonce}'`, "'strict-dynamic'", ...(development ? ["'unsafe-eval'"] : [])],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": IMAGE_SOURCES,
    "font-src": ["'self'"],
    "connect-src": ["'self'", ...(development ? ["ws:"] : [])],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
  };
  return Object.entries(directives)
    .map(([name, values]) => `${name} ${values.join(" ")}`)
    .join("; ");
}

/** CSP_REPORT_ONLY=true sends the policy as Content-Security-Policy-Report-Only, to try a change. */
function policyHeaderName(): string {
  return process.env.CSP_REPORT_ONLY === "true"
    ? "Content-Security-Policy-Report-Only"
    : "Content-Security-Policy";
}

function newNonce(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return btoa(String.fromCharCode(...bytes));
}

// An optimistic check: it only looks at the cookie, so a visitor without a login never sees a
// protected page load. It does not check the signature, because only the backend can. The real
// check happens on every backend call (see lib/server/authed.ts), where a 401 sends the user to
// /session-expired.
export function proxy(request: NextRequest) {
  const nonce = newNonce();
  const policy = contentSecurityPolicy(nonce);
  const header = policyHeaderName();

  let response: NextResponse;
  if (isProtectedPath(request.nextUrl.pathname) && !hasLiveToken(request.cookies.get(SESSION_COOKIE)?.value)) {
    response = NextResponse.redirect(new URL(LOGIN_PATH, request.url));
  } else {
    const headers = new Headers(request.headers);
    headers.set(header, policy);
    headers.set("x-nonce", nonce);
    response = NextResponse.next({ request: { headers } });
  }
  response.headers.set(header, policy);
  return response;
}

// Everything except static files and images. The path list itself lives in lib/auth/routes.ts.
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
