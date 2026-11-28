import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PosterImage from "@/components/layout/PosterImage";

const TMDB_POSTER = "https://image.tmdb.org/t/p/w500/abc.jpg";
const IGDB_COVER = "https://images.igdb.com/igdb/image/upload/t_cover_big/co1r7f.jpg";

describe("PosterImage (#451)", () => {
  it("loads a card poster lazily, with a 2:3 size and the smaller TMDB file", () => {
    render(<PosterImage posterUrl={TMDB_POSTER} title="Dune" />);

    const poster = screen.getByAltText("Poster of Dune");
    expect(poster).toHaveAttribute("loading", "lazy");
    expect(poster).toHaveAttribute("decoding", "async");
    expect(poster).toHaveAttribute("width", "342");
    expect(poster).toHaveAttribute("height", "513");
    expect(poster).toHaveAttribute("referrerpolicy", "no-referrer");
    expect(poster).toHaveAttribute(
      "src",
      `/api/poster?url=${encodeURIComponent("https://image.tmdb.org/t/p/w342/abc.jpg")}`,
    );
  });

  it("loads the poster of the title page at once, in the larger TMDB size", () => {
    render(<PosterImage posterUrl={TMDB_POSTER} title="Dune" size="detail" />);

    const poster = screen.getByAltText("Poster of Dune");
    expect(poster).toHaveAttribute("loading", "eager");
    expect(poster).toHaveAttribute("decoding", "async");
    expect(poster).toHaveAttribute("width", "500");
    expect(poster).toHaveAttribute("height", "750");
    expect(poster).toHaveAttribute("src", `/api/poster?url=${encodeURIComponent(TMDB_POSTER)}`);
  });

  it("keeps the IGDB cover size", () => {
    render(<PosterImage posterUrl={IGDB_COVER} title="Hades" />);

    expect(screen.getByAltText("Poster of Hades")).toHaveAttribute(
      "src",
      `/api/poster?url=${encodeURIComponent(IGDB_COVER)}`,
    );
  });

  it("shows the placeholder without a poster and when the file does not load", () => {
    const { unmount } = render(<PosterImage posterUrl={null} title="Dune" />);
    expect(screen.getByText("No poster")).toBeInTheDocument();
    unmount();

    render(<PosterImage posterUrl={TMDB_POSTER} title="Dune" />);
    fireEvent.error(screen.getByAltText("Poster of Dune"));
    expect(screen.getByText("No poster")).toBeInTheDocument();
    expect(screen.queryByAltText("Poster of Dune")).not.toBeInTheDocument();
  });
});
