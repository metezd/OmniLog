import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DiaryPage from "@/app/diary/page";
import LibraryPage from "@/app/library/page";
import Home from "@/app/page";
import SearchPage from "@/app/search/page";
import TitleDetailPage from "@/app/title/[id]/page";
import { searchCatalog, getTitleDetails } from "@/lib/server/catalog";
import { getAllChapterProgress } from "@/lib/server/chapters";
import { PAGE_SIZE } from "@/lib/server/library";
import { getReview } from "@/lib/server/reviews";
import { getCurrentUser } from "@/lib/server/user";
import type { DiaryEntry, LibraryEntry, MediaDetail, MediaItem } from "@/types/api";
import { cookieStore } from "../mocks/cookie-store";
import { server } from "../mocks/server";
import { liveToken } from "../mocks/token";

// The pages with the real library and journal code against a fake backend (MSW) that pages its
// answers like the real one (#448): `limit` 1 to 500 with a default of 200, `offset`, oldest first.
// A library of 501 titles needs a second page of 500, and the missing title is the newest one.

vi.mock("next/headers", async () => {
  const { cookieStore } = await import("../mocks/cookie-store");
  return { cookies: async () => cookieStore };
});
vi.mock("next/navigation", async () => ({
  ...(await import("../mocks/next-navigation")),
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));
vi.mock("@/lib/server/user", () => ({ getCurrentUser: vi.fn() }));
vi.mock("@/lib/server/catalog", () => ({ searchCatalog: vi.fn(), getTitleDetails: vi.fn() }));
vi.mock("@/lib/server/chapters", () => ({ getAllChapterProgress: vi.fn() }));
vi.mock("@/lib/server/reviews", () => ({ getReview: vi.fn() }));
vi.mock("@/lib/actions/library", () => ({
  addToLibraryAction: vi.fn(),
  updateLibraryEntryAction: vi.fn(),
  removeLibraryEntryAction: vi.fn(),
  logTitlePlaytimeAction: vi.fn(),
  submitReviewAction: vi.fn(),
}));
vi.mock("@/lib/actions/chapters", () => ({
  rateChapterAction: vi.fn(),
  logPlaytimeAction: vi.fn(),
  recordDecisionAction: vi.fn(),
}));

const BASE = "http://backend.test";

function media(id: number): MediaItem {
  return {
    id,
    title: `Title ${id}`,
    media_type: "SERIES",
    poster_url: null,
    release_date: "2024-01-01",
    external_api_id: id,
    genres: [],
  };
}

function entry(id: number): LibraryEntry {
  return {
    id,
    user_id: 7,
    media_item_id: id,
    status: "IN_PROGRESS",
    rating: null,
    playtime_minutes: 0,
    updated_at: null,
    media_item: media(id),
  };
}

/** Slices `rows` like the backend does, and remembers the query of every call. */
function paged<T>(rows: T[], seen: string[]) {
  return ({ request }: { request: Request }) => {
    const url = new URL(request.url);
    seen.push(url.search);
    const limit = Number(url.searchParams.get("limit") ?? 200);
    const offset = Number(url.searchParams.get("offset") ?? 0);
    if (limit < 1 || limit > 500) return HttpResponse.json({ detail: "limit" }, { status: 422 });
    return HttpResponse.json(rows.slice(offset, offset + limit));
  };
}

/** A fake backend whose library has `count` titles (ids 1 to count, oldest first). */
function libraryOf(count: number): { seen: string[]; rows: LibraryEntry[] } {
  const rows = Array.from({ length: count }, (_, i) => entry(i + 1));
  const seen: string[] = [];
  const page = paged(rows, seen);
  server.use(
    http.get(`${BASE}/library`, ({ request }) => {
      const mediaId = new URL(request.url).searchParams.get("media_item_id");
      if (mediaId === null) return page({ request });
      seen.push(new URL(request.url).search);
      return HttpResponse.json(rows.filter((row) => row.media_item_id === Number(mediaId)));
    }),
  );
  return { seen, rows };
}

beforeEach(() => {
  vi.stubEnv("BACKEND_URL", BASE);
  cookieStore.clear();
  cookieStore.set("omnilog_session", liveToken());
});

describe("Library page with a second page (#448)", () => {
  it("shows the newest title, which is on the second page", async () => {
    const { seen } = libraryOf(PAGE_SIZE + 1);

    render(await LibraryPage());

    expect(screen.getByRole("heading", { name: "Title 501" })).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { name: /^Title \d+$/ })).toHaveLength(501);
    expect(seen).toEqual(["?limit=500&offset=0", "?limit=500&offset=500"]);
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
  });
});

describe("Home page with a second page (#448)", () => {
  it("counts every title of the library", async () => {
    vi.mocked(getCurrentUser).mockResolvedValue({
      id: 7,
      username: "ali",
      email: "ali@example.com",
      created_at: "2026-10-01T10:00:00Z",
    });
    libraryOf(PAGE_SIZE + 1);

    render(await Home());

    expect(screen.getByText("501 titles in your personal library")).toBeInTheDocument();
  });
});

describe("Search page with a second page (#448)", () => {
  it("marks a title of the second page as in the library", async () => {
    vi.mocked(searchCatalog).mockResolvedValue([media(PAGE_SIZE + 1), media(9999)]);
    libraryOf(PAGE_SIZE + 1);

    render(await SearchPage({ searchParams: Promise.resolve({ q: "title" }) }));

    expect(screen.getAllByText("✓ In Library")).toHaveLength(1);
    expect(screen.getAllByRole("button", { name: "+ Add to Library" })).toHaveLength(1);
  });
});

describe("Title page with a second page (#448)", () => {
  it("finds the entry of the newest title and shows its controls", async () => {
    const detail: MediaDetail = { ...media(PAGE_SIZE + 1), description: null, seasons: [], chapters: [] };
    vi.mocked(getTitleDetails).mockResolvedValue(detail);
    vi.mocked(getReview).mockResolvedValue(null);
    vi.mocked(getAllChapterProgress).mockResolvedValue([]);
    const { seen } = libraryOf(PAGE_SIZE + 1);

    render(await TitleDetailPage({ params: Promise.resolve({ id: String(PAGE_SIZE + 1) }) }));

    expect(screen.getByRole("heading", { name: "Your Library Status" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "+ Add to Library" })).not.toBeInTheDocument();
    expect(seen).toEqual(["?media_item_id=501"]); // one request, not the whole library
  });
});

describe("Diary page with a second page (#448)", () => {
  it("reads the older events with an offset and names a title of the second library page", async () => {
    const events: DiaryEntry[] = Array.from({ length: 150 }, (_, i) => ({
      id: 150 - i,
      user_id: 7,
      media_item_id: i === 120 ? PAGE_SIZE + 1 : null,
      action: "LIST_CREATED",
      details: `Event ${150 - i}`,
      created_at: "2026-11-27T10:00:00Z",
    }));
    const diarySeen: string[] = [];
    server.use(http.get(`${BASE}/diary`, paged(events, diarySeen)));
    libraryOf(PAGE_SIZE + 1);

    render(await DiaryPage({ searchParams: Promise.resolve({ page: "2" }) }));

    expect(diarySeen).toEqual(["?limit=101&offset=100"]);
    expect(screen.getAllByText(/^Event \d+$/)).toHaveLength(50);
    expect(screen.getByText("Event 50")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Title 501" })).toHaveAttribute("href", "/title/501");
    expect(screen.getByRole("link", { name: "Newer events" })).toHaveAttribute("href", "/diary");
    expect(screen.queryByRole("link", { name: "Older events" })).not.toBeInTheDocument();
  });
});
