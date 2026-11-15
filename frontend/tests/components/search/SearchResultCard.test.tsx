import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import SearchResultCard from "@/components/search/SearchResultCard";
import type { MediaItem } from "@/types/api";

vi.mock("@/lib/actions/library", () => ({
  addToLibraryAction: vi.fn(),
}));

function makeItem(overrides: Partial<MediaItem> = {}): MediaItem {
  return {
    id: 42,
    title: "Cyberpunk 2077",
    media_type: "GAME",
    poster_url: "https://images.test/cp2077.jpg",
    release_date: "2020-12-10",
    external_api_id: 1077,
    genres: ["RPG", "Action", "Sci-Fi", "Open World"],
    ...overrides,
  };
}

describe("SearchResultCard", () => {
  it("renders poster, title link, release year, up to 3 genres and the Add to Library button", () => {
    render(<SearchResultCard item={makeItem()} inLibrary={false} />);

    const link = screen.getByRole("link", { name: "Cyberpunk 2077" });
    expect(link).toHaveAttribute("href", "/title/42");
    expect(screen.getByAltText("Poster of Cyberpunk 2077")).toHaveAttribute("src", "https://images.test/cp2077.jpg");
    expect(screen.getByText("Game")).toBeInTheDocument();
    expect(screen.getByText("2020")).toBeInTheDocument();
    expect(screen.getByText("RPG")).toBeInTheDocument();
    expect(screen.getByText("Action")).toBeInTheDocument();
    expect(screen.getByText("Sci-Fi")).toBeInTheDocument();
    expect(screen.queryByText("Open World")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+ Add to Library" })).toBeInTheDocument();
  });

  it("shows fallback text when poster and release date are missing and shows In Library badge when already added", () => {
    render(
      <SearchResultCard
        item={makeItem({ poster_url: null, release_date: null, media_type: "SERIES", genres: [] })}
        inLibrary={true}
      />,
    );

    expect(screen.getByText("No poster")).toBeInTheDocument();
    expect(screen.getByText("Release date unknown")).toBeInTheDocument();
    expect(screen.getByText("TV Series")).toBeInTheDocument();
    expect(screen.getByText(/In Library/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "+ Add to Library" })).not.toBeInTheDocument();
  });
});
