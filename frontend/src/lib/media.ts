import type { MediaType, WatchStatus } from "@/types/api";

export const STATUS_LABELS: Record<WatchStatus, string> = {
  PLAN_TO_WATCH: "Plan to watch",
  IN_PROGRESS: "In progress",
  COMPLETED: "Completed",
  DROPPED: "Dropped",
};

export const MEDIA_TYPE_LABELS: Record<MediaType, string> = {
  GAME: "Game",
  SERIES: "TV Series",
  MOVIE: "Movie",
};

/** Pill badge color & glow per media type: Game = Ice Blue, Series = Light Green, Movie = Purple. */
export const MEDIA_TYPE_BADGE_CLASSES: Record<MediaType, string> = {
  GAME: "border-sky-300/45 bg-sky-400/20 text-sky-200 shadow-[0_0_12px_rgba(56,189,248,0.35)]",
  SERIES:
    "border-emerald-400/45 bg-emerald-500/20 text-emerald-300 shadow-[0_0_12px_rgba(52,211,153,0.35)]",
  MOVIE:
    "border-purple-400/45 bg-purple-500/20 text-purple-300 shadow-[0_0_12px_rgba(168,85,247,0.35)]",
};

/** Card hover border & glow modifier class matching the media type badge. */
export const MEDIA_TYPE_CARD_CLASSES: Record<MediaType, string> = {
  GAME: "liquid-glass-card-game group",
  SERIES: "liquid-glass-card-series group",
  MOVIE: "liquid-glass-card-movie group",
};

/** Title glow & hover color matching the media type badge. */
export const MEDIA_TYPE_TITLE_CLASSES: Record<MediaType, string> = {
  GAME: "transition-all hover:text-sky-200 hover:drop-shadow-[0_0_10px_rgba(56,189,248,0.65)] group-hover:text-sky-200 group-hover:drop-shadow-[0_0_10px_rgba(56,189,248,0.55)]",
  SERIES:
    "transition-all hover:text-emerald-300 hover:drop-shadow-[0_0_10px_rgba(52,211,153,0.65)] group-hover:text-emerald-300 group-hover:drop-shadow-[0_0_10px_rgba(52,211,153,0.55)]",
  MOVIE:
    "transition-all hover:text-purple-300 hover:drop-shadow-[0_0_10px_rgba(168,85,247,0.65)] group-hover:text-purple-300 group-hover:drop-shadow-[0_0_10px_rgba(168,85,247,0.55)]",
};

/** The year at the start of a release date such as "2015-01-30", or null. */
export function releaseYear(releaseDate: string | null): string | null {
  const match = releaseDate?.match(/^\d{4}/);
  return match ? match[0] : null;
}

/** Allowed external catalog CDN hostnames that can be proxied through /api/poster. */
export const ALLOWED_POSTER_HOSTS = new Set([
  "image.tmdb.org",
  "images.igdb.com",
  "static.tvmaze.com",
  "shared.akamai.steamstatic.com",
  "cdn.akamai.steamstatic.com",
  "is1-ssl.mzstatic.com",
  "is2-ssl.mzstatic.com",
  "is3-ssl.mzstatic.com",
  "is4-ssl.mzstatic.com",
  "is5-ssl.mzstatic.com",
]);

/**
 * Where a poster is shown. A card is at most about 340 CSS pixels wide (one column on a phone,
 * four on a large screen), the title page is wider on a phone and is the first thing on the page.
 */
export type PosterSize = "card" | "detail";

/** The TMDB size of every poster size (#451). The backend saves `w500` for every movie and series. */
export const TMDB_POSTER_SIZES: Record<PosterSize, string> = { card: "w342", detail: "w500" };

/** Width and height of the poster file of every size, so the browser knows the 2:3 shape before it loads. */
export const POSTER_DIMENSIONS: Record<PosterSize, { width: number; height: number }> = {
  card: { width: 342, height: 513 },
  detail: { width: 500, height: 750 },
};

const TMDB_SIZE_PATTERN = /^\/t\/p\/(?:w\d+|original)\//;

/**
 * Asks TMDB for the size that fits where the poster is shown, for example `w342` instead of the
 * saved `w500` in a card (#451). Other hosts are kept: IGDB `t_cover_big` is 264 pixels wide already.
 */
export function sizedPosterUrl(posterUrl: string, size: PosterSize): string {
  try {
    const parsed = new URL(posterUrl);
    if (parsed.hostname === "image.tmdb.org" && TMDB_SIZE_PATTERN.test(parsed.pathname)) {
      parsed.pathname = parsed.pathname.replace(TMDB_SIZE_PATTERN, `/t/p/${TMDB_POSTER_SIZES[size]}/`);
      return parsed.toString();
    }
  } catch {
    return posterUrl;
  }
  return posterUrl;
}

/**
 * Route known external catalog poster URLs through the Next.js /api/poster proxy so browsers
 * behind ISP/DNS blocks or strict tracking filters load images from the app origin.
 */
export function resolvePosterUrl(posterUrl: string | null, size?: PosterSize): string | null {
  if (!posterUrl) return null;
  try {
    const parsed = new URL(size ? sizedPosterUrl(posterUrl, size) : posterUrl);
    if (parsed.protocol === "https:" && ALLOWED_POSTER_HOSTS.has(parsed.hostname)) {
      const cleanTarget = `${parsed.origin}${parsed.pathname}`;
      return `/api/poster?url=${encodeURIComponent(cleanTarget)}`;
    }
  } catch {
    return posterUrl;
  }
  return posterUrl;
}

/** Minutes as hours and minutes, for example 125 -> "2h 5m" and 0 -> "0h 0m" (#413). */
export function formatPlaytime(totalMinutes: number): string {
  const minutes = Number.isFinite(totalMinutes) && totalMinutes > 0 ? Math.floor(totalMinutes) : 0;
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
}
