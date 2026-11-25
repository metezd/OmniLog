import type { Metadata } from "next";
import Link from "next/link";

import SearchResultCard from "@/components/search/SearchResultCard";
import EmptyState from "@/components/states/EmptyState";
import ErrorState from "@/components/states/ErrorState";
import { toErrorState } from "@/lib/server/error-state";
import { getLibrary } from "@/lib/server/library";
import { getRecommendations } from "@/lib/server/recommendations";
import type { LibraryEntry, MediaItem, MediaType } from "@/types/api";

export const metadata: Metadata = {
  title: "Recommendations | OmniLog",
};

interface RecommendationsPageProps {
  searchParams?: Promise<{ target?: string | string[] }>;
}

const TARGET_TABS: { value: MediaType; label: string }[] = [
  { value: "SERIES", label: "TV Series" },
  { value: "GAME", label: "Video Games" },
  { value: "MOVIE", label: "Movies" },
];

function firstValue(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? "";
}

function parseTarget(value: string): MediaType {
  return TARGET_TABS.find((tab) => tab.value === value)?.value ?? "SERIES";
}

function rethrowIfRedirect(error: unknown): void {
  const digest = (error as { digest?: unknown } | null)?.digest;
  if (typeof digest === "string" && digest.startsWith("NEXT_REDIRECT")) throw error;
}

export default async function RecommendationsPage({ searchParams }: RecommendationsPageProps) {
  const params = searchParams ? await searchParams : {};
  const target = parseTarget(firstValue(params.target));
  const targetLabel = TARGET_TABS.find((tab) => tab.value === target)?.label ?? "Titles";

  let items: MediaItem[] = [];
  let library: LibraryEntry[] = [];

  try {
    const [recs, entries] = await Promise.all([
      getRecommendations(target),
      getLibrary().catch((error) => {
        rethrowIfRedirect(error);
        return [] as LibraryEntry[];
      }),
    ]);
    items = recs;
    library = entries;
  } catch (error) {
    rethrowIfRedirect(error);
    const state = toErrorState(error);
    return (
      <Shell>
        <ErrorState kind={state.kind} message={state.message} />
      </Shell>
    );
  }

  const libraryIds = new Set(library.map((entry) => entry.media_item_id));

  return (
    <Shell>
      <nav
        aria-label="Recommendation target"
        className="liquid-glass inline-flex self-start rounded-xl border border-white/10 p-1"
      >
        {TARGET_TABS.map((tab) => (
          <Link
            key={tab.value}
            href={`/recommendations?target=${tab.value}`}
            aria-current={tab.value === target ? "page" : undefined}
            className={`rounded-lg px-4 py-1.5 text-xs font-medium transition-all ${
              tab.value === target
                ? "bg-white/15 text-white"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {tab.label}
          </Link>
        ))}
      </nav>

      {items.length === 0 ? (
        library.length === 0 ? (
          <EmptyState
            title="Your library is empty"
            message="Add and rate games, series, or movies in your library so we can recommend titles for you."
            action={{ href: "/search", label: "Browse catalog" }}
          />
        ) : (
          <EmptyState
            title="No recommendations available yet"
            message={`No unowned ${targetLabel.toLowerCase()} recommendations are available right now.`}
            action={{ href: "/search", label: "Browse catalog" }}
          />
        )
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {items.map((item) => (
            <SearchResultCard
              key={item.id}
              item={item}
              inLibrary={libraryIds.has(item.id)}
            />
          ))}
        </div>
      )}
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative z-10 mx-auto w-full max-w-7xl space-y-6 px-4 py-8 sm:px-8">
      <div className="border-b border-white/10 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-white">
          Recommendations
        </h1>
        <p className="text-xs text-slate-400">
          Personalized cross-media recommendations based on your library
        </p>
      </div>
      {children}
    </div>
  );
}
