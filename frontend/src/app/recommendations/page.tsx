import type { Metadata } from "next";
import Link from "next/link";

import AddToLibraryButton from "@/components/search/AddToLibraryButton";
import EmptyState from "@/components/states/EmptyState";
import ErrorState from "@/components/states/ErrorState";
import { MEDIA_TYPE_LABELS } from "@/lib/media";
import { toErrorState } from "@/lib/server/error-state";
import { getLibrary } from "@/lib/server/library";
import { getRecommendations } from "@/lib/server/recommendations";
import type { MediaType, RecommendationItem } from "@/types/api";

export const metadata: Metadata = {
  title: "Recommendations | OmniLog",
};

interface RecommendationsPageProps {
  searchParams?: Promise<{ target?: string | string[] }>;
}

const FILTER_TABS: { value: MediaType | "ALL"; label: string }[] = [
  { value: "ALL", label: "All Cross-Media" },
  { value: "SERIES", label: "TV Series for Gamers" },
  { value: "GAME", label: "Games for Series Fans" },
];

export default async function RecommendationsPage({ searchParams }: RecommendationsPageProps) {
  const params = searchParams ? await searchParams : {};
  const rawTarget = Array.isArray(params.target) ? params.target[0] : params.target;
  const activeTab: MediaType | "ALL" =
    rawTarget === "SERIES" || rawTarget === "GAME" ? rawTarget : "ALL";

  let items: RecommendationItem[] = [];
  let libraryIds = new Set<number>();

  try {
    const [recs, library] = await Promise.all([
      getRecommendations(activeTab === "ALL" ? undefined : activeTab),
      getLibrary().catch(() => []),
    ]);
    items = recs;
    libraryIds = new Set(library.map((e) => e.media_item_id));
  } catch (error) {
    const digest = (error as { digest?: unknown } | null)?.digest;
    if (typeof digest === "string" && digest.startsWith("NEXT_REDIRECT")) throw error;
    const state = toErrorState(error);
    return (
      <Shell>
        <ErrorState kind={state.kind} message={state.message} />
      </Shell>
    );
  }

  return (
    <Shell>
      <nav
        aria-label="Recommendation target filter"
        className="liquid-glass inline-flex self-start rounded-xl border border-white/10 p-1"
      >
        {FILTER_TABS.map((tab) => {
          const href =
            tab.value === "ALL" ? "/recommendations" : `/recommendations?target=${tab.value}`;
          return (
            <Link
              key={tab.value}
              href={href}
              aria-current={tab.value === activeTab ? "page" : undefined}
              className={`rounded-lg px-4 py-1.5 text-xs font-medium transition-all ${
                tab.value === activeTab
                  ? "bg-white/15 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>

      {items.length === 0 ? (
        <EmptyState
          title="No recommendations available yet"
          message="Add and rate games or TV series in your library so the cross-media engine can compute recommendations."
        />
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => {
            const inLibrary = libraryIds.has(item.id);
            return (
              <article
                key={item.id}
                className="liquid-glass liquid-glass-card flex flex-col justify-between gap-4 rounded-2xl border border-white/10 p-5"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="rounded-full border border-horizon-cyan/40 bg-horizon-cyan/20 px-2.5 py-0.5 text-[10px] font-semibold text-cyan-300">
                      {MEDIA_TYPE_LABELS[item.media_type]}
                    </span>
                    {item.release_date && (
                      <span className="text-[11px] text-slate-400">
                        {item.release_date.slice(0, 4)}
                      </span>
                    )}
                  </div>

                  <h3 className="text-base font-bold tracking-tight text-white">
                    <Link
                      href={`/title/${item.id}`}
                      className="transition-colors hover:text-cyan-300"
                    >
                      {item.title}
                    </Link>
                  </h3>

                  {item.description && (
                    <p className="line-clamp-3 text-xs leading-relaxed text-slate-300">
                      {item.description}
                    </p>
                  )}

                  {item.genres && item.genres.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {item.genres.slice(0, 4).map((genre) => (
                        <span
                          key={genre}
                          className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-slate-300"
                        >
                          {genre}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="pt-2">
                  {inLibrary ? (
                    <div className="w-full rounded-lg border border-emerald-500/20 bg-emerald-500/10 py-1.5 text-center text-xs font-medium text-emerald-300">
                      ✓ In Library
                    </div>
                  ) : (
                    <AddToLibraryButton mediaItemId={item.id} />
                  )}
                </div>
              </article>
            );
          })}
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
          AI Cross-Media Recommendations
        </h1>
        <p className="text-xs text-slate-400">
          Personalized TV series recommendations based on your played video games, and vice versa
        </p>
      </div>
      {children}
    </div>
  );
}
