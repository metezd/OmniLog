// @vitest-environment node
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getCurrentUser } from "@/lib/server/user";
import { cookieStore } from "../../mocks/cookie-store";
import { server } from "../../mocks/server";
import { liveToken } from "../../mocks/token";

vi.mock("next/headers", async () => {
  const { cookieStore } = await import("../../mocks/cookie-store");
  return { cookies: async () => cookieStore };
});

const BASE = "http://backend.test";
const USER = { id: 7, email: "ali@example.com", username: "ali", created_at: "2026-10-01T10:00:00Z" };

beforeEach(() => {
  vi.stubEnv("BACKEND_URL", BASE);
  cookieStore.clear();
});

describe("getCurrentUser", () => {
  it("returns the user that the backend names", async () => {
    cookieStore.set("omnilog_session", liveToken());
    server.use(http.get(`${BASE}/auth/me`, () => HttpResponse.json(USER)));

    expect(await getCurrentUser()).toEqual(USER);
  });

  it("returns null without a session and does not call the backend", async () => {
    expect(await getCurrentUser()).toBeNull();
  });

  it("returns null when the backend refuses the token", async () => {
    cookieStore.set("omnilog_session", liveToken());
    server.use(http.get(`${BASE}/auth/me`, () => HttpResponse.json({ detail: "Not authenticated" }, { status: 401 })));

    expect(await getCurrentUser()).toBeNull();
  });

  it("returns null when the backend cannot be reached, so a public page still loads", async () => {
    cookieStore.set("omnilog_session", liveToken());
    server.use(http.get(`${BASE}/auth/me`, () => HttpResponse.error()));

    expect(await getCurrentUser()).toBeNull();
  });

  it("does not hide a mistake of the setup", async () => {
    cookieStore.set("omnilog_session", liveToken());
    vi.stubEnv("BACKEND_URL", "backend:8000");

    await expect(getCurrentUser()).rejects.toThrow("BACKEND_URL is not a valid URL");
  });
});
