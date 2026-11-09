// @vitest-environment node
// Axios runs here as it does on the server, in plain Node and without a simulated browser.
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { api, getErrorMessage } from "@/lib/api";
import { server } from "../mocks/server";

describe("getErrorMessage", () => {
  it("returns the detail text of an error answer of the backend", async () => {
    server.use(
      http.get("http://localhost:8000/boom", () =>
        HttpResponse.json({ detail: "Invalid credentials" }, { status: 401 }),
      ),
    );

    const error = await api.get("/boom").catch((caught: unknown) => caught);

    expect(getErrorMessage(error)).toBe("Invalid credentials");
  });

  it("falls back to the message of the request error when there is no detail text", async () => {
    server.use(http.get("http://localhost:8000/boom", () => new HttpResponse(null, { status: 500 })));

    const error = await api.get("/boom").catch((caught: unknown) => caught);

    expect(getErrorMessage(error)).toBe("Request failed with status code 500");
  });

  it("returns the message of an ordinary error", () => {
    expect(getErrorMessage(new Error("Boom"))).toBe("Boom");
  });

  it("returns a general text for anything else", () => {
    expect(getErrorMessage("text")).toBe("Something went wrong");
    expect(getErrorMessage(undefined)).toBe("Something went wrong");
  });
});
