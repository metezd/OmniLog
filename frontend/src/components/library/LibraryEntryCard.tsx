import Link from "next/link";

import PosterImage from "@/components/layout/PosterImage";
import {
  MEDIA_TYPE_BADGE_CLASSES,
  MEDIA_TYPE_CARD_CLASSES,
  MEDIA_TYPE_LABELS,
  MEDIA_TYPE_TITLE_CLASSES,
  releaseYear,
  STATUS_LABELS,
} from "@/lib/media";
import type { LibraryEntry } from "@/types/api";

interface LibraryEntryCardProps {
  entry: LibraryEntry;
}

/** One title of the library: poster, title, status and rating. Links to the title detail page. */
export default function LibraryEntryCard({ entry }: LibraryEntryCardProps) {
  const { media_item: item } = entry;
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
        <span className="absolute right-3 top-3 rounded-full border border-white/20 bg-black/40 px-2 py-0.5 text-[10px] font-semibold text-slate-200 backdrop-blur-md">
          {STATUS_LABELS[entry.status]}
        </span>
      </div>

      <div className="space-y-1 p-5">
        <h3 className="font-bold tracking-tight text-white">
          <Link href={`/title/${item.id}`} className={MEDIA_TYPE_TITLE_CLASSES[item.media_type]}>
            {item.title}
          </Link>
        </h3>
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>{year ?? "Release date unknown"}</span>
          <span className="font-semibold text-amber-400">
            {entry.rating === null ? "Not rated" : `★ ${entry.rating}/10`}
          </span>
        </div>
      </div>
    </article>
  );
}
