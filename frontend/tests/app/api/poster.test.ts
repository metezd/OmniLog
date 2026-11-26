// @vitest-environment node
import { HttpResponse, http } from "msw";
import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { GET } from "@/app/api/poster/route";
import { isProtectedPath } from "@/lib/auth/routes";
import { server } from "../../mocks/server";

function posterRequest(url?: string): NextRequest {
  const query = url === undefined ? "" : `?url=${encodeURIComponent(url)}`;
  return new NextRequest(`http://localhost:3000/api/poster${query}`);
}

describe("GET /api/poster", () => {
  it("is not behind the login guard", () => {
    expect(isProtectedPath("/api/poster")).toBe(false);
  });

  it("returns 400 when url parameter is missing or invalid", async () => {
    expect((await GET(posterRequest())).status).toBe(400);
    expect((await GET(posterRequest("not-a-valid-url"))).status).toBe(400);
  });

  it("returns 403 for non-HTTPS or disallowed hosts", async () => {
    expect((await GET(posterRequest("http://image.tmdb.org/t/p/w500/a.jpg"))).status).toBe(403);
    expect((await GET(posterRequest("https://evil.example.com/a.jpg"))).status).toBe(403);
  });

  it("proxies an allowed catalog image with caching and nosniff headers", async () => {
    const target = "https://image.tmdb.org/t/p/w500/poster.jpg";
    server.use(
      http.get(target, () =>
        HttpResponse.arrayBuffer(new Uint8Array([0xff, 0xd8, 0xff]).buffer, {
          headers: { "Content-Type": "image/jpeg" },
        }),
      ),
    );

    const response = await GET(posterRequest(target));

    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe("image/jpeg");
    expect(response.headers.get("X-Content-Type-Options")).toBe("nosniff");
    expect(response.headers.get("Cache-Control")).toContain("max-age=86400");
  });

  it("returns 404 when upstream image is missing and 502 when upstream is not an image", async () => {
    const missing = "https://image.tmdb.org/t/p/w500/missing.jpg";
    const htmlUrl = "https://image.tmdb.org/t/p/w500/not-image.jpg";
    server.use(
      http.get(missing, () => new HttpResponse(null, { status: 404 })),
      http.get(htmlUrl, () =>
        HttpResponse.text("<html>error</html>", { headers: { "Content-Type": "text/html" } }),
      ),
    );

    expect((await GET(posterRequest(missing))).status).toBe(404);
    expect((await GET(posterRequest(htmlUrl))).status).toBe(502);
  });
});
