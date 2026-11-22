import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TitleDetailPage from "@/app/title/[id]/page";
import { BackendError } from "@/lib/server/backend";
import { getTitleDetails } from "@/lib/server/catalog";
import { getChapterProgress } from "@/lib/server/chapters";
import { getLibrary } from "@/lib/server/library";
import { getReview } from "@/lib/server/reviews";
import type { LibraryEntry, MediaDetail } from "@/types/api";

vi.mock("@/lib/server/catalog", () => ({ getTitleDetails: vi.fn() }));
vi.mock("@/lib/server/library", () => ({ getLibrary: vi.fn() }));
vi.mock("@/lib/server/chapters", () => ({ getChapterProgress: vi.fn() }));
vi.mock("@/lib/server/reviews", () => ({ getReview: vi.fn() }));
vi.mock("@/lib/actions/library", () => ({
  addToLibraryAction: vi.fn(),
  updateLibraryEntryAction: vi.fn(),
  removeLibraryEntryAction: vi.fn(),
  submitReviewAction: vi.fn(),
}));
vi.mock("@/lib/actions/chapters", () => ({
  rateChapterAction: vi.fn(),
  logPlaytimeAction: vi.fn(),
  recordDecisionAction: vi.fn(),
}));
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));

const catalogMock = vi.mocked(getTitleDetails);
const libraryMock = vi.mocked(getLibrary);
const progressMock = vi.mocked(getChapterProgress);
const reviewMock = vi.mocked(getReview);

function makeDetail(overrides: Partial<MediaDetail> = {}): MediaDetail {
  return {
    id: 42,
    title: "Life is Strange",
    media_type: "GAME",
    poster_url: "https://images.test/lis.jpg",
    release_date: "2015-01-30",
    external_api_id: 100,
    genres: ["Adventure", "Narrative"],
    description: "A photography student discovers she can rewind time.",
    seasons: [],
    chapters: [
      {
        id: 101,
        number: 1,
        kind: "CHAPTER",
        title: "Chrysalis",
        release_date: "2015-01-30",
        runtime_minutes: 120,
        decision_points: [],
      },
    ],
    ...overrides,
  };
}

function makeEntry(media_item_id = 42): LibraryEntry {
  return {
    id: 10,
    user_id: 1,
    media_item_id,
    status: "IN_PROGRESS",
    rating: 9,
    updated_at: null,
    media_item: {
      id: media_item_id,
      title: "Life is Strange",
      media_type: "GAME",
      poster_url: null,
      release_date: "2015-01-30",
      external_api_id: 100,
      genres: ["Adventure"],
    },
  };
}

async function renderTitle(id = "42") {
  render(await TitleDetailPage({ params: Promise.resolve({ id }) }));
}

describe("TitleDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders header details, chapters and Add to Library button when title is not in library", async () => {
    catalogMock.mockResolvedValue(makeDetail());
    libraryMock.mockResolvedValue([]);

    await renderTitle("42");

    expect(screen.getByRole("heading", { name: "Life is Strange" })).toBeInTheDocument();
    expect(screen.getByAltText("Poster of Life is Strange")).toHaveAttribute("src", "https://images.test/lis.jpg");
    expect(screen.getByText("Game")).toBeInTheDocument();
    expect(screen.getByText("2015")).toBeInTheDocument();
    expect(screen.getByText("Adventure")).toBeInTheDocument();
    expect(screen.getByText("Narrative")).toBeInTheDocument();
    expect(screen.getByText("A photography student discovers she can rewind time.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+ Add to Library" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Chapters & Narrative Choices" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Chrysalis" })).toBeInTheDocument();
  });

  it("renders LibraryControls, seasons and episodes when a series is in the user's library", async () => {
    catalogMock.mockResolvedValue(
      makeDetail({
        id: 7,
        title: "Severance",
        media_type: "SERIES",
        chapters: [],
        seasons: [
          {
            id: 1,
            season_number: 1,
            title: "Season One",
            air_date: "2022-02-18",
            episodes: [
              {
                id: 201,
                number: 1,
                kind: "EPISODE",
                title: "Good News About Hell",
                release_date: "2022-02-18",
                runtime_minutes: 57,
                decision_points: [],
              },
            ],
          },
        ],
      }),
    );
    libraryMock.mockResolvedValue([makeEntry(7)]);
    reviewMock.mockResolvedValue(null);
    progressMock.mockResolvedValue({
      library_entry_id: 10,
      chapter_id: 201,
      rating: 5,
      playtime_minutes: 57,
      updated_at: null,
      choice: null,
      decided_at: null,
      decisions: [],
    });

    await renderTitle("7");

    expect(screen.getByRole("heading", { name: "Your Library Status" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Seasons & Episodes" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Season 1: Season One" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Good News About Hell" })).toBeInTheDocument();
    expect(screen.getByText("★ 5/5")).toBeInTheDocument();
    expect(screen.getByText("57 min logged")).toBeInTheDocument();
  });

  it("handles a title without genres, description, poster, release date or chapters using shared states", async () => {
    catalogMock.mockResolvedValue(
      makeDetail({
        poster_url: null,
        release_date: null,
        genres: [],
        description: null,
        seasons: [],
        chapters: [],
      }),
    );
    libraryMock.mockResolvedValue([]);

    await renderTitle("42");

    expect(screen.getByText("No poster")).toBeInTheDocument();
    expect(screen.getByText("Release date unknown")).toBeInTheDocument();
    expect(screen.getByText("No genres listed")).toBeInTheDocument();
    expect(screen.getByText("No description available.")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("No chapters or episodes");
  });

  it("shows not_found ErrorState when the id parameter is invalid", async () => {
    await renderTitle("invalid-id");
    expect(screen.getByRole("alert")).toHaveTextContent("This catalog title does not exist.");
  });

  it("shows not_found ErrorState when backend returns 404", async () => {
    catalogMock.mockRejectedValueOnce(new BackendError(404, "Title not found"));
    libraryMock.mockResolvedValueOnce([]);
    await renderTitle("999");
    expect(screen.getByRole("alert")).toHaveTextContent("We could not find what you were looking for.");
  });
});
