import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SearchPage from "@/app/search/page";
import { BackendError } from "@/lib/server/backend";
import { searchCatalog } from "@/lib/server/catalog";
import { getLibrary } from "@/lib/server/library";
import type { LibraryEntry, MediaItem } from "@/types/api";

vi.mock("@/lib/server/catalog", () => ({ searchCatalog: vi.fn() }));
vi.mock("@/lib/server/library", () => ({ getLibrary: vi.fn() }));
vi.mock("@/lib/actions/library", () => ({ addToLibraryAction: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));

const catalogMock = vi.mocked(searchCatalog);
const libraryMock = vi.mocked(getLibrary);

function item(id: number, title: string, media_type: MediaItem["media_type"] = "SERIES"): MediaItem {
  return {
    id,
    title,
    media_type,
    poster_url: null,
    release_date: "2024-01-01",
    external_api_id: id * 10,
    genres: ["Drama"],
  };
}

function entry(media_item_id: number): LibraryEntry {
  return {
    id: media_item_id,
    user_id: 1,
    media_item_id,
    status: "PLAN_TO_WATCH",
    rating: null,
    updated_at: null,
    media_item: item(media_item_id, "Saved"),
  };
}

async function renderSearch(params: { q?: string; type?: string } = {}) {
  render(await SearchPage({ searchParams: Promise.resolve(params) }));
}

describe("SearchPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("searches catalog with query and type and marks items already in library", async () => {
    catalogMock.mockResolvedValue([item(1, "Arcane", "SERIES"), item(2, "Severance", "SERIES")]);
    libraryMock.mockResolvedValue([entry(1)]);

    await renderSearch({ q: "arc", type: "SERIES" });

    expect(catalogMock).toHaveBeenCalledWith("arc", "SERIES");
    expect(screen.getByText(/2 results for “arc”/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Arcane" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Severance" })).toBeInTheDocument();
    expect(screen.getByText(/In Library/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+ Add to Library" })).toBeInTheDocument();
  });

  it("switches media type tabs and preserves the search query in tab links", async () => {
    catalogMock.mockResolvedValue([item(10, "Elden Ring", "GAME")]);
    libraryMock.mockResolvedValue([]);

    await renderSearch({ q: "elden", type: "GAME" });

    expect(catalogMock).toHaveBeenCalledWith("elden", "GAME");
    expect(screen.getByRole("link", { name: "Video Games" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "TV Series" })).toHaveAttribute("href", "/search?type=SERIES&q=elden");
    expect(screen.getByRole("link", { name: "Movies" })).toHaveAttribute("href", "/search?type=MOVIE&q=elden");
  });

  it("shows the No results empty state when a query matches nothing", async () => {
    catalogMock.mockResolvedValue([]);
    libraryMock.mockResolvedValue([]);

    await renderSearch({ q: "nonexistentxyz", type: "GAME" });

    expect(screen.getByRole("status")).toHaveTextContent('Nothing found for "nonexistentxyz" in Video Games.');
  });

  it("shows the 503 service unavailable state when the outside catalog service is down", async () => {
    catalogMock.mockRejectedValue(new BackendError(503, "External catalog service is temporarily unavailable"));
    libraryMock.mockResolvedValue([]);

    await renderSearch({ q: "witcher", type: "GAME" });

    expect(screen.getByRole("alert")).toHaveTextContent("Service unavailable");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("rethrows NEXT_REDIRECT errors without swallowing them", async () => {
    const redirectErr = Object.assign(new Error("NEXT_REDIRECT"), { digest: "NEXT_REDIRECT;/session-expired" });
    catalogMock.mockRejectedValue(redirectErr);
    libraryMock.mockResolvedValue([]);

    await expect(SearchPage({ searchParams: Promise.resolve({ q: "test" }) })).rejects.toThrow("NEXT_REDIRECT");
  });
});

