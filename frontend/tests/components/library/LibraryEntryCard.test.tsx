import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import LibraryEntryCard from "@/components/library/LibraryEntryCard";
import type { LibraryEntry } from "@/types/api";

function entry(overrides: Partial<LibraryEntry> = {}, item: Partial<LibraryEntry["media_item"]> = {}): LibraryEntry {
  return {
    id: 1,
    user_id: 7,
    media_item_id: 4,
    status: "IN_PROGRESS",
    rating: 8,
    updated_at: "2026-10-20T10:00:00Z",
    media_item: {
      id: 4,
      title: "Life is Strange",
      media_type: "GAME",
      poster_url: "https://images.test/lis.jpg",
      release_date: "2015-01-30",
      external_api_id: 1,
      genres: ["Adventure", "Indie"],
      ...item,
    },
    ...overrides,
  };
}

describe("LibraryEntryCard", () => {
  it("shows the poster, title, type, status, year and rating", () => {
    render(<LibraryEntryCard entry={entry()} />);

    expect(screen.getByRole("heading", { name: "Life is Strange" })).toBeInTheDocument();
    expect(screen.getByAltText("Poster of Life is Strange")).toHaveAttribute("src", "https://images.test/lis.jpg");
    expect(screen.getByText("Game")).toBeInTheDocument();
    expect(screen.getByText("In progress")).toBeInTheDocument();
    expect(screen.getByText("2015")).toBeInTheDocument();
    expect(screen.getByText("★ 8/10")).toBeInTheDocument();
  });

  it("says so when a title has no rating, no poster or no release date", () => {
    render(
      <LibraryEntryCard
        entry={entry({ rating: null, status: "PLAN_TO_WATCH" }, { poster_url: null, release_date: null, media_type: "SERIES" })}
      />,
    );

    expect(screen.getByText("Not rated")).toBeInTheDocument();
    expect(screen.getByText("No poster")).toBeInTheDocument();
    expect(screen.getByText("Release date unknown")).toBeInTheDocument();
    expect(screen.getByText("TV Series")).toBeInTheDocument();
    expect(screen.getByText("Plan to watch")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
