import Link from "next/link";

import { MEDIA_TYPE_LABELS, releaseYear, STATUS_LABELS } from "@/lib/media";
import type { LibraryEntry } from "@/types/api";

interface LibraryEntryCardProps {
  entry: LibraryEntry;
}

/** One title of the library: poster, title, status and rating. Links to the title detail page. */
export default function LibraryEntryCard({ entry }: LibraryEntryCardProps) {
  const { media_item: item } = entry;
  const year = releaseYear(item.release_date);

  return (
    <article className="liquid-glass liquid-glass-card flex flex-col overflow-hidden rounded-2xl">
      <div className="relative h-56 w-full overflow-hidden bg-black/40">
        {item.poster_url ? (
          // A plain img, because the poster hosts of IGDB and TMDB are not configured for next/image
          // eslint-disable-next-line @next/next/no-img-element
          <img src={item.poster_url} alt={`Poster of ${item.title}`} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-slate-500">No poster</div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-[#090C15] via-transparent to-transparent" />
        <span className="absolute left-3 top-3 rounded-full border border-horizon-cyan/40 bg-horizon-cyan/20 px-2 py-0.5 text-[10px] font-semibold text-cyan-300 backdrop-blur-md">
          {MEDIA_TYPE_LABELS[item.media_type]}
        </span>
        <span className="absolute right-3 top-3 rounded-full border border-white/20 bg-black/40 px-2 py-0.5 text-[10px] font-semibold text-slate-200 backdrop-blur-md">
          {STATUS_LABELS[entry.status]}
        </span>
      </div>

      <div className="space-y-1 p-5">
        <h3 className="font-bold tracking-tight text-white">
          <Link href={`/title/${item.id}`} className="transition-colors hover:text-cyan-300">
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
