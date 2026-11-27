// @vitest-environment node
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getTitleDetails, searchCatalog } from "@/lib/server/catalog";
import { getAllChapterProgress, getChapterProgress, logPlaytime, rateChapter, recordDecision } from "@/lib/server/chapters";
import { addItemToList, createList, deleteList, getDiary, getList, getLists, removeItemFromList } from "@/lib/server/journal";
import { addToLibrary, getLibrary, removeFromLibrary, updateLibraryEntry } from "@/lib/server/library";
import { getRecommendations } from "@/lib/server/recommendations";
import { getReview, submitReview } from "@/lib/server/reviews";
import { cookieStore } from "../../mocks/cookie-store";
import { server } from "../../mocks/server";
import { liveToken } from "../../mocks/token";

vi.mock("next/headers", async () => {
  const { cookieStore } = await import("../../mocks/cookie-store");
  return { cookies: async () => cookieStore };
});
vi.mock("next/navigation", async () => await import("../../mocks/next-navigation"));

const BASE = "http://backend.test";
const TOKEN = liveToken();

type Seen = { method: string; path: string; auth: string | null; body: unknown };

/** Answers every call to the fake backend with `reply` (or 204 without a body when `reply` is null)
 * and remembers what it received. */
function fakeBackend(reply: Record<string, unknown> | unknown[] | null = {}): { seen: Seen[] } {
  const seen: Seen[] = [];
  server.use(
    http.all(`${BASE}/*`, async ({ request }) => {
      const url = new URL(request.url);
      const text = await request.text();
      seen.push({
        method: request.method,
        path: url.pathname + url.search,
        auth: request.headers.get("authorization"),
        body: text ? JSON.parse(text) : undefined,
      });
      return reply === null ? new HttpResponse(null, { status: 204 }) : HttpResponse.json(reply);
    }),
  );
  return { seen };
}

beforeEach(() => {
  vi.stubEnv("BACKEND_URL", BASE);
  cookieStore.clear();
  cookieStore.set("omnilog_session", TOKEN);
});

describe("library", () => {
  it("reads the library", async () => {
    const { seen } = fakeBackend([]);
    await getLibrary();
    expect(seen).toEqual([{ method: "GET", path: "/library", auth: `Bearer ${TOKEN}`, body: undefined }]);
  });

  it("adds a title with the field names of the backend", async () => {
    const { seen } = fakeBackend();
    await addToLibrary({ mediaItemId: 4, status: "IN_PROGRESS" });
    expect(seen[0]).toMatchObject({ method: "POST", path: "/library", body: { media_item_id: 4, status: "IN_PROGRESS" } });
  });

  it("changes only what is given, and sends a null rating to clear it", async () => {
    const { seen } = fakeBackend();
    await updateLibraryEntry(9, { status: "COMPLETED" });
    await updateLibraryEntry(9, { rating: null });
    expect(seen.map((s) => [s.method, s.path, s.body])).toEqual([
      ["PATCH", "/library/9", { status: "COMPLETED" }],
      ["PATCH", "/library/9", { rating: null }],
    ]);
  });
});

describe("removals", () => {
  it("removes a title from the library with a DELETE and returns nothing", async () => {
    const { seen } = fakeBackend(null);

    await expect(removeFromLibrary(9)).resolves.toBeUndefined();

    expect(seen).toEqual([{ method: "DELETE", path: "/library/9", auth: `Bearer ${TOKEN}`, body: undefined }]);
  });

  it("takes a title out of a list and deletes a list", async () => {
    const { seen } = fakeBackend(null);

    await expect(removeItemFromList(5, 12)).resolves.toBeUndefined();
    await expect(deleteList(5)).resolves.toBeUndefined();

    expect(seen.map((s) => [s.method, s.path])).toEqual([
      ["DELETE", "/lists/5/items/12"],
      ["DELETE", "/lists/5"],
    ]);
  });

  it("throws a BackendError with status 404 for a title that is not there", async () => {
    server.use(http.delete(`${BASE}/library/9`, () => HttpResponse.json({ detail: "Library entry not found" }, { status: 404 })));

    await expect(removeFromLibrary(9)).rejects.toMatchObject({ status: 404, message: "Library entry not found" });
  });
});

describe("catalog", () => {
  it("searches with the query and the type, and escapes the query", async () => {
    const { seen } = fakeBackend([]);
    await searchCatalog("Life is Strange & more", "GAME");
    expect(seen[0].method).toBe("GET");
    const url = new URL(`${BASE}${seen[0].path}`);
    expect(url.pathname).toBe("/catalog/search");
    expect(url.searchParams.get("q")).toBe("Life is Strange & more");
    expect(url.searchParams.get("type")).toBe("GAME");
  });

  it("opens a title", async () => {
    const { seen } = fakeBackend();
    await getTitleDetails(12);
    expect(seen[0]).toMatchObject({ method: "GET", path: "/catalog/12" });
  });
});

describe("chapters", () => {
  it("reads the progress of a chapter of a library entry", async () => {
    const { seen } = fakeBackend();
    await getChapterProgress(3, 8);
    expect(seen[0]).toMatchObject({ method: "GET", path: "/library/3/chapters/8" });
  });

  it("rates a chapter", async () => {
    const { seen } = fakeBackend();
    await rateChapter(3, 8, 4);
    expect(seen[0]).toMatchObject({ method: "PUT", path: "/library/3/chapters/8/rating", body: { rating: 4 } });
  });

  it("logs playtime", async () => {
    const { seen } = fakeBackend();
    await logPlaytime(3, 8, 90);
    expect(seen[0]).toMatchObject({ method: "POST", path: "/library/3/chapters/8/playtime", body: { minutes: 90 } });
  });

  it("reads the progress of all chapters of an entry in one call (#419)", async () => {
    const { seen } = fakeBackend([]);
    await getAllChapterProgress(3);
    expect(seen.map((s) => [s.method, s.path])).toEqual([["GET", "/library/3/chapters"]]);
  });

  it("records a decision, and sends the decision point only when it is given", async () => {
    const { seen } = fakeBackend();
    await recordDecision(3, 8, "A");
    await recordDecision(3, 8, "B", 21);
    expect(seen.map((s) => [s.method, s.path, s.body])).toEqual([
      ["PUT", "/library/3/chapters/8/decision", { choice: "A" }],
      ["PUT", "/library/3/chapters/8/decision", { choice: "B", decision_point_id: 21 }],
    ]);
  });
});

describe("journal", () => {
  it("reads the lists, one list and the diary", async () => {
    const { seen } = fakeBackend([]);
    await getLists();
    await getList(5);
    await getDiary();
    expect(seen.map((s) => [s.method, s.path])).toEqual([
      ["GET", "/lists"],
      ["GET", "/lists/5"],
      ["GET", "/diary"],
    ]);
  });

  it("reads a page of the diary with limit and offset", async () => {
    const { seen } = fakeBackend([]);
    await getDiary({ limit: 50 });
    await getDiary({ limit: 50, offset: 100 });
    expect(seen.map((s) => [s.method, s.path])).toEqual([
      ["GET", "/diary?limit=50"],
      ["GET", "/diary?limit=50&offset=100"],
    ]);
  });

  it("creates a list and adds a title to it", async () => {
    const { seen } = fakeBackend();
    await createList("Best narrative games");
    await addItemToList(5, 12);
    expect(seen.map((s) => [s.method, s.path, s.body])).toEqual([
      ["POST", "/lists", { name: "Best narrative games" }],
      ["POST", "/lists/5/items", { media_item_id: 12 }],
    ]);
  });
});

describe("reviews", () => {
  const sampleReview = {
    id: 1,
    library_entry_id: 10,
    text: "Great pacing and memorable ending.",
    contains_spoiler: false,
    spoiler_score: 0.1,
    spoiler_model_version: "omnilog-nlp-spoiler-v1",
    created_at: "2026-11-20T12:00:00Z",
    updated_at: null,
  };

  it("posts a review to /library/{entry_id}/review with { text }", async () => {
    const { seen } = fakeBackend(sampleReview);
    const saved = await submitReview(10, "Great pacing and memorable ending.");
    expect(saved).toEqual(sampleReview);
    expect(seen[0]).toEqual({
      method: "POST",
      path: "/library/10/review",
      auth: `Bearer ${TOKEN}`,
      body: { text: "Great pacing and memorable ending." },
    });
  });

  it("reads an existing review", async () => {
    const { seen } = fakeBackend(sampleReview);
    expect(await getReview(10)).toEqual(sampleReview);
    expect(seen[0]).toMatchObject({ method: "GET", path: "/library/10/review" });
  });

  it("returns null when the entry has no review yet (404 Review not found)", async () => {
    server.use(
      http.get(`${BASE}/library/10/review`, () =>
        HttpResponse.json({ detail: "Review not found" }, { status: 404 }),
      ),
    );
    await expect(getReview(10)).resolves.toBeNull();
  });

  it("throws 404 when the library entry itself is missing", async () => {
    server.use(
      http.get(`${BASE}/library/999/review`, () =>
        HttpResponse.json({ detail: "Library entry not found" }, { status: 404 }),
      ),
    );
    await expect(getReview(999)).rejects.toMatchObject({
      status: 404,
      message: "Library entry not found",
    });
  });
});

describe("recommendations", () => {
  it("fetches recommendations with the required target query parameter", async () => {
    const { seen } = fakeBackend([]);
    await getRecommendations("SERIES");
    await getRecommendations("GAME", 5);

    expect(seen.map((s) => [s.method, s.path, s.auth])).toEqual([
      ["GET", "/recommendations?target=SERIES", `Bearer ${TOKEN}`],
      ["GET", "/recommendations?target=GAME&limit=5", `Bearer ${TOKEN}`],
    ]);
  });

  it("throws BackendError on 422 or 503 responses", async () => {
    server.use(
      http.get(`${BASE}/recommendations`, () =>
        HttpResponse.json({ detail: "Service unavailable" }, { status: 503 }),
      ),
    );
    await expect(getRecommendations("MOVIE")).rejects.toMatchObject({ status: 503 });
  });
});
