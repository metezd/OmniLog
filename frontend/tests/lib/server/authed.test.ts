// @vitest-environment node
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { authedFetch } from "@/lib/server/authed";
import { BackendError } from "@/lib/server/backend";
import { cookieStore } from "../../mocks/cookie-store";
import { server } from "../../mocks/server";
import { endedToken, liveToken } from "../../mocks/token";

vi.mock("next/headers", async () => {
  const { cookieStore } = await import("../../mocks/cookie-store");
  return { cookies: async () => cookieStore };
});
vi.mock("next/navigation", async () => await import("../../mocks/next-navigation"));

const BASE = "http://backend.test";

beforeEach(() => {
  vi.stubEnv("BACKEND_URL", BASE);
  cookieStore.clear();
});

describe("authedFetch", () => {
  it("sends the token of the session cookie to the backend", async () => {
    const token = liveToken();
    cookieStore.set("omnilog_session", token);
    let header: string | null = null;
    server.use(
      http.get(`${BASE}/library`, ({ request }) => {
        header = request.headers.get("authorization");
        return HttpResponse.json([]);
      }),
    );

    expect(await authedFetch("/library")).toEqual([]);
    expect(header).toBe(`Bearer ${token}`);
  });

  it("sends the user to the login page when there is no session, without calling the backend", async () => {
    // No handler is set. A call to the backend would fail the test.
    await expect(authedFetch("/library")).rejects.toMatchObject({ url: "/login" });
  });

  it("sends the user to the login page when the token has ended", async () => {
    cookieStore.set("omnilog_session", endedToken());

    await expect(authedFetch("/library")).rejects.toMatchObject({ url: "/login" });
  });

  it("sends the user to /session-expired when the backend refuses the token", async () => {
    cookieStore.set("omnilog_session", liveToken());
    server.use(http.get(`${BASE}/library`, () => HttpResponse.json({ detail: "Not authenticated" }, { status: 401 })));

    await expect(authedFetch("/library")).rejects.toMatchObject({ url: "/session-expired" });
  });

  it.each([404, 422, 500, 503])("throws a BackendError for status %i", async (status) => {
    cookieStore.set("omnilog_session", liveToken());
    server.use(http.get(`${BASE}/library`, () => HttpResponse.json({ detail: "nope" }, { status })));

    await expect(authedFetch("/library")).rejects.toMatchObject({ status });
    await expect(authedFetch("/library")).rejects.toBeInstanceOf(BackendError);
  });

  it("passes the method and the body on", async () => {
    cookieStore.set("omnilog_session", liveToken());
    let received: unknown;
    server.use(
      http.post(`${BASE}/lists`, async ({ request }) => {
        received = await request.json();
        return HttpResponse.json({ id: 1 }, { status: 201 });
      }),
    );

    await authedFetch("/lists", { method: "POST", body: { name: "Best" } });

    expect(received).toEqual({ name: "Best" });
  });
});
