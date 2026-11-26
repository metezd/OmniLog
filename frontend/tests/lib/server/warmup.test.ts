// @vitest-environment node
import { delay, http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { WARMUP_INTERVAL_MS, resetWarmUp, warmUpBackend } from "@/lib/server/warmup";
import { server } from "../../mocks/server";

const BASE = "http://backend.test";

// A free backend on Render sleeps when nobody uses it. The login and register pages wake it up
// while the user fills in the form, so the first real request does not wait for the start (#250).

let pings = 0;

beforeEach(() => {
  vi.stubEnv("BACKEND_URL", BASE);
  resetWarmUp();
  pings = 0;
  server.use(
    http.get(`${BASE}/health`, () => {
      pings += 1;
      return HttpResponse.json({ status: "healthy" });
    }),
  );
});

afterEach(() => {
  vi.unstubAllEnvs();
});

async function settle() {
  // The ping is not awaited by the page, so give it time to reach the mock
  await new Promise((resolve) => setTimeout(resolve, 20));
}

describe("warmUpBackend", () => {
  it("sends one GET /health to the backend", async () => {
    expect(warmUpBackend(1_000)).toBe(true);
    await settle();

    expect(pings).toBe(1);
  });

  it("sends no second ping within the interval", async () => {
    warmUpBackend(1_000);
    expect(warmUpBackend(1_000 + WARMUP_INTERVAL_MS - 1)).toBe(false);
    await settle();

    expect(pings).toBe(1);
  });

  it("pings again after the interval", async () => {
    warmUpBackend(1_000);
    expect(warmUpBackend(1_000 + WARMUP_INTERVAL_MS)).toBe(true);
    await settle();

    expect(pings).toBe(2);
  });

  it("waits at most one minute between pings, so a page view cannot flood the backend", () => {
    expect(WARMUP_INTERVAL_MS).toBe(60_000);
  });

  it("returns at once and does not wait for the answer", async () => {
    server.use(
      http.get(`${BASE}/health`, async () => {
        await delay(5_000);
        return HttpResponse.json({ status: "healthy" });
      }),
    );

    const started = performance.now();
    warmUpBackend(1_000);

    expect(performance.now() - started).toBeLessThan(50);
  });

  it("never throws when the backend is down", async () => {
    server.use(http.get(`${BASE}/health`, () => HttpResponse.error()));
    const unhandled = vi.fn();
    process.on("unhandledRejection", unhandled);

    expect(() => warmUpBackend(1_000)).not.toThrow();
    await settle();

    process.off("unhandledRejection", unhandled);
    expect(unhandled).not.toHaveBeenCalled();
  });

  it("never throws when BACKEND_URL is missing in production", async () => {
    vi.stubEnv("BACKEND_URL", "");
    vi.stubEnv("NODE_ENV", "production");
    const unhandled = vi.fn();
    process.on("unhandledRejection", unhandled);

    expect(() => warmUpBackend(1_000)).not.toThrow();
    await settle();

    process.off("unhandledRejection", unhandled);
    expect(unhandled).not.toHaveBeenCalled();
  });
});
