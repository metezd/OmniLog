// @vitest-environment node
import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET } from "@/app/api/poster/route";

const fetchMock = vi.fn();

function call(url?: string) {
  const target = new URL("http://localhost:3000/api/poster");
  if (url !== undefined) {
    target.searchParams.set("url", url);
  }
  return GET(new NextRequest(target));
}

function imageResponse(contentType: string | null = "image/png") {
  const headers = contentType ? { "Content-Type": contentType } : undefined;
  return new Response(new Uint8Array([1, 2, 3]), { status: 200, headers });
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("GET /api/poster", () => {
  describe("rejects a bad request with 400", () => {
    it("when the url parameter is missing", async () => {
      const response = await call();

      expect(response.status).toBe(400);
      expect(fetchMock).not.toHaveBeenCalled();
    });

    it("when the url parameter is too long", async () => {
      const response = await call(`https://image.tmdb.org/${"a".repeat(500)}.jpg`);

      expect(response.status).toBe(400);
      expect(fetchMock).not.toHaveBeenCalled();
    });

    it("when the url parameter is not a URL", async () => {
      const response = await call("not a url");

      expect(response.status).toBe(400);
      expect(fetchMock).not.toHaveBeenCalled();
    });
  });

  describe("rejects a disallowed target with 403", () => {
    it.each([
      ["a plain http URL", "http://image.tmdb.org/t/p/w500/abc.jpg"],
      ["a host that is not on the allowlist", "https://evil.example.com/t/p/w500/abc.jpg"],
      ["a look-alike host", "https://image.tmdb.org.evil.example.com/abc.jpg"],
      ["a path with unsafe characters", "https://image.tmdb.org/t/p/w500/a%20b.jpg"],
    ])("for %s", async (_label, url) => {
      const response = await call(url);

      expect(response.status).toBe(403);
      expect(fetchMock).not.toHaveBeenCalled();
    });
  });

  describe("streams an allowed poster", () => {
    it("returns the image with the safe headers", async () => {
      fetchMock.mockResolvedValueOnce(imageResponse("image/png"));

      const response = await call("https://image.tmdb.org/t/p/w500/abc.jpg");

      expect(response.status).toBe(200);
      expect(response.headers.get("Content-Type")).toBe("image/png");
      expect(response.headers.get("Cache-Control")).toContain("max-age=86400");
      expect(response.headers.get("X-Content-Type-Options")).toBe("nosniff");
      expect(new Uint8Array(await response.arrayBuffer())).toEqual(new Uint8Array([1, 2, 3]));
    });

    it("asks the upstream host for the path only, without the query string", async () => {
      fetchMock.mockResolvedValueOnce(imageResponse());

      await call("https://image.tmdb.org/t/p/w500/abc.jpg?token=secret");

      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(fetchMock.mock.calls[0][0]).toBe("https://image.tmdb.org/t/p/w500/abc.jpg");
    });

    it("falls back to image/jpeg when the upstream sends no content type", async () => {
      fetchMock.mockResolvedValueOnce(imageResponse(null));

      const response = await call("https://image.tmdb.org/t/p/w500/abc.jpg");

      expect(response.status).toBe(200);
      expect(response.headers.get("Content-Type")).toBe("image/jpeg");
    });
  });

  describe("handles upstream problems without leaking details", () => {
    it("passes a 404 through", async () => {
      fetchMock.mockResolvedValueOnce(new Response("missing", { status: 404 }));

      const response = await call("https://image.tmdb.org/t/p/w500/abc.jpg");

      expect(response.status).toBe(404);
    });

    it("turns another upstream error into 502", async () => {
      fetchMock.mockResolvedValueOnce(new Response("boom", { status: 500 }));

      const response = await call("https://image.tmdb.org/t/p/w500/abc.jpg");

      expect(response.status).toBe(502);
      expect(await response.text()).not.toContain("boom");
    });

    it("refuses an upstream answer that is not an image", async () => {
      fetchMock.mockResolvedValueOnce(
        new Response("<html></html>", { status: 200, headers: { "Content-Type": "text/html" } }),
      );

      const response = await call("https://image.tmdb.org/t/p/w500/abc.jpg");

      expect(response.status).toBe(502);
    });

    it("turns a network failure into 502", async () => {
      fetchMock.mockRejectedValueOnce(new Error("socket hang up"));

      const response = await call("https://image.tmdb.org/t/p/w500/abc.jpg");

      expect(response.status).toBe(502);
      expect(await response.text()).not.toContain("socket hang up");
    });
  });
});