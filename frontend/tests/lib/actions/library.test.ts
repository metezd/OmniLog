// @vitest-environment node
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  deleteReviewAction,
  logTitlePlaytimeAction,
  removeLastTitlePlaytimeAction,
  submitReviewAction,
  type ReviewActionState,
} from "@/lib/actions/library";
import type { Review } from "@/types/api";
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
const TOKEN = liveToken();

function form(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [name, value] of Object.entries(values)) data.set(name, value);
  return data;
}

function makeReview(overrides: Partial<Review> = {}): Review {
  return {
    id: 1,
    library_entry_id: 10,
    text: "Fantastic worldbuilding.",
    contains_spoiler: false,
    spoiler_score: 0.05,
    spoiler_model_version: "omnilog-nlp-spoiler-v1",
    created_at: "2026-11-20T12:00:00Z",
    updated_at: null,
    ...overrides,
  };
}

beforeEach(() => {
  vi.stubEnv("BACKEND_URL", BASE);
  cookieStore.clear();
  cookieStore.set("omnilog_session", TOKEN);
  revalidatePathMock.mockReset();
});

describe("submitReviewAction", () => {
  it("submits POST /library/{entry_id}/review with { text } and returns the saved review", async () => {
    const savedReview = makeReview();
    let seenBody: unknown;
    let seenAuth: string | null = null;
    server.use(
      http.post(`${BASE}/library/10/review`, async ({ request }) => {
        seenAuth = request.headers.get("authorization");
        seenBody = await request.json();
        return HttpResponse.json(savedReview, { status: 201 });
      }),
    );

    const state = await submitReviewAction(
      { status: "idle", review: null },
      form({ entryId: "10", mediaItemId: "42", text: "  Fantastic worldbuilding.  " }),
    );

    expect(seenAuth).toBe(`Bearer ${TOKEN}`);
    expect(seenBody).toEqual({ text: "Fantastic worldbuilding." });
    expect(state).toEqual({ status: "saved", review: savedReview });
    expect(revalidatePathMock).toHaveBeenCalledWith("/diary");
    expect(revalidatePathMock).toHaveBeenCalledWith("/title/42");
  });

  it("saves the review when spoiler check could not complete (contains_spoiler is null)", async () => {
    const uncheckedReview = makeReview({
      contains_spoiler: null,
      spoiler_score: null,
      spoiler_model_version: null,
    });
    server.use(
      http.post(`${BASE}/library/10/review`, () =>
        HttpResponse.json(uncheckedReview, { status: 201 }),
      ),
    );

    const state = await submitReviewAction(
      { status: "idle", review: null },
      form({ entryId: "10", mediaItemId: "42", text: "Fantastic worldbuilding." }),
    );

    expect(state).toEqual({ status: "saved", review: uncheckedReview });
  });

  it("rejects blank review text before calling the backend", async () => {
    const state = await submitReviewAction(
      { status: "idle", review: null },
      form({ entryId: "10", mediaItemId: "42", text: "   " }),
    );

    expect(state).toEqual({
      status: "error",
      code: "validation",
      message: "Review text cannot be empty.",
      review: null,
      draft: "   ",
    });
  });

  it("returns the backend 422 validation message while keeping the existing saved review", async () => {
    const existing = makeReview({ text: "Existing review" });
    server.use(
      http.post(`${BASE}/library/10/review`, () =>
        HttpResponse.json(
          {
            detail: [
              { loc: ["body", "text"], msg: "Value error, Review text cannot be blank" },
            ],
          },
          { status: 422 },
        ),
      ),
    );

    const previous: ReviewActionState = { status: "saved", review: existing };
    const state = await submitReviewAction(
      previous,
      form({ entryId: "10", mediaItemId: "42", text: "Some input" }),
    );

    expect(state).toEqual({
      status: "error",
      code: "validation",
      message: "Review text cannot be blank",
      review: existing,
      draft: "Some input",
    });
  });

  it("handles a 404 response when the library entry is not found", async () => {
    server.use(
      http.post(`${BASE}/library/999/review`, () =>
        HttpResponse.json({ detail: "Library entry not found" }, { status: 404 }),
      ),
    );

    const state = await submitReviewAction(
      { status: "idle", review: null },
      form({ entryId: "999", mediaItemId: "42", text: "Great game" }),
    );

    expect(state).toEqual({
      status: "error",
      code: "not_found",
      message: "This title or library entry could not be found.",
      review: null,
      draft: "Great game",
    });
  });

  it("handles a 503 response accurately without claiming the review was saved", async () => {
    const existing = makeReview({ text: "Previous review" });
    server.use(
      http.post(`${BASE}/library/10/review`, () =>
        HttpResponse.json({ detail: "External service is unavailable" }, { status: 503 }),
      ),
    );

    const state = await submitReviewAction(
      { status: "saved", review: existing },
      form({ entryId: "10", mediaItemId: "42", text: "Updated review text" }),
    );

    expect(state).toEqual({
      status: "error",
      code: "unavailable",
      message:
        "The AI moderation service is unavailable right now. Your review was not saved. Please try again.",
      review: existing,
      draft: "Updated review text",
    });
  });
});

describe("logTitlePlaytimeAction", () => {
  it("adds hours and minutes and sends POST /library/{entry_id}/playtime (#413)", async () => {
    let seenBody: unknown;
    server.use(
      http.post(`${BASE}/library/10/playtime`, async ({ request }) => {
        seenBody = await request.json();
        return HttpResponse.json(
          {
            id: 1,
            library_entry_id: 10,
            minutes: 90,
            logged_at: "2026-11-27T12:00:00Z",
            playtime_minutes: 90,
          },
          { status: 201 },
        );
      }),
    );

    const state = await logTitlePlaytimeAction(
      { status: "idle" },
      form({ entryId: "10", mediaItemId: "42", hours: "1", minutes: "30" }),
    );

    expect(seenBody).toEqual({ minutes: 90 });
    expect(state).toEqual({ status: "saved", message: "+1h 30m logged" });
    expect(revalidatePathMock).toHaveBeenCalledWith("/title/42");
    expect(revalidatePathMock).toHaveBeenCalledWith("/stats");
    expect(revalidatePathMock).toHaveBeenCalledWith("/diary");
  });

  it.each([
    [{ hours: "", minutes: "" }, "Playtime must be at least 1 minute."],
    [{ hours: "0", minutes: "0" }, "Playtime must be at least 1 minute."],
    [{ hours: "-1", minutes: "10" }, "Hours and minutes must be whole numbers."],
    [{ hours: "1.5", minutes: "" }, "Hours and minutes must be whole numbers."],
    [{ hours: "2000", minutes: "0" }, "One session can be at most 100,000 minutes."],
  ])("rejects %o before calling the backend", async (values, message) => {
    const state = await logTitlePlaytimeAction(
      { status: "idle" },
      form({ entryId: "10", mediaItemId: "42", ...values }),
    );

    expect(state).toEqual({ status: "error", message });
    expect(revalidatePathMock).not.toHaveBeenCalled();
  });

  it("shows the message of the backend, for example 422 for a series", async () => {
    server.use(
      http.post(`${BASE}/library/10/playtime`, () =>
        HttpResponse.json(
          { detail: "The time of a series is logged on its episodes" },
          { status: 422 },
        ),
      ),
    );

    const state = await logTitlePlaytimeAction(
      { status: "idle" },
      form({ entryId: "10", mediaItemId: "42", minutes: "45" }),
    );

    expect(state.status).toBe("error");
    expect(revalidatePathMock).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------- take back what was logged (#427)
describe("removeLastTitlePlaytimeAction", () => {
  it("sends DELETE /library/{id}/playtime/last and refreshes the pages", async () => {
    let method = "";
    server.use(
      http.delete(`${BASE}/library/7/playtime/last`, ({ request }) => {
        method = request.method;
        return HttpResponse.json({ id: 7, playtime_minutes: 60 });
      }),
    );

    const state = await removeLastTitlePlaytimeAction({ status: "idle" }, form({ entryId: "7", mediaItemId: "42" }));

    expect(method).toBe("DELETE");
    expect(state).toEqual({ status: "saved", message: "Last entry removed" });
    expect(revalidatePathMock).toHaveBeenCalledWith("/title/42");
    expect(revalidatePathMock).toHaveBeenCalledWith("/stats");
  });

  it("shows the message of a failed call", async () => {
    server.use(http.delete(`${BASE}/library/7/playtime/last`, () => HttpResponse.json({ detail: "No entry" }, { status: 404 })));

    const state = await removeLastTitlePlaytimeAction({ status: "idle" }, form({ entryId: "7", mediaItemId: "42" }));

    expect(state.status).toBe("error");
    expect(revalidatePathMock).not.toHaveBeenCalled();
  });

  it("refuses an entry id that is not a number", async () => {
    const state = await removeLastTitlePlaytimeAction({ status: "idle" }, form({ entryId: "abc" }));

    expect(state).toEqual({ status: "error", message: "Invalid library entry." });
  });
});

describe("deleteReviewAction", () => {
  const previous: ReviewActionState = { status: "idle", review: makeReview() };

  it("deletes the review and gives back a state without a review", async () => {
    let called = false;
    server.use(
      http.delete(`${BASE}/library/10/review`, () => {
        called = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );

    const state = await deleteReviewAction(previous, form({ entryId: "10", mediaItemId: "42" }));

    expect(called).toBe(true);
    expect(state).toEqual({ status: "idle", review: null });
    expect(revalidatePathMock).toHaveBeenCalledWith("/title/42");
  });

  it("treats a review that is already gone as deleted", async () => {
    server.use(http.delete(`${BASE}/library/10/review`, () => HttpResponse.json({ detail: "Review not found" }, { status: 404 })));

    expect(await deleteReviewAction(previous, form({ entryId: "10", mediaItemId: "42" }))).toEqual({
      status: "idle",
      review: null,
    });
  });

  it("keeps the review when the server fails", async () => {
    server.use(http.delete(`${BASE}/library/10/review`, () => HttpResponse.json({ detail: "boom" }, { status: 500 })));

    const state = await deleteReviewAction(previous, form({ entryId: "10", mediaItemId: "42" }));

    expect(state).toMatchObject({ status: "error", review: previous.review });
  });

  it("refuses an entry id that is not a number", async () => {
    const state = await deleteReviewAction(previous, form({ entryId: "x" }));

    expect(state).toMatchObject({ status: "error", code: "not_found" });
  });
});

