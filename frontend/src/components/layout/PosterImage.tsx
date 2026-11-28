"use client";

import { useState } from "react";

import { POSTER_DIMENSIONS, type PosterSize, resolvePosterUrl } from "@/lib/media";

interface PosterImageProps {
  posterUrl: string | null;
  title: string;
  className?: string;
  /** Where the poster is shown: picks the TMDB size and whether it loads at once (#451). */
  size?: PosterSize;
}

/**
 * Renders a catalog poster image through the app's poster proxy and falls back to
 * the "No poster" placeholder if the image is missing or fails to load.
 *
 * A card poster loads lazily, so the posters below the fold of a search or library page wait
 * until they are scrolled to. The poster of the title page is the first thing on the page, so it
 * loads at once. Width and height give the browser the 2:3 shape before the file arrives (#451).
 */
export default function PosterImage({
  posterUrl,
  title,
  className = "h-full w-full object-cover",
  size = "card",
}: PosterImageProps) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const resolvedSrc = resolvePosterUrl(posterUrl, size);

  if (!resolvedSrc || failedUrl === resolvedSrc) {
    return (
      <div className="flex h-full items-center justify-center text-xs text-slate-500">
        No poster
      </div>
    );
  }

  const { width, height } = POSTER_DIMENSIONS[size];

  return (
    // A plain <img>, not next/image: the poster proxy /api/poster serves the files and the
    // Next.js image optimizer is turned off in next.config.ts (#451).
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={resolvedSrc}
      alt={`Poster of ${title}`}
      width={width}
      height={height}
      loading={size === "detail" ? "eager" : "lazy"}
      decoding="async"
      referrerPolicy="no-referrer"
      onError={() => setFailedUrl(resolvedSrc)}
      className={className}
    />
  );
}
