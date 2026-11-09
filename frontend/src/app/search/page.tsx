import type { Metadata } from "next";
import Link from "next/link";

import SearchResultCard from "@/components/search/SearchResultCard";
import EmptyState from "@/components/states/EmptyState";
import ErrorState from "@/components/states/ErrorState";
import { searchCatalog } from "@/lib/server/catalog";
import { toErrorState } from "@/lib/server/error-state";
import { getLibrary } from "@/lib/server/library";
import type { MediaItem, MediaType } from "@/types/api";

export const metadata: Metadata = {
  title: "Search | OmniLog",
};

const TABS: { value: MediaType; label: string }[] = [
  { value: "SERIES", label: "TV Series" },
  { value: "GAME", label: "Video Games" },
  { value: "MOVIE", label: "Movies" },
];

interface SearchPageProps {
  searchParams: Promise<{ q?: string | string[]; type?: string | string[] }>;
}

function firstValue(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? "";
}

function parseType(value: string): MediaType {
  return TABS.find((tab) => tab.value === value)?.value ?? "SERIES";
}

function tabHref(type: MediaType, query: string): string {
  const params = new URLSearchParams({ type });
  if (query) params.set("q", query);
  return `/search?${params}`;
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const params = await searchParams;
  const query = firstValue(params.q).trim();
  const type = parseType(firstValue(params.type));
  const typeLabel = TABS.find((tab) => tab.value === type)?.label ?? "";

  let results: MediaItem[] = [];
  let libraryIds = new Set<number>();
  let failure: ReturnType<typeof toErrorState> | null = null;

  if (query) {
    try {
      const [found, library] = await Promise.all([
        searchCatalog(query, type),
        getLibrary().catch(() => []),
      ]);
      results = found;
      libraryIds = new Set(library.map((entry) => entry.media_item_id));
    } catch (error) {
      // A redirect (for example to the session-expired route) must not be swallowed
      const digest = (error as { digest?: unknown } | null)?.digest;
      if (typeof digest === "string" && digest.startsWith("NEXT_REDIRECT")) throw error;
      failure = toErrorState(error);
    }
  }

  return (
    <div className="relative z-10 mx-auto w-full max-w-7xl space-y-6 px-4 py-8 sm:px-8">
      <div className="border-b border-white/10 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-white">Search</h1>
        <p className="text-xs text-slate-400">
          Find series, games and movies and add them to your library
        </p>
      </div>

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <nav
          aria-label="Media type"
          className="liquid-glass inline-flex self-start rounded-xl border border-white/10 p-1"
        >
          {TABS.map((tab) => (
            <Link
              key={tab.value}
              href={tabHref(tab.value, query)}
              aria-current={tab.value === type ? "page" : undefined}
              className={`rounded-lg px-4 py-1.5 text-xs font-medium transition-all ${
                tab.value === type
                  ? "bg-white/15 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {tab.label}
            </Link>
          ))}
        </nav>

        <form
          action="/search"
          className="liquid-glass flex flex-1 items-center gap-3 rounded-2xl border border-white/10 px-4 py-2.5 lg:max-w-xl"
        >
          <input type="hidden" name="type" value={type} />
          <input
            type="search"
            name="q"
            defaultValue={query}
            placeholder={`Search ${typeLabel.toLowerCase()} by title...`}
            className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <button
            type="submit"
            className="rounded-lg border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-medium text-slate-200 transition-all hover:bg-white/15 hover:text-white active:scale-95"
          >
            Search
          </button>
        </form>
      </div>

      {failure ? (
        <ErrorState kind={failure.kind} message={failure.message} />
      ) : !query ? (
        <EmptyState
          title="Search the catalog"
          message="Type a title above to find series, games or movies."
        />
      ) : results.length === 0 ? (
        <EmptyState
          title="No results"
          message={`Nothing found for "${query}" in ${typeLabel}.`}
        />
      ) : (
        <>
          <p className="text-xs text-slate-400">
            {results.length} result{results.length === 1 ? "" : "s"} for &ldquo;{query}&rdquo;
          </p>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {results.map((item) => (
              <SearchResultCard
                key={item.id}
                item={item}
                inLibrary={libraryIds.has(item.id)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}