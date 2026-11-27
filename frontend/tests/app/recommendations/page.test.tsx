import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import RecommendationsLoading from "@/app/recommendations/loading";
import RecommendationsPage from "@/app/recommendations/page";
import { BackendError } from "@/lib/server/backend";
import { getLibrary } from "@/lib/server/library";
import { getRecommendations } from "@/lib/server/recommendations";
import type { LibraryEntry, MediaItem } from "@/types/api";

vi.mock("@/lib/server/recommendations", () => ({ getRecommendations: vi.fn() }));
vi.mock("@/lib/server/library", () => ({ getLibrary: vi.fn() }));
vi.mock("@/lib/actions/library", () => ({ addToLibraryAction: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));

const recsMock = vi.mocked(getRecommendations);
const libraryMock = vi.mocked(getLibrary);

function makeItem(
  id: number,
  title: string,
  media_type: MediaItem["media_type"] = "SERIES",
): MediaItem {
  return {
    id,
    title,
    media_type,
    poster_url: `https://images.test/${id}.jpg`,
    release_date: "2023-04-10",
    external_api_id: id * 100,
    genres: ["Sci-Fi", "Drama"],
  };
}

function makeEntry(media_item_id: number): LibraryEntry {
  return {
    id: media_item_id,
    user_id: 1,
    media_item_id,
    status: "COMPLETED",
    rating: 9,
    playtime_minutes: 0,
    updated_at: null,
    media_item: makeItem(media_item_id, "Owned Title", "GAME"),
  };
}

async function renderRecommendations(params: { target?: string } = {}) {
  render(await RecommendationsPage({ searchParams: Promise.resolve(params) }));
}

describe("RecommendationsPage (S-10)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("defaults to SERIES target so target is always sent, and renders search-style cards with Add to Library", async () => {
    recsMock.mockResolvedValue([
      makeItem(1, "Severance", "SERIES"),
      makeItem(2, "Dark", "SERIES"),
    ]);
    libraryMock.mockResolvedValue([makeEntry(10), makeEntry(1)]);

    await renderRecommendations();

    expect(recsMock).toHaveBeenCalledWith("SERIES");
    expect(screen.getByRole("link", { name: "TV Series" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Video Games" })).toHaveAttribute(
      "href",
      "/recommendations?target=GAME",
    );
    expect(screen.getByRole("link", { name: "Movies" })).toHaveAttribute(
      "href",
      "/recommendations?target=MOVIE",
    );

    expect(screen.getByRole("link", { name: "Severance" })).toHaveAttribute("href", "/title/1");
    expect(screen.getByAltText("Poster of Severance")).toHaveAttribute(
      "src",
      "https://images.test/1.jpg",
    );
    expect(screen.getByRole("link", { name: "Dark" })).toHaveAttribute("href", "/title/2");
    expect(screen.getByText(/In Library/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+ Add to Library" })).toBeInTheDocument();
  });

  it.each([
    ["GAME", "Video Games", 20, "Disco Elysium"],
    ["MOVIE", "Movies", 30, "Arrival"],
  ] as const)(
    "switches to the requested %s target",
    async (target, label, id, title) => {
      recsMock.mockResolvedValue([makeItem(id, title, target)]);
      libraryMock.mockResolvedValue([makeEntry(10)]);

      await renderRecommendations({ target });

      expect(recsMock).toHaveBeenCalledWith(target);
      expect(screen.getByRole("link", { name: label })).toHaveAttribute("aria-current", "page");
      expect(screen.getByRole("link", { name: title })).toHaveAttribute("href", `/title/${id}`);
    },
  );

  it("falls back to SERIES for invalid target values", async () => {
    recsMock.mockResolvedValue([]);
    libraryMock.mockResolvedValue([]);

    await renderRecommendations({ target: "INVALID" });

    expect(recsMock).toHaveBeenCalledWith("SERIES");
  });

  it("shows the empty library state when the user has an empty library and no recommendations", async () => {
    recsMock.mockResolvedValue([]);
    libraryMock.mockResolvedValue([]);

    await renderRecommendations();

    const status = screen.getByRole("status");
    expect(status).toHaveTextContent("Your library is empty");
    expect(screen.getByRole("link", { name: "Browse catalog" })).toHaveAttribute(
      "href",
      "/search",
    );
  });

  it("shows an empty state when the user has library items but no recommendations for the target", async () => {
    recsMock.mockResolvedValue([]);
    libraryMock.mockResolvedValue([makeEntry(10)]);

    await renderRecommendations({ target: "GAME" });

    expect(screen.getByRole("status")).toHaveTextContent("No recommendations available yet");
  });

  it("renders the shared 503 unavailable error state with retry when backend returns 503", async () => {
    recsMock.mockRejectedValue(new BackendError(503, "External service is unavailable"));
    libraryMock.mockResolvedValue([]);

    await renderRecommendations();

    expect(screen.getByRole("alert")).toHaveTextContent("Service unavailable");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("rethrows 401/session-expired NEXT_REDIRECT from recommendations or library without swallowing it", async () => {
    const redirectErr = Object.assign(new Error("NEXT_REDIRECT"), {
      digest: "NEXT_REDIRECT;/session-expired",
    });
    recsMock.mockRejectedValueOnce(redirectErr);
    libraryMock.mockResolvedValue([]);

    await expect(
      RecommendationsPage({ searchParams: Promise.resolve({ target: "SERIES" }) }),
    ).rejects.toBe(redirectErr);

    recsMock.mockResolvedValueOnce([]);
    libraryMock.mockRejectedValueOnce(redirectErr);

    await expect(
      RecommendationsPage({ searchParams: Promise.resolve({ target: "SERIES" }) }),
    ).rejects.toBe(redirectErr);
  });

  it("renders the shared loading state on the recommendations loading screen", () => {
    render(<RecommendationsLoading />);

    expect(screen.getByRole("heading", { name: "Recommendations" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Loading recommendations...");
  });
});
