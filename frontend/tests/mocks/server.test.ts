import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "./server";

// These tests check the test setup itself, so a broken setup is noticed at once.
describe("the fake backend", () => {
  it("answers a request that has a handler", async () => {
    server.use(http.get("http://localhost:8000/health", () => HttpResponse.json({ status: "healthy" })));

    const response = await fetch("http://localhost:8000/health");

    expect(await response.json()).toEqual({ status: "healthy" });
  });

  it("fails a request that has no handler", async () => {
    await expect(fetch("http://localhost:8000/not-mocked")).rejects.toThrow();
  });

  it("forgets the handlers of the previous test", async () => {
    // The handler of the first test is gone, so this request has no handler
    await expect(fetch("http://localhost:8000/health")).rejects.toThrow();
  });
});
