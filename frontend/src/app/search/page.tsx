"use client";

import { useEffect, useState } from "react";

import {
  addToLibrary,
  getLibraryIds,
  removeFromLibrary,
  searchCatalog,
} from "@/lib/services/catalog";
import type { CatalogItem, MediaKind } from "@/types/media";

type KindFilter = MediaKind | "all";

const FILTERS: { value: KindFilter; label: string }[] = [
  { value: "all", label: "All Media" },
  { value: "tv", label: "TV Series" },
  { value: "game", label: "Video Games" },
];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<KindFilter>("all");
  const [results, setResults] = useState<CatalogItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [libraryIds, setLibraryIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    getLibraryIds().then((ids) => setLibraryIds(new Set(ids)));
  }, []);

  // Debounced search. The cancelled flag ignores stale responses.
  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    const timer = setTimeout(() => {
      searchCatalog({ query, kind }).then((data) => {
        if (cancelled) return;
        setResults(data);
        setIsLoading(false);
      });
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, kind]);

  const toggleLibrary = async (id: string) => {
    if (libraryIds.has(id)) {
      await removeFromLibrary(id);
    } else {
      await addToLibrary(id);
    }
    setLibraryIds(new Set(await getLibraryIds()));
  };

  return (
    <div className="relative z-10 mx-auto w-full max-w-7xl px-4 py-8 sm:px-8 space-y-8">
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4 border-b border-white/10 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Search Catalog
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Find series (TMDB) and games (IGDB) and add them to your library
          </p>
        </div>

        <div className="liquid-glass inline-flex rounded-xl border border-white/10 p-1 text-xs font-medium">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => setKind(f.value)}
              className={`px-4 py-2 rounded-lg transition-all ${
                kind === f.value
                  ? "bg-white/15 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="liquid-glass rounded-2xl border border-white/10 px-4 py-3 flex items-center gap-3">
        <span className="text-slate-400">🔍</span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by title or genre, e.g. Arcane, RPG, Thriller..."
          className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
        />
        {query && (
          <button
            type="button"
            onClick={() => setQuery("")}
            className="text-xs text-slate-400 hover:text-white"
          >
            Clear
          </button>
        )}
      </div>

      <p className="text-xs text-slate-400">
        {isLoading
          ? "Searching..."
          : query.trim()
          ? `${results.length} result${results.length === 1 ? "" : "s"} for "${query.trim()}"`
          : "Popular right now"}
      </p>

      {!isLoading && results.length === 0 && (
        <div className="liquid-glass rounded-2xl border border-white/10 p-10 text-center text-sm text-slate-400">
          Nothing found. Try a different title or genre.
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {results.map((item) => {
          const inLibrary = libraryIds.has(item.id);
          return (
            <article
              key={item.id}
              className="liquid-glass rounded-2xl border border-white/10 hover:border-white/20 transition-all overflow-hidden flex flex-col"
            >
              <div className="relative h-44 bg-linear-to-br from-slate-800 via-purple-950 to-black">
                {item.imageUrl ? (
                  <img
                    src={item.imageUrl}
                    alt={item.title}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="h-full w-full flex items-center justify-center text-5xl font-bold text-white/20">
                    {item.title.charAt(0)}
                  </div>
                )}
                <span className="absolute top-3 left-3 rounded-full bg-black/60 border border-white/15 px-2.5 py-0.5 text-[10px] font-medium text-slate-200">
                  {item.kind === "tv" ? "TV Series" : "Game"}
                </span>
                <span className="absolute top-3 right-3 rounded-full bg-black/60 border border-white/15 px-2.5 py-0.5 text-[10px] font-medium text-cyan-300">
                  {item.source}
                </span>
              </div>

              <div className="p-4 flex flex-col gap-3 flex-1">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="text-sm font-bold text-white">{item.title}</h2>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {item.year} • {item.length}
                    </p>
                  </div>
                  <span className="shrink-0 text-xs font-bold text-amber-300">
                    ★ {item.rating.toFixed(1)}
                  </span>
                </div>

                <p className="text-xs text-slate-300 line-clamp-3">
                  {item.summary}
                </p>

                <div className="flex flex-wrap gap-1.5">
                  {item.genres.map((g) => (
                    <span
                      key={g}
                      className="text-[10px] text-slate-300 bg-white/5 border border-white/10 rounded-md px-2 py-0.5"
                    >
                      {g}
                    </span>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={() => toggleLibrary(item.id)}
                  className={`mt-auto rounded-xl border px-3 py-2 text-xs font-medium transition-all active:scale-95 ${
                    inLibrary
                      ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/25"
                      : "bg-white/10 border-white/15 text-slate-200 hover:bg-white/15 hover:text-white"
                  }`}
                >
                  {inLibrary ? "✓ In Library" : "+ Add to Library"}
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}