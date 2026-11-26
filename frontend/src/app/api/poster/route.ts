import { type NextRequest } from "next/server";

import { ALLOWED_POSTER_HOSTS } from "@/lib/media";

const SAFE_PATH_PATTERN = /^\/[A-Za-z0-9/_.-]{1,250}$/;

/**
 * Server-side poster proxy for external catalog CDNs (TMDB, IGDB, TVMaze, Steam, iTunes for movies saved before #370).
 * Prevents broken posters when a user's ISP, DNS, or browser extension blocks direct requests
 * to image.tmdb.org while the hosted frontend (e.g. Render Frankfurt) can reach it directly.
 */
export async function GET(request: NextRequest) {
  const rawUrl = request.nextUrl.searchParams.get("url");
  if (!rawUrl || rawUrl.length > 500) {
    return new Response("Invalid poster URL", { status: 400 });
  }

  let parsed: URL;
  try {
    parsed = new URL(rawUrl);
  } catch {
    return new Response("Invalid poster URL", { status: 400 });
  }

  if (
    parsed.protocol !== "https:" ||
    !ALLOWED_POSTER_HOSTS.has(parsed.hostname) ||
    !SAFE_PATH_PATTERN.test(parsed.pathname)
  ) {
    return new Response("Disallowed poster host", { status: 403 });
  }

  const upstreamUrl = `https://${parsed.hostname}${parsed.pathname}`;

  try {
    const upstream = await fetch(upstreamUrl, {
      headers: { Accept: "image/*" },
      // The host was checked above, a redirect would skip that check (SSRF), so none is followed
      redirect: "error",
      signal: AbortSignal.timeout(8000),
    });

    if (!upstream.ok) {
      return new Response("Poster not found", { status: upstream.status === 404 ? 404 : 502 });
    }

    const contentType = upstream.headers.get("content-type") ?? "image/jpeg";
    if (!contentType.toLowerCase().startsWith("image/")) {
      return new Response("Upstream response is not an image", { status: 502 });
    }

    const buffer = await upstream.arrayBuffer();
    return new Response(buffer, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "public, max-age=86400, s-maxage=86400, stale-while-revalidate=604800",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch {
    return new Response("Failed to fetch poster", { status: 502 });
  }
}
