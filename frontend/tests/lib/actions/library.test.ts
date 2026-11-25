// @vitest-environment node
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { submitReviewAction, type ReviewActionState } from "@/lib/actions/library";
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
