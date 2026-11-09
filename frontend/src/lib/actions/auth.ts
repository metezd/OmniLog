"use server";

import { redirect } from "next/navigation";

import { BackendError, backendFetch } from "@/lib/server/backend";
import { createSession, destroySession } from "@/lib/server/session";

// Server Actions of the login, the registration and the logout. The forms call them, and they
// call the backend. The token goes into an httpOnly cookie and never reaches the page.
//
// The backend is the only place with the rules for the fields (length, @ in a username, the format
// of the email, the password rules). The actions do not check them again. They show the message
// that the backend gives for each field.

/** Where the user goes after a login or a registration. */
const AFTER_LOGIN = "/library";

/**
 * What a form shows after it was sent. `message` is for the whole form, `fieldErrors` has one
 * message for each field and `values` gives the text back, so the form does not lose what the
 * user typed. The password is never part of the state.
 */
export type AuthFormState =
  | {
      message?: string;
      fieldErrors?: Record<string, string>;
      values?: { username?: string; email?: string };
    }
  | undefined;

type Token = { access_token: string; token_type: string };

function field(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value : "";
}

/** The state to show for a failed call. A mistake of the setup is not shown, it is thrown again. */
function failureState(error: unknown, values: NonNullable<AuthFormState>["values"]): AuthFormState {
  if (!(error instanceof BackendError)) throw error;

  if (error.status === 0) {
    return { values, message: "The server cannot be reached. Please try again in a moment." };
  }
  if (error.status >= 500) {
    // The text of a server error is not for the user
    return { values, message: "Something went wrong on the server. Please try again." };
  }
  if (Object.keys(error.fieldErrors).length > 0) {
    return { values, fieldErrors: error.fieldErrors };
  }
  return { values, message: error.message };
}

async function logIn(username: string, password: string): Promise<void> {
  const token = await backendFetch<Token>("/auth/login", {
    method: "POST",
    body: { username, password },
  });
  await createSession(token.access_token);
}

/** Log in with a username or an email (both go in the field `username`). */
export async function loginAction(_previous: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const username = field(formData, "username");
  const password = field(formData, "password");

  try {
    await logIn(username, password);
  } catch (error) {
    return failureState(error, { username });
  }
  // redirect() works by throwing, so it must stay outside of the try block
  redirect(AFTER_LOGIN);
}

/** Create the account and log in at once. */
export async function registerAction(_previous: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const username = field(formData, "username");
  const email = field(formData, "email");
  const password = field(formData, "password");

  try {
    await backendFetch("/auth/register", { method: "POST", body: { username, email, password } });
  } catch (error) {
    return failureState(error, { username, email });
  }

  try {
    await logIn(username, password);
  } catch (error) {
    if (!(error instanceof BackendError)) throw error;
    // The account exists. Only the automatic login failed, so ask the user to log in.
    redirect("/login?registered=1");
  }
  redirect(AFTER_LOGIN);
}

/**
 * Log out. The cookie is removed. The token itself stays valid until it ends, because the backend
 * does not keep a list of tokens, but nobody has it anymore.
 */
export async function logoutAction(): Promise<void> {
  await destroySession();
  redirect("/login");
}
