import AddToLibraryButton from "@/components/search/AddToLibraryButton";
import { MEDIA_TYPE_LABELS, releaseYear } from "@/lib/media";
import type { MediaItem } from "@/types/api";

interface SearchResultCardProps {
  item: MediaItem;
  inLibrary: boolean;
}

/** One catalog result: poster, title, year and the add-to-library action. */
export default function SearchResultCard({ item, inLibrary }: SearchResultCardProps) {
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
      </div>

      <div className="flex flex-1 flex-col gap-3 p-5">
        <div className="space-y-1">
          <h3 className="font-bold tracking-tight text-white">{item.title}</h3>
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