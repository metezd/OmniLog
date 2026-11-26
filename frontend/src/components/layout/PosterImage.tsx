"use client";

import { useState } from "react";

import { resolvePosterUrl } from "@/lib/media";

interface PosterImageProps {
  posterUrl: string | null;
  title: string;
  className?: string;
}

/**
 * Renders a catalog poster image through the app's poster proxy and falls back to
 * the "No poster" placeholder if the image is missing or fails to load.
 */
export default function PosterImage({
  posterUrl,
  title,
  className = "h-full w-full object-cover",
}: PosterImageProps) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const resolvedSrc = resolvePosterUrl(posterUrl);

  if (!resolvedSrc || failedUrl === resolvedSrc) {
    return (
      <div className="flex h-full items-center justify-center text-xs text-slate-500">
        No poster
      </div>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={resolvedSrc}
      alt={`Poster of ${title}`}
      referrerPolicy="no-referrer"
      onError={() => setFailedUrl(resolvedSrc)}
      className={className}
    />
  );
}
