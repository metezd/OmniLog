import Link from "next/link";

import PosterImage from "@/components/layout/PosterImage";
import AddToLibraryButton from "@/components/search/AddToLibraryButton";
import {
  MEDIA_TYPE_BADGE_CLASSES,
  MEDIA_TYPE_CARD_CLASSES,
  MEDIA_TYPE_LABELS,
  MEDIA_TYPE_TITLE_CLASSES,
  releaseYear,
} from "@/lib/media";
import type { MediaItem } from "@/types/api";

interface SearchResultCardProps {
  item: MediaItem;
  inLibrary: boolean;
}

/** One catalog result: poster, title, year and the add-to-library action. */
export default function SearchResultCard({ item, inLibrary }: SearchResultCardProps) {
  const year = releaseYear(item.release_date);

  return (
    <article
      className={`liquid-glass liquid-glass-card ${MEDIA_TYPE_CARD_CLASSES[item.media_type]} flex flex-col overflow-hidden rounded-2xl`}
    >
      <div className="relative h-56 w-full overflow-hidden bg-black/40">
        <PosterImage posterUrl={item.poster_url} title={item.title} />
        <div className="absolute inset-0 bg-gradient-to-t from-[#090C15] via-transparent to-transparent" />
        <span
          className={`absolute left-3 top-3 rounded-full border px-2 py-0.5 text-[10px] font-semibold backdrop-blur-md ${MEDIA_TYPE_BADGE_CLASSES[item.media_type]}`}
        >
          {MEDIA_TYPE_LABELS[item.media_type]}
        </span>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-5">
        <div className="space-y-1">
          <h3 className="font-bold tracking-tight text-white">
            <Link href={`/title/${item.id}`} className={MEDIA_TYPE_TITLE_CLASSES[item.media_type]}>
              {item.title}
            </Link>
          </h3>
          <p className="text-xs text-slate-400">{year ?? "Release date unknown"}</p>
        </div>

        {item.genres.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {item.genres.slice(0, 3).map((genre) => (
              <span
                key={genre}
                className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-slate-300"
              >
                {genre}
              </span>
            ))}
          </div>
        )}

        <div className="mt-auto">
          {inLibrary ? (
            <div className="w-full rounded-lg border border-emerald-500/20 bg-emerald-500/10 py-1.5 text-center text-xs font-medium text-emerald-300">
              ✓ In Library
            </div>
          ) : (
            <AddToLibraryButton mediaItemId={item.id} />
          )}
        </div>
      </div>
    </article>
  );
}