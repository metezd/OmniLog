import { redirect } from "next/navigation";

import { LOGIN_PATH } from "@/lib/auth/routes";
import { destroySession } from "@/lib/server/session";

// The backend refused the token (see lib/server/authed.ts). A page cannot remove a cookie while
// it is rendered, but a Route Handler can. So the user lands here, the cookie is removed and the
// login page explains what happened.
export async function GET() {
  await destroySession();
  redirect(`${LOGIN_PATH}?expired=1`);
}
