import { beforeEach, describe, expect, it } from "vitest";

import {
  POSTER_LIMIT_PER_WINDOW,
  POSTER_WINDOW_MS,
  clientAddress,
  resetPosterLimit,
  takePosterSlot,
} from "@/lib/server/poster-limit";

beforeEach(() => {
  resetPosterLimit();
});

describe("clientAddress", () => {
  it("takes the right-most entry, the one the proxy wrote", () => {
    expect(clientAddress("1.1.1.1, 203.0.113.7")).toBe("203.0.113.7");
  });

  it("puts requests without a usable header under one key", () => {
    expect(clientAddress(null)).toBe("unknown");
    expect(clientAddress("")).toBe("unknown");
    expect(clientAddress("not an address")).toBe("unknown");
  });
});

describe("takePosterSlot", () => {
  it("never limits one page of 20 posters", () => {
    expect(POSTER_LIMIT_PER_WINDOW).toBeGreaterThanOrEqual(20);
    for (let i = 0; i < 20; i += 1) {
      expect(takePosterSlot("203.0.113.7", 0)).toBeNull();
    }
  });

  it("limits an address over the limit and says when to retry", () => {
    for (let i = 0; i < POSTER_LIMIT_PER_WINDOW; i += 1) {
      expect(takePosterSlot("203.0.113.7", 0)).toBeNull();
    }
    expect(takePosterSlot("203.0.113.7", 15_000)).toBe(45);
    // Another address has its own count
    expect(takePosterSlot("198.51.100.1", 15_000)).toBeNull();
  });

  it("starts a new window after a minute", () => {
    for (let i = 0; i < POSTER_LIMIT_PER_WINDOW; i += 1) takePosterSlot("203.0.113.7", 0);
    expect(takePosterSlot("203.0.113.7", POSTER_WINDOW_MS - 1)).toBe(1);
    expect(takePosterSlot("203.0.113.7", POSTER_WINDOW_MS)).toBeNull();
  });
});
