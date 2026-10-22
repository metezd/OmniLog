// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createSession, destroySession, getSessionToken, SESSION_COOKIE, tokenExpiry } from "@/lib/server/session";
import { cookieStore } from "../../mocks/cookie-store";

vi.mock("next/headers", async () => {
  const { cookieStore } = await import("../../mocks/cookie-store");
  return { cookies: async () => cookieStore };
});

const NOW = new Date("2026-10-21T10:00:00Z");

/** A token like the backend makes: three parts, and the middle part holds the claims. */
function makeToken(claims: Record<string, unknown>): string {
  const encode = (value: unknown) => Buffer.from(JSON.stringify(value)).toString("base64url");
  return `${encode({ alg: "HS256", typ: "JWT" })}.${encode(claims)}.signature`;
}

/** A token that ends the given number of seconds after NOW. */
function tokenEndingIn(seconds: number): string {
  return makeToken({ sub: "7", exp: Math.floor(NOW.getTime() / 1000) + seconds });
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(NOW);
  cookieStore.clear();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("tokenExpiry", () => {
  it("reads the end time from the exp claim", () => {
    expect(tokenExpiry(makeToken({ sub: "1", exp: 1_800_000_000 }))).toEqual(new Date(1_800_000_000_000));
  });

  it.each([
    ["an empty string", ""],
    ["a text that is not a token", "abc"],
    ["two parts", "a.b"],
    ["four parts", "a.b.c.d"],
    ["a middle part that is not base64 JSON", "a.%%%.c"],
    ["a middle part that is not JSON", `a.${Buffer.from("plain").toString("base64url")}.c`],
    ["claims that are not an object", makeToken(5 as unknown as Record<string, unknown>)],
    ["claims without exp", makeToken({ sub: "1" })],
    ["an exp that is text", makeToken({ exp: "1800000000" })],
    ["an exp that is null", makeToken({ exp: null })],
    ["an exp of zero", makeToken({ exp: 0 })],
    ["a negative exp", makeToken({ exp: -5 })],
  ])("returns null for %s", (_name, token) => {
    expect(tokenExpiry(token)).toBeNull();
  });
});

describe("createSession", () => {
  it("saves the token in an httpOnly cookie that is not sent along with requests from other sites", async () => {
    const token = tokenEndingIn(90 * 60);

    await createSession(token);

    expect(cookieStore.get(SESSION_COOKIE)).toEqual({ name: SESSION_COOKIE, value: token });
    expect(cookieStore.options.get(SESSION_COOKIE)).toMatchObject({
      httpOnly: true,
      sameSite: "lax",
      path: "/",
    });
    expect(cookieStore.names).toEqual([SESSION_COOKIE]);
  });

  it("gives the cookie the lifetime of the token, in seconds from now", async () => {
    await createSession(tokenEndingIn(90 * 60));

    expect(cookieStore.options.get(SESSION_COOKIE)?.maxAge).toBe(5400);
  });

  it("follows the token when the backend uses another lifetime", async () => {
    await createSession(tokenEndingIn(8 * 60 * 60));

    expect(cookieStore.options.get(SESSION_COOKIE)?.maxAge).toBe(28800);
  });

  it("allows plain http in development and demands https in production", async () => {
    vi.stubEnv("NODE_ENV", "development");
    await createSession(tokenEndingIn(60));
    expect(cookieStore.options.get(SESSION_COOKIE)?.secure).toBe(false);

    vi.stubEnv("NODE_ENV", "production");
    await createSession(tokenEndingIn(60));
    expect(cookieStore.options.get(SESSION_COOKIE)?.secure).toBe(true);
  });

  it("makes a cookie that ends with the browser when the token has no readable end time", async () => {
    await createSession("opaque-token-without-claims");

    const options = cookieStore.options.get(SESSION_COOKIE);
    expect(cookieStore.get(SESSION_COOKIE)?.value).toBe("opaque-token-without-claims");
    expect(options).not.toHaveProperty("maxAge");
    expect(options).not.toHaveProperty("expires");
  });

  it.each([-60, 0])("refuses a token that ended %i seconds ago and saves nothing", async (seconds) => {
    await expect(createSession(tokenEndingIn(seconds))).rejects.toThrow("The login token has already expired");

    expect(cookieStore.names).toEqual([]);
  });

  it("replaces the cookie of an earlier login", async () => {
    await createSession(tokenEndingIn(60));
    const second = tokenEndingIn(120);

    await createSession(second);

    expect(cookieStore.get(SESSION_COOKIE)?.value).toBe(second);
    expect(cookieStore.names).toEqual([SESSION_COOKIE]);
  });
});

describe("getSessionToken", () => {
  it("returns the token of the cookie", async () => {
    const token = tokenEndingIn(60);
    cookieStore.set(SESSION_COOKIE, token);

    expect(await getSessionToken()).toBe(token);
  });

  it("returns undefined when there is no cookie, or the cookie is empty", async () => {
    expect(await getSessionToken()).toBeUndefined();

    cookieStore.set(SESSION_COOKIE, "");
    expect(await getSessionToken()).toBeUndefined();
  });

  it("returns undefined when the token has ended, even if the cookie is still sent", async () => {
    cookieStore.set(SESSION_COOKIE, tokenEndingIn(60));

    vi.setSystemTime(new Date(NOW.getTime() + 61_000));

    expect(await getSessionToken()).toBeUndefined();
  });

  it("returns a token without a readable end time, because only the backend can judge it", async () => {
    cookieStore.set(SESSION_COOKIE, "opaque-token-without-claims");

    expect(await getSessionToken()).toBe("opaque-token-without-claims");
  });

  it("ignores other cookies", async () => {
    cookieStore.set("theme", "dark");

    expect(await getSessionToken()).toBeUndefined();
  });
});

describe("destroySession", () => {
  it("removes the session cookie and leaves the other cookies", async () => {
    cookieStore.set("theme", "dark");
    await createSession(tokenEndingIn(60));

    await destroySession();

    expect(cookieStore.names).toEqual(["theme"]);
  });

  it("does nothing when nobody is logged in", async () => {
    await expect(destroySession()).resolves.toBeUndefined();
  });
});
