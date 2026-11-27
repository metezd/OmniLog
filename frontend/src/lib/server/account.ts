import "server-only";

import { authedFetch } from "./authed";

// Account management of the logged-in user (#426). A wrong password answers 403, not 401, so
// authedFetch does not take it for an ended session.

type Token = { access_token: string; token_type: string };

/** Sets a new password. Every session ends, and the answer holds a new token for this one. */
export function changePassword(currentPassword: string, newPassword: string): Promise<Token> {
  return authedFetch<Token>("/auth/password", {
    method: "PUT",
    body: { current_password: currentPassword, new_password: newPassword },
  });
}

/** Ends every session of the user, also this one. */
export function logoutAllDevices(): Promise<void> {
  return authedFetch<void>("/auth/logout-all", { method: "POST" });
}

/** Deletes the account with all its data. */
export function deleteAccount(password: string): Promise<void> {
  return authedFetch<void>("/auth/me", { method: "DELETE", body: { password } });
}
