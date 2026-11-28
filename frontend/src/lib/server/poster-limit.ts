import "server-only";

// A limit per browser address for GET /api/poster (#450). The route needs no login, so without a
// limit a script could use this server as a bandwidth proxy for the allowed catalog CDNs.
//
// The count lives in the memory of this process: a fixed window of one minute per address. On a
// small server with one process that is enough, and it needs no Redis.

/** Length of one window. */
export const POSTER_WINDOW_MS = 60_000;

/**
 * Posters per address and window. A page of 20 posters is far below it, and so are the diary
 * (100 entries a page) and a large library, which load their posters while the user scrolls. The
 * browser keeps a poster for a day (Cache-Control), so a reload does not count again.
 */
export const POSTER_LIMIT_PER_WINDOW = 300;

/** Most addresses that are kept. Old windows are dropped first, so the map cannot grow forever. */
const MAX_TRACKED_ADDRESSES = 10_000;

/** Addresses (IPv4, IPv6) separated by commas, as in an X-Forwarded-For header (see backend.ts). */
const FORWARDED_FOR = /^[0-9A-Fa-f.:[\], ]{1,512}$/;

type Window = { start: number; count: number };

const windows = new Map<string, Window>();

/**
 * The browser address of a request: the right-most entry of X-Forwarded-For, the one that the
 * proxy in front of this server wrote (the same rule as backendFetch, #301). The left part was
 * written by the browser and can be anything. Requests without a usable header share one key, so
 * a missing header is not a way around the limit.
 */
export function clientAddress(forwardedFor: string | null): string {
  const value = forwardedFor?.trim();
  if (!value || !FORWARDED_FOR.test(value)) return "unknown";
  return value.split(",").map((part) => part.trim()).filter(Boolean).at(-1) ?? "unknown";
}

function prune(now: number): void {
  for (const [address, window] of windows) {
    if (now - window.start >= POSTER_WINDOW_MS) windows.delete(address);
  }
  if (windows.size >= MAX_TRACKED_ADDRESSES) windows.clear();
}

/**
 * Counts one poster request of an address. Returns null when it is allowed, or the number of
 * seconds until the window ends (for Retry-After) when the address is over the limit.
 */
export function takePosterSlot(address: string, now: number = Date.now()): number | null {
  let window = windows.get(address);
  if (!window || now - window.start >= POSTER_WINDOW_MS) {
    if (!window && windows.size >= MAX_TRACKED_ADDRESSES) prune(now);
    window = { start: now, count: 0 };
    windows.set(address, window);
  }
  if (window.count >= POSTER_LIMIT_PER_WINDOW) {
    return Math.max(1, Math.ceil((window.start + POSTER_WINDOW_MS - now) / 1000));
  }
  window.count += 1;
  return null;
}

/** Forgets every count. For the tests only. */
export function resetPosterLimit(): void {
  windows.clear();
}
