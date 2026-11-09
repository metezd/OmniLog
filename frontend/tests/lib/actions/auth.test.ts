// @vitest-environment node
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { loginAction, logoutAction, registerAction } from "@/lib/actions/auth";
import { SESSION_COOKIE } from "@/lib/server/session";
import { cookieStore } from "../../mocks/cookie-store";
import { server } from "../../mocks/server";

vi.mock("next/navigation", async () => await import("../../mocks/next-navigation"));
vi.mock("next/headers", async () => {
  const { cookieStore } = await import("../../mocks/cookie-store");
  return { cookies: async () => cookieStore };
});

const BASE = "http://backend.test";
const PASSWORD = "StrongPass123!";

/** A token like the backend makes, valid for 90 minutes. */
function token(minutes = 90): string {
  const encode = (value: unknown) => Buffer.from(JSON.stringify(value)).toString("base64url");
  return `${encode({ alg: "HS256" })}.${encode({ sub: "7", exp: Math.floor(Date.now() / 1000) + minutes * 60 })}.sig`;
}

function form(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [name, value] of Object.entries(values)) data.set(name, value);
  return data;
}

/** Run an action that is expected to end with a redirect, and give back where it went. */
async function redirectOf(call: Promise<unknown>): Promise<string> {
  const error = await call.then(
    () => undefined,
    (caught: unknown) => caught,
  );
  expect(error).toMatchObject({ name: "RedirectSignal" });
  return (error as { url: string }).url;
}

/** Handlers of the backend that record the calls in the order they arrive. */
function useBackend({
  register = () => HttpResponse.json({ id: 1 }, { status: 201 }),
  login = () => HttpResponse.json({ access_token: token(), token_type: "bearer" }),
}: {
  register?: () => Response;
  login?: () => Response;
} = {}) {
  const calls: Array<{ path: string; body: unknown }> = [];
  server.use(
    http.post(`${BASE}/auth/register`, async ({ request }) => {
      calls.push({ path: "/auth/register", body: await request.json() });
      return register();
    }),
    http.post(`${BASE}/auth/login`, async ({ request }) => {
      calls.push({ path: "/auth/login", body: await request.json() });
      return login();
    }),
  );
  return calls;
}

const unprocessable = (detail: unknown[]) => () => HttpResponse.json({ detail }, { status: 422 });
const refuse = (status: number, detail: string) => () => HttpResponse.json({ detail }, { status });

beforeEach(() => {
  vi.stubEnv("BACKEND_URL", BASE);
  cookieStore.clear();
});

describe("loginAction", () => {
  it("logs in, saves the token in the session cookie and goes to the library", async () => {
    const calls = useBackend();

    const url = await redirectOf(loginAction(undefined, form({ username: "ali", password: PASSWORD })));

    expect(url).toBe("/library");
    expect(calls).toEqual([{ path: "/auth/login", body: { username: "ali", password: PASSWORD } }]);
    expect(cookieStore.has(SESSION_COOKIE)).toBe(true);
    const options = cookieStore.options.get(SESSION_COOKIE);
    expect(options).toMatchObject({ httpOnly: true });
    // 90 minutes, minus the moment that the test needed (the clock runs in this test)
    expect(options?.maxAge).toBeGreaterThan(5390);
    expect(options?.maxAge).toBeLessThanOrEqual(5400);
  });

  it("sends an email in the same field", async () => {
    const calls = useBackend();

    await redirectOf(loginAction(undefined, form({ username: "ali@example.com", password: PASSWORD })));

    expect(calls[0].body).toEqual({ username: "ali@example.com", password: PASSWORD });
  });

  it("shows the message of the backend for wrong credentials and keeps the username", async () => {
    useBackend({ login: refuse(401, "Invalid credentials") });

    const state = await loginAction(undefined, form({ username: "ali", password: "wrong" }));

    expect(state).toEqual({ values: { username: "ali" }, message: "Invalid credentials" });
    expect(cookieStore.names).toEqual([]);
  });

  it("never gives the password back to the form", async () => {
    useBackend({ login: refuse(401, "Invalid credentials") });

    const state = await loginAction(undefined, form({ username: "ali", password: "my-secret-password" }));

    expect(JSON.stringify(state)).not.toContain("my-secret-password");
  });

  it("shows the message of the backend for each field that it rejects", async () => {
    useBackend({
      login: unprocessable([{ loc: ["body", "username"], msg: "String should have at least 1 character" }]),
    });

    const state = await loginAction(undefined, form({ username: "", password: PASSWORD }));

    expect(state).toEqual({
      values: { username: "" },
      fieldErrors: { username: "String should have at least 1 character" },
    });
  });

  it("sends empty text for a field that is missing, and lets the backend judge", async () => {
    const calls = useBackend({ login: unprocessable([{ loc: ["body", "username"], msg: "too short" }]) });
    const data = new FormData();
    data.set("password", PASSWORD);
    data.set("username", new File(["x"], "x.txt")); // a file is not a text

    await loginAction(undefined, data);

    expect(calls[0].body).toEqual({ username: "", password: PASSWORD });
  });

  it("says that the server cannot be reached", async () => {
    server.use(http.post(`${BASE}/auth/login`, () => HttpResponse.error()));

    const state = await loginAction(undefined, form({ username: "ali", password: PASSWORD }));

    expect(state?.message).toBe("The server cannot be reached. Please try again in a moment.");
    expect(state?.values).toEqual({ username: "ali" });
  });

  it("hides the text of a server error", async () => {
    useBackend({ login: refuse(500, "Traceback: secret internals") });

    const state = await loginAction(undefined, form({ username: "ali", password: PASSWORD }));

    expect(state?.message).toBe("Something went wrong on the server. Please try again.");
    expect(JSON.stringify(state)).not.toContain("secret internals");
  });

  it("throws a mistake of the setup again, so it is not hidden behind a form message", async () => {
    vi.stubEnv("BACKEND_URL", "backend:8000");

    await expect(loginAction(undefined, form({ username: "ali", password: PASSWORD }))).rejects.toThrow(
      "BACKEND_URL is not a valid URL",
    );
  });

  it("replaces the cookie of an earlier login", async () => {
    useBackend();
    cookieStore.set(SESSION_COOKIE, "old-token");

    await redirectOf(loginAction(undefined, form({ username: "ali", password: PASSWORD })));

    expect(cookieStore.get(SESSION_COOKIE)?.value).not.toBe("old-token");
  });
});

describe("registerAction", () => {
  const data = () => form({ username: "ali", email: "ali@example.com", password: PASSWORD });

  it("creates the account, logs in with the same data and goes to the library", async () => {
    const calls = useBackend();

    const url = await redirectOf(registerAction(undefined, data()));

    expect(url).toBe("/library");
    // in this order, and the login does not get the email
    expect(calls).toEqual([
      { path: "/auth/register", body: { username: "ali", email: "ali@example.com", password: PASSWORD } },
      { path: "/auth/login", body: { username: "ali", password: PASSWORD } },
    ]);
    expect(cookieStore.has(SESSION_COOKIE)).toBe(true);
  });

  it("shows one message for the whole form when the account exists, and does not log in", async () => {
    const calls = useBackend({ register: refuse(409, "Username or email is already registered") });

    const state = await registerAction(undefined, data());

    expect(state).toEqual({
      values: { username: "ali", email: "ali@example.com" },
      message: "Username or email is already registered",
    });
    expect(calls.map((call) => call.path)).toEqual(["/auth/register"]);
    expect(cookieStore.names).toEqual([]);
  });

  it("shows the message of the backend for each field that it rejects", async () => {
    useBackend({
      register: unprocessable([
        { loc: ["body", "username"], msg: "Value error, must not contain @" },
        { loc: ["body", "password"], msg: "String should have at least 8 characters" },
      ]),
    });

    const state = await registerAction(undefined, form({ username: "a@b", email: "a@b.com", password: "x" }));

    expect(state).toEqual({
      values: { username: "a@b", email: "a@b.com" },
      fieldErrors: { username: "must not contain @", password: "String should have at least 8 characters" },
    });
    expect(cookieStore.names).toEqual([]);
  });

  it("never gives the password back to the form", async () => {
    useBackend({ register: refuse(409, "Username or email is already registered") });

    const state = await registerAction(
      undefined,
      form({ username: "ali", email: "ali@example.com", password: "my-secret-password" }),
    );

    expect(JSON.stringify(state)).not.toContain("my-secret-password");
  });

  it.each([
    ["the login is refused", refuse(401, "Invalid credentials")],
    ["the login has a server error", refuse(500, "boom")],
  ])("asks the user to log in when the account exists but %s", async (_name, login) => {
    useBackend({ login });

    const url = await redirectOf(registerAction(undefined, data()));

    expect(url).toBe("/login?registered=1");
    expect(cookieStore.names).toEqual([]);
  });

  it("asks the user to log in when the server stops answering after the account was created", async () => {
    server.use(
      http.post(`${BASE}/auth/register`, () => HttpResponse.json({ id: 1 }, { status: 201 })),
      http.post(`${BASE}/auth/login`, () => HttpResponse.error()),
    );

    expect(await redirectOf(registerAction(undefined, data()))).toBe("/login?registered=1");
  });

  it("says that the server cannot be reached when the registration cannot be sent", async () => {
    server.use(http.post(`${BASE}/auth/register`, () => HttpResponse.error()));

    const state = await registerAction(undefined, data());

    expect(state?.message).toBe("The server cannot be reached. Please try again in a moment.");
  });

  it("throws a mistake of the setup again", async () => {
    vi.stubEnv("BACKEND_URL", "");
    vi.stubEnv("NODE_ENV", "production");

    await expect(registerAction(undefined, data())).rejects.toThrow("BACKEND_URL is not set");
  });
});

describe("logoutAction", () => {
  it("removes the session cookie, keeps the other cookies and goes to the login page", async () => {
    cookieStore.set("theme", "dark");
    cookieStore.set(SESSION_COOKIE, token());

    const url = await redirectOf(logoutAction());

    expect(url).toBe("/login");
    expect(cookieStore.names).toEqual(["theme"]);
  });

  it("works when nobody is logged in", async () => {
    expect(await redirectOf(logoutAction())).toBe("/login");
  });

  it("does not call the backend", async () => {
    // A call without a handler would fail the test, so no call is the proof
    cookieStore.set(SESSION_COOKIE, token());

    await redirectOf(logoutAction());
  });
});
