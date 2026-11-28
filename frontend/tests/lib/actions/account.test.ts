// @vitest-environment node
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { changePasswordAction, deleteAccountAction, logoutAllDevicesAction } from "@/lib/actions/account";
import { SESSION_COOKIE } from "@/lib/server/session";
import { cookieStore } from "../../mocks/cookie-store";
import { server } from "../../mocks/server";
import { liveToken } from "../../mocks/token";

vi.mock("next/headers", async () => {
  const { cookieStore } = await import("../../mocks/cookie-store");
  return { cookies: async () => cookieStore, headers: async () => new Headers() };
});
vi.mock("next/navigation", async () => await import("../../mocks/next-navigation"));

const BASE = "http://backend.test";
const IDLE = { status: "idle" } as const;

function form(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [name, value] of Object.entries(values)) data.set(name, value);
  return data;
}

async function redirectOf(call: Promise<unknown>): Promise<string> {
  const error = await call.then(
    () => undefined,
    (caught: unknown) => caught,
  );
  expect(error).toMatchObject({ name: "RedirectSignal" });
  return (error as { url: string }).url;
}

beforeEach(() => {
  vi.stubEnv("BACKEND_URL", BASE);
  cookieStore.clear();
  cookieStore.set(SESSION_COOKIE, liveToken());
});

describe("changePasswordAction (#426)", () => {
  it("sends both passwords and keeps this browser logged in with the new token", async () => {
    const fresh = liveToken();
    let body: unknown;
    server.use(
      http.put(`${BASE}/auth/password`, async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ access_token: fresh, token_type: "bearer" });
      }),
    );

    const state = await changePasswordAction(
      IDLE,
      form({ current_password: "Old-Pass-2026!", new_password: "New-Pass-2026!", confirm_password: "New-Pass-2026!" }),
    );

    expect(body).toEqual({ current_password: "Old-Pass-2026!", new_password: "New-Pass-2026!" });
    expect(state).toMatchObject({ status: "saved" });
    expect(cookieStore.get(SESSION_COOKIE)?.value).toBe(fresh);
  });

  it("shows a wrong current password on its field (403, not a logout)", async () => {
    server.use(http.put(`${BASE}/auth/password`, () => HttpResponse.json({ detail: "The password is not correct" }, { status: 403 })));

    const state = await changePasswordAction(
      IDLE,
      form({ current_password: "x", new_password: "New-Pass-2026!", confirm_password: "New-Pass-2026!" }),
    );

    expect(state).toEqual({ status: "error", fieldErrors: { current_password: "The password is not correct." } });
    expect(cookieStore.names).toContain(SESSION_COOKIE);
  });

  it("shows the rule of the backend for a weak new password", async () => {
    server.use(
      http.put(`${BASE}/auth/password`, () =>
        HttpResponse.json(
          { detail: [{ type: "value_error", loc: ["body", "new_password"], msg: "Value error, this password is too common" }] },
          { status: 422 },
        ),
      ),
    );

    const state = await changePasswordAction(
      IDLE,
      form({ current_password: "Old-Pass-2026!", new_password: "password", confirm_password: "password" }),
    );

    expect(state).toMatchObject({ status: "error", fieldErrors: { new_password: "this password is too common" } });
  });

  it("does not call the backend when the two new passwords differ", async () => {
    let called = false;
    server.use(http.put(`${BASE}/auth/password`, () => ((called = true), HttpResponse.json({}))));

    const state = await changePasswordAction(
      IDLE,
      form({ current_password: "a", new_password: "New-Pass-2026!", confirm_password: "Other-2026!" }),
    );

    expect(called).toBe(false);
    expect(state).toMatchObject({ fieldErrors: { confirm_password: expect.any(String) } });
  });
});

describe("logoutAllDevicesAction (#426)", () => {
  it("ends every session, removes the cookie and goes to the login page", async () => {
    let called = false;
    server.use(http.post(`${BASE}/auth/logout-all`, () => ((called = true), new HttpResponse(null, { status: 204 }))));

    expect(await redirectOf(logoutAllDevicesAction())).toBe("/login?loggedOut=all");
    expect(called).toBe(true);
    expect(cookieStore.names).not.toContain(SESSION_COOKIE);
  });
});

describe("deleteAccountAction (#426)", () => {
  it("needs DELETE typed before it calls the backend", async () => {
    const state = await deleteAccountAction(IDLE, form({ password: "x", confirm: "delete" }));

    expect(state).toMatchObject({ status: "error", fieldErrors: { confirm: expect.any(String) } });
  });

  it("deletes the account, removes the cookie and goes to the login page", async () => {
    let body: unknown;
    server.use(
      http.delete(`${BASE}/auth/me`, async ({ request }) => {
        body = await request.json();
        return new HttpResponse(null, { status: 204 });
      }),
    );

    expect(await redirectOf(deleteAccountAction(IDLE, form({ password: "Pass-2026!", confirm: "DELETE" })))).toBe(
      "/login?deleted=1",
    );
    expect(body).toEqual({ password: "Pass-2026!" });
    expect(cookieStore.names).not.toContain(SESSION_COOKIE);
  });

  it("keeps the account and the session for a wrong password", async () => {
    server.use(http.delete(`${BASE}/auth/me`, () => HttpResponse.json({ detail: "no" }, { status: 403 })));

    const state = await deleteAccountAction(IDLE, form({ password: "wrong", confirm: "DELETE" }));

    expect(state).toEqual({ status: "error", fieldErrors: { password: "The password is not correct." } });
    expect(cookieStore.names).toContain(SESSION_COOKIE);
  });
});
