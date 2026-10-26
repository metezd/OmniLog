// @vitest-environment node
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "./server";

// Server code (Server Actions, the backend client) is tested in plain Node, without a browser.
// This file shows the pattern: the line at the top switches the environment for this file.
describe("the Node environment", () => {
  it("has no browser objects", () => {
    expect(typeof document).toBe("undefined");
    expect(typeof window).toBe("undefined");
  });

  it("can use the fake backend", async () => {
    server.use(http.get("http://backend.test/ping", () => HttpResponse.json({ ok: true })));

    const response = await fetch("http://backend.test/ping");

    expect(await response.json()).toEqual({ ok: true });
  });
});
