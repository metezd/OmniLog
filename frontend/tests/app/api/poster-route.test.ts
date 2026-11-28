// @vitest-environment node
import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET } from "@/app/api/poster/route";
import { POSTER_LIMIT_PER_WINDOW, resetPosterLimit } from "@/lib/server/poster-limit";

const fetchMock = vi.fn();

const POSTER = "https://image.tmdb.org/t/p/w500/abc.jpg";
const MAX_POSTER_BYTES = 2 * 1024 * 1024;

function call(url?: string, forwardedFor?: string) {
  const target = new URL("http://localhost:3000/api/poster");
  if (url !== undefined) {
    target.searchParams.set("url", url);
  }
  const headers = forwardedFor === undefined ? undefined : { "X-Forwarded-For": forwardedFor };
  return GET(new NextRequest(target, { headers }));
}

/** An upstream body that sends `chunks` pieces of `chunkSize` bytes and notes when it is cancelled. */
function chunkedBody(chunks: number, chunkSize: number) {
  const state = { sent: 0, cancelled: false };
  const stream = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (state.sent >= chunks) {
        controller.close();
        return;
      }
      state.sent += 1;
      controller.enqueue(new Uint8Array(chunkSize));
    },
    cancel() {
      state.cancelled = true;
    },
  });
  return { stream, state };
}

function imageResponse(contentType: string | null = "image/png") {
  const headers = contentType ? { "Content-Type": contentType } : undefined;
  return new Response(new Uint8Array([1, 2, 3]), { status: 200, headers });
}

beforeEach(() => {
  resetPosterLimit();
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

    it("does not follow a redirect of the upstream host", async () => {
      // An allowed CDN that answers with a redirect could send the server to any address, for
      // example one inside its own network. fetch follows redirects unless it is told not to.
      fetchMock.mockResolvedValueOnce(imageResponse());

      await call("https://image.tmdb.org/t/p/w500/abc.jpg");

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const init = fetchMock.mock.calls[0][1] as RequestInit | undefined;
      expect(init?.redirect).toBe("error");
    });

    it("turns a refused redirect into 502", async () => {
      // With redirect "error", fetch rejects with a TypeError when the upstream redirects
      fetchMock.mockRejectedValueOnce(new TypeError("fetch failed: redirect mode is set to error"));

      const response = await call("https://image.tmdb.org/t/p/w500/abc.jpg");

      expect(response.status).toBe(502);
      expect(await response.text()).not.toContain("redirect");
    });

    it("turns a network failure into 502", async () => {
      fetchMock.mockRejectedValueOnce(new Error("socket hang up"));

      const response = await call("https://image.tmdb.org/t/p/w500/abc.jpg");

      expect(response.status).toBe(502);
      expect(await response.text()).not.toContain("socket hang up");
    });
  });

  describe("passes on raster posters only", () => {
    it.each(["image/jpeg", "image/png", "image/webp", "image/jpeg; charset=binary"])(
      "accepts %s",
      async (type) => {
        fetchMock.mockResolvedValueOnce(imageResponse(type));

        const response = await call(POSTER);

        expect(response.status).toBe(200);
        expect(response.headers.get("Content-Type")).toBe(type.split(";")[0]);
      },
    );

    it.each(["image/svg+xml", "image/gif", "image/x-icon"])("refuses %s with 502", async (type) => {
      fetchMock.mockResolvedValueOnce(
        new Response('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', {
          status: 200,
          headers: { "Content-Type": type },
        }),
      );

      const response = await call(POSTER);

      expect(response.status).toBe(502);
      expect(await response.text()).not.toContain("<script>");
    });
  });

  describe("limits the size of a poster", () => {
    it("streams the upstream body instead of reading it first", async () => {
      const { stream, state } = chunkedBody(4, 1024);
      fetchMock.mockResolvedValueOnce(
        new Response(stream, { status: 200, headers: { "Content-Type": "image/jpeg" } }),
      );

      const response = await call(POSTER);

      expect(response.status).toBe(200);
      // The answer is ready before the whole upstream body was read
      expect(state.sent).toBeLessThan(4);
      expect((await response.arrayBuffer()).byteLength).toBe(4 * 1024);
    });

    it("refuses an answer whose Content-Length is over the limit, without reading it", async () => {
      const { stream, state } = chunkedBody(1, 16);
      fetchMock.mockResolvedValueOnce(
        new Response(stream, {
          status: 200,
          headers: { "Content-Type": "image/jpeg", "Content-Length": String(MAX_POSTER_BYTES + 1) },
        }),
      );

      const response = await call(POSTER);

      expect(response.status).toBe(502);
      expect(state.cancelled).toBe(true);
    });

    it("accepts a poster of exactly the limit", async () => {
      const { stream } = chunkedBody(32, MAX_POSTER_BYTES / 32);
      fetchMock.mockResolvedValueOnce(
        new Response(stream, { status: 200, headers: { "Content-Type": "image/png" } }),
      );

      const response = await call(POSTER);

      expect((await response.arrayBuffer()).byteLength).toBe(MAX_POSTER_BYTES);
    });

    it("stops a body without Content-Length that grows past the limit", async () => {
      // 3 MB in 64 KB pieces, with no Content-Length
      const { stream, state } = chunkedBody(48, 64 * 1024);
      fetchMock.mockResolvedValueOnce(
        new Response(stream, { status: 200, headers: { "Content-Type": "image/jpeg" } }),
      );

      const response = await call(POSTER);

      await expect(response.arrayBuffer()).rejects.toThrow();
      expect(state.cancelled).toBe(true);
      expect(state.sent).toBeLessThan(48);
    });
  });

  describe("limits the requests of one address", () => {
    it("does not limit one page of 20 posters", async () => {
      fetchMock.mockImplementation(async () => imageResponse());

      for (let i = 0; i < 20; i += 1) {
        expect((await call(POSTER, "203.0.113.7")).status).toBe(200);
      }
    });

    it("answers 429 with Retry-After over the limit, without calling the upstream host", async () => {
      fetchMock.mockImplementation(async () => imageResponse());
      for (let i = 0; i < POSTER_LIMIT_PER_WINDOW; i += 1) {
        await call(POSTER, "203.0.113.7");
      }
      fetchMock.mockClear();

      const response = await call(POSTER, "203.0.113.7");

      expect(response.status).toBe(429);
      expect(Number(response.headers.get("Retry-After"))).toBeGreaterThan(0);
      expect(Number(response.headers.get("Retry-After"))).toBeLessThanOrEqual(60);
      expect(fetchMock).not.toHaveBeenCalled();
    });

    it("counts the right-most X-Forwarded-For entry, not one the browser made up", async () => {
      fetchMock.mockImplementation(async () => imageResponse());
      for (let i = 0; i < POSTER_LIMIT_PER_WINDOW; i += 1) {
        await call(POSTER, `10.0.0.${i % 250}, 203.0.113.7`);
      }

      expect((await call(POSTER, "10.9.9.9, 203.0.113.7")).status).toBe(429);
      expect((await call(POSTER, "198.51.100.1")).status).toBe(200);
    });
  });
});
