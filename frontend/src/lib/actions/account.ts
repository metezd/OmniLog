"use server";

import { redirect } from "next/navigation";

import { changePassword, deleteAccount, logoutAllDevices } from "@/lib/server/account";
import { BackendError } from "@/lib/server/backend";
import { toErrorState } from "@/lib/server/error-state";
import { createSession, destroySession } from "@/lib/server/session";

// The account page (#426). Each form shows the message of the backend for its field.

export type AccountFormState =
  | { status: "idle" }
  | { status: "saved"; message: string }
  | { status: "error"; message?: string; fieldErrors?: Record<string, string> };

function field(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value : "";
}

function rethrowIfRedirect(error: unknown): void {
  const digest = (error as { digest?: unknown } | null)?.digest;
  if (typeof digest === "string" && digest.startsWith("NEXT_REDIRECT")) throw error;
}

function failure(error: unknown, passwordField: string): AccountFormState {
  rethrowIfRedirect(error);
  if (error instanceof BackendError) {
    if (error.status === 403) return { status: "error", fieldErrors: { [passwordField]: "The password is not correct." } };
    if (error.status === 422 && Object.keys(error.fieldErrors).length > 0) {
      return { status: "error", fieldErrors: error.fieldErrors };
    }
  }
  return { status: "error", message: toErrorState(error).message };
}

/** Changes the password. The other sessions end, and this browser gets the new token. */
export async function changePasswordAction(
  _previous: AccountFormState,
  formData: FormData,
): Promise<AccountFormState> {
  const current = field(formData, "current_password");
  const next = field(formData, "new_password");
  if (next !== field(formData, "confirm_password")) {
    return { status: "error", fieldErrors: { confirm_password: "The two new passwords are not the same." } };
  }

  try {
    const token = await changePassword(current, next);
    await createSession(token.access_token);
  } catch (error) {
    return failure(error, "current_password");
  }
  return { status: "saved", message: "Your password was changed. Your other devices are logged out." };
}

/** Logs out on every device, this one too. */
export async function logoutAllDevicesAction(): Promise<void> {
  try {
    await logoutAllDevices();
  } catch (error) {
    rethrowIfRedirect(error);
    // The cookie is removed anyway, so this browser is logged out in every case
  }
  await destroySession();
  redirect("/login?loggedOut=all");
}

/** Deletes the account after the password was given again. */
export async function deleteAccountAction(
  _previous: AccountFormState,
  formData: FormData,
): Promise<AccountFormState> {
  if (field(formData, "confirm") !== "DELETE") {
    return { status: "error", fieldErrors: { confirm: 'Type DELETE to confirm.' } };
  }
  try {
    await deleteAccount(field(formData, "password"));
  } catch (error) {
    return failure(error, "password");
  }
  await destroySession();
  redirect("/login?deleted=1");
}
