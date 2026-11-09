import { describe, expect, it } from "vitest";

import { MEDIA_TYPE_LABELS, releaseYear, STATUS_LABELS } from "@/lib/media";

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
