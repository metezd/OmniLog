import { NextResponse, type NextRequest } from "next/server";

import { isProtectedPath, LOGIN_PATH } from "@/lib/auth/routes";
import { hasLiveToken, SESSION_COOKIE } from "@/lib/auth/token";

// An optimistic check: it only looks at the cookie, so a visitor without a login never sees a
// protected page load. It does not check the signature, because only the backend can. The real
// check happens on every backend call (see lib/server/authed.ts), where a 401 sends the user to
// /session-expired.
export function proxy(request: NextRequest) {
  if (!isProtectedPath(request.nextUrl.pathname)) return NextResponse.next();
  if (hasLiveToken(request.cookies.get(SESSION_COOKIE)?.value)) return NextResponse.next();
  return NextResponse.redirect(new URL(LOGIN_PATH, request.url));
}

// Everything except static files and images. The path list itself lives in lib/auth/routes.ts.
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
