import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import StatsPage from "@/app/stats/page";
import { BackendError } from "@/lib/server/backend";
import type { StatsResponse } from "@/types/api";

const { getStats } = vi.hoisted(() => ({ getStats: vi.fn() }));

vi.mock("server-only", () => ({}));
vi.mock("@/lib/server/stats", () => ({ getStats }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));

function makeStats(overrides: Partial<StatsResponse> = {}): StatsResponse {
  return {
    total_items: 12,
    media_split: { GAME: 5, SERIES: 4, MOVIE: 3 },
    rating_distribution: { "10": 3, "8": 1 },
    genre_breakdown: [
      { genre: "RPG", count: 4 },
      { genre: "Drama", count: 2 },
    ],
    playtime: { total_minutes: 150, histogram: [{ bucket: "0-30", count: 3 }] },
    ...overrides,
  };
}

// The page is an async Server Component, so it is called and awaited before it is rendered.
async function renderPage() {
  render(await StatsPage());
}

beforeEach(() => {
  getStats.mockReset();
});

describe("StatsPage", () => {
  it("shows the empty state for a user without data", async () => {
    getStats.mockResolvedValue(makeStats({ total_items: 0 }));

    await renderPage();

    expect(screen.getByRole("status")).toHaveTextContent("No analytics data yet");
    expect(screen.queryByText("Media Split Ratio")).not.toBeInTheDocument();
  });

  it("shows the totals", async () => {
    getStats.mockResolvedValue(makeStats());

    await renderPage();

    expect(screen.getByText("Total Tracked Titles").parentElement).toHaveTextContent(
      /Total Tracked Titles\s*12/,
    );
    expect(screen.getByText("Total Logged Time").parentElement).toHaveTextContent(
      /Total Logged Time\s*2\.5 hrs/,
    );
    expect(screen.getByText("(150 min)")).toBeInTheDocument();
    expect(screen.getByText("Video Games").parentElement).toHaveTextContent(/Video Games\s*5/);
    // Series and movies are added together: 4 + 3
    expect(screen.getByText("TV Series & Movies").parentElement).toHaveTextContent(
      /TV Series & Movies\s*7/,
    );
  });

  it("shows the count and the percentage of every media type", async () => {
    getStats.mockResolvedValue(makeStats());

    await renderPage();

    expect(screen.getByText("5 (42%)")).toBeInTheDocument();
    expect(screen.getByText("4 (33%)")).toBeInTheDocument();
    expect(screen.getByText("3 (25%)")).toBeInTheDocument();
  });

  it("shows the genres, and only the eight most frequent ones", async () => {
    getStats.mockResolvedValue(makeStats());
    await renderPage();

    expect(screen.getByText("RPG")).toBeInTheDocument();
    expect(screen.getByText("4 titles")).toBeInTheDocument();
    expect(screen.getByText("Drama")).toBeInTheDocument();
    expect(screen.getByText("2 titles")).toBeInTheDocument();
  });

  it("cuts the genre list after eight", async () => {
    const genres = Array.from({ length: 10 }, (_, index) => ({
      genre: `Genre ${index}`,
      count: 10 - index,
    }));
    getStats.mockResolvedValue(makeStats({ genre_breakdown: genres }));

    await renderPage();

    expect(screen.getByText("Genre 7")).toBeInTheDocument();
    expect(screen.queryByText("Genre 8")).not.toBeInTheDocument();
  });

  it("says so when no genres are tagged yet", async () => {
    getStats.mockResolvedValue(makeStats({ genre_breakdown: [] }));

    await renderPage();

    expect(screen.getByText("No genres tagged yet.")).toBeInTheDocument();
  });

  it("shows a column for each rating from 1 to 10", async () => {
    getStats.mockResolvedValue(makeStats());

    await renderPage();

    for (let star = 1; star <= 10; star += 1) {
      expect(screen.getByText(`${star}\u2605`)).toBeInTheDocument();
    }
    // The count sits above the label in the same column
    expect(screen.getByText("10\u2605").parentElement).toHaveTextContent("310\u2605");
    expect(screen.getByText("8\u2605").parentElement).toHaveTextContent("18\u2605");
  });

  it("shows the playtime histogram", async () => {
    getStats.mockResolvedValue(makeStats());

    await renderPage();

    expect(screen.getByText("0-30")).toBeInTheDocument();
    expect(screen.getByText("3 chapters")).toBeInTheDocument();
  });

  it("says so when no chapter playtime is logged", async () => {
    getStats.mockResolvedValue(
      makeStats({ playtime: { total_minutes: 0, histogram: [] } }),
    );

    await renderPage();

    expect(screen.getByText(/No chapter playtime logged yet/)).toBeInTheDocument();
  });

  it.each([
    [503, "Service unavailable"],
    [404, "Not found"],
    [500, "Something went wrong"],
  ])("shows an error state for backend status %i", async (status, title) => {
    getStats.mockRejectedValue(new BackendError(status, "x"));

    await renderPage();

    expect(screen.getByRole("alert")).toHaveTextContent(title);
    // The page frame stays, so the user knows where they are
    expect(screen.getByRole("heading", { name: "Analytics Dashboard" })).toBeInTheDocument();
  });

  it("lets a redirect through instead of showing an error", async () => {
    const redirectSignal = Object.assign(new Error("NEXT_REDIRECT"), {
      digest: "NEXT_REDIRECT;replace;/login;307;",
    });
    getStats.mockRejectedValue(redirectSignal);

    await expect(StatsPage()).rejects.toBe(redirectSignal);
  });

  it("throws errors it does not know", async () => {
    getStats.mockRejectedValue(new Error("boom"));

    await expect(StatsPage()).rejects.toThrow("boom");
  });
});