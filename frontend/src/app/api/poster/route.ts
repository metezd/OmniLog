import { type NextRequest } from "next/server";

import { ALLOWED_POSTER_HOSTS } from "@/lib/media";
import { clientAddress, takePosterSlot } from "@/lib/server/poster-limit";

const SAFE_PATH_PATTERN = /^\/[A-Za-z0-9/_.-]{1,250}$/;

/**
 * Largest poster that is passed on. Catalog posters are far smaller (TMDB w500 is about 100 KB).
 * Not exported: a route file may only export the route fields of Next.js.
 */
const MAX_POSTER_BYTES = 2 * 1024 * 1024;

/** Only raster images are posters. SVG (it can hold scripts) and every other type answer 502. */
const ALLOWED_POSTER_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

/** Drops an upstream body that is not sent on. Not awaited: some bodies only settle when read. */
function discard(upstream: Response): void {
  upstream.body?.cancel().catch(() => undefined);
}

/**
 * Passes the body on chunk by chunk and stops it when it grows past `MAX_POSTER_BYTES`, so a
 * poster is never held in memory as a whole (#450). The error aborts the answer, and pipeThrough
 * cancels the upstream body.
 */
function limitBody(body: ReadableStream<Uint8Array>): ReadableStream<Uint8Array> {
  let received = 0;
  return body.pipeThrough(
    new TransformStream<Uint8Array, Uint8Array>({
      transform(chunk, controller) {
        received += chunk.byteLength;
        if (received > MAX_POSTER_BYTES) {
          controller.error(new Error("Poster is too large"));
          return;
        }
        controller.enqueue(chunk);
      },
    }),
  );
}

/**
 * Server-side poster proxy for external catalog CDNs (TMDB, IGDB, TVMaze, Steam, iTunes for movies saved before #370).
 * Prevents broken posters when a user's ISP, DNS, or browser extension blocks direct requests
 * to image.tmdb.org while the hosted frontend (e.g. Render Frankfurt) can reach it directly.
 */
export async function GET(request: NextRequest) {
  const retryAfter = takePosterSlot(clientAddress(request.headers.get("x-forwarded-for")));
  if (retryAfter !== null) {
    return new Response("Too many poster requests", {
      status: 429,
      headers: { "Retry-After": String(retryAfter) },
    });
  }

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
      discard(upstream);
      return new Response("Poster not found", { status: upstream.status === 404 ? 404 : 502 });
    }

    // "image/jpeg; charset=binary" is still a JPEG, so only the media type before ";" counts
    const contentType = (upstream.headers.get("content-type") ?? "image/jpeg")
      .split(";")[0]
      .trim()
      .toLowerCase();
    if (!ALLOWED_POSTER_TYPES.has(contentType)) {
      discard(upstream);
      return new Response("Upstream response is not a poster image", { status: 502 });
    }

    const declaredLength = Number(upstream.headers.get("content-length"));
    if (Number.isFinite(declaredLength) && declaredLength > MAX_POSTER_BYTES) {
      discard(upstream);
      return new Response("Poster is too large", { status: 502 });
    }

    if (!upstream.body) {
      return new Response("Failed to fetch poster", { status: 502 });
    }

    return new Response(limitBody(upstream.body), {
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
