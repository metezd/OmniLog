import { describe, expect, it } from "vitest";

import { MEDIA_TYPE_LABELS, releaseYear, resolvePosterUrl, STATUS_LABELS } from "@/lib/media";

describe("releaseYear", () => {
  it.each([
    ["2015-01-30", "2015"],
    ["2015", "2015"],
  ])("reads the year of %s", (date, year) => {
    expect(releaseYear(date)).toBe(year);
  });

  it.each([null, "", "unknown", "15-01-30"])("returns null for %s", (date) => {
    expect(releaseYear(date)).toBeNull();
  });
});

describe("labels", () => {
  it("has a label for every status and every media type of the backend", () => {
    expect(Object.keys(STATUS_LABELS).sort()).toEqual(["COMPLETED", "DROPPED", "IN_PROGRESS", "PLAN_TO_WATCH"]);
    expect(Object.keys(MEDIA_TYPE_LABELS).sort()).toEqual(["GAME", "MOVIE", "SERIES"]);
  });
});

describe("resolvePosterUrl", () => {
  it("routes known catalog CDN URLs through /api/poster", () => {
    expect(resolvePosterUrl("https://image.tmdb.org/t/p/w500/abc.jpg")).toBe(
      "/api/poster?url=https%3A%2F%2Fimage.tmdb.org%2Ft%2Fp%2Fw500%2Fabc.jpg",
    );
    expect(resolvePosterUrl("https://images.igdb.com/igdb/image/upload/t_cover_big/co1r7f.jpg")).toBe(
      "/api/poster?url=https%3A%2F%2Fimages.igdb.com%2Figdb%2Fimage%2Fupload%2Ft_cover_big%2Fco1r7f.jpg",
    );
  });

  it("returns null for null and preserves non-CDN URLs", () => {
    expect(resolvePosterUrl(null)).toBeNull();
    expect(resolvePosterUrl("https://images.test/cp2077.jpg")).toBe("https://images.test/cp2077.jpg");
  });
});
