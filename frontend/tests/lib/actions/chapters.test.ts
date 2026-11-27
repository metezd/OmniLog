// @vitest-environment node
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { logPlaytimeAction, type ChapterActionState } from "@/lib/actions/chapters";
import { CHAPTER_WRITE_TIMEOUT_MS } from "@/lib/server/chapters";
import { cookieStore } from "../../mocks/cookie-store";
import { server } from "../../mocks/server";
import { liveToken } from "../../mocks/token";

const revalidatePathMock = vi.fn();

vi.mock("next/cache", () => ({
  revalidatePath: (...args: unknown[]) => revalidatePathMock(...args),
}));
vi.mock("next/headers", async () => {
  const { cookieStore } = await import("../../mocks/cookie-store");
  return { cookies: async () => cookieStore };
});
vi.mock("next/navigation", async () => await import("../../mocks/next-navigation"));

const BASE = "http://backend.test";
const IDLE: ChapterActionState = { status: "idle" };

function form(minutes: string): FormData {
  const data = new FormData();
  data.set("entryId", "10");
  data.set("chapterId", "7");
  data.set("mediaItemId", "42");
  data.set("minutes", minutes);
  return data;
}

beforeEach(() => {
  vi.stubEnv("BACKEND_URL", BASE);
  cookieStore.clear();
  cookieStore.set("omnilog_session", liveToken());
  revalidatePathMock.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("logPlaytimeAction (#411)", () => {
  it("logs the minutes, waits up to a minute for a backend that wakes up, and refreshes the title", async () => {
    const timeout = vi.spyOn(AbortSignal, "timeout");
    let seenBody: unknown;
    server.use(
      http.post(`${BASE}/library/10/chapters/7/playtime`, async ({ request }) => {
        seenBody = await request.json();
        return HttpResponse.json(
          { id: 1, chapter_id: 7, minutes: 45, logged_at: "2026-11-27T10:00:00Z", playtime_minutes: 45 },
          { status: 201 },
        );
      }),
    );

    const state = await logPlaytimeAction(IDLE, form("45"));

    expect(state).toEqual({ status: "saved", message: "+45m logged" });
    expect(seenBody).toEqual({ minutes: 45 });
    expect(timeout).toHaveBeenCalledWith(CHAPTER_WRITE_TIMEOUT_MS);
    expect(CHAPTER_WRITE_TIMEOUT_MS).toBe(60_000);
    expect(revalidatePathMock).toHaveBeenCalledWith("/title/42");
  });

  it.each(["0", "-3", "", "1.5", "abc"])("refuses %j minutes before calling the backend", async (minutes) => {
    const called = vi.fn();
    server.use(http.post(`${BASE}/library/10/chapters/7/playtime`, called));

    const state = await logPlaytimeAction(IDLE, form(minutes));

    expect(state).toEqual({ status: "error", message: "Playtime must be a positive number of minutes." });
    expect(called).not.toHaveBeenCalled();
  });

  it("shows the rule of the backend on 422", async () => {
    server.use(
      http.post(`${BASE}/library/10/chapters/7/playtime`, () =>
        HttpResponse.json({ detail: "The total playtime of a chapter is too large" }, { status: 422 }),
      ),
    );

    const state = await logPlaytimeAction(IDLE, form("45"));

    expect(state).toEqual({ status: "error", message: "The total playtime of a chapter is too large" });
  });

  it("asks to reload before trying again when the backend did not answer in time", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new DOMException("timed out", "TimeoutError"));

    const state = await logPlaytimeAction(IDLE, form("45"));

    expect(state).toEqual({
      status: "error",
      message: "The server took too long to answer. Reload the page to see if it was saved before you try again.",
    });
  });

  it("still says the data service is not available on 503", async () => {
    server.use(
      http.post(`${BASE}/library/10/chapters/7/playtime`, () =>
        HttpResponse.json({ detail: "The database is not available right now" }, { status: 503 }),
      ),
    );

    const state = await logPlaytimeAction(IDLE, form("45"));

    expect(state).toEqual({
      status: "error",
      message: "The data service is not available right now. Please try again.",
    });
  });
});
