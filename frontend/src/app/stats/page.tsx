import type { Metadata } from "next";

import EmptyState from "@/components/states/EmptyState";
import ErrorState from "@/components/states/ErrorState";
import { MEDIA_TYPE_LABELS } from "@/lib/media";
import { toErrorState } from "@/lib/server/error-state";
import { getStats } from "@/lib/server/stats";
import type { MediaType, StatsResponse } from "@/types/api";

export const metadata: Metadata = {
  title: "Analytics Dashboard | OmniLog",
};

export default async function StatsPage() {
  let stats: StatsResponse;
  try {
    stats = await getStats();
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

  const totalHours = (stats.playtime.total_minutes / 60).toFixed(1);
  const maxRatingCount = Math.max(1, ...Object.values(stats.rating_distribution));
  const maxBucketCount = Math.max(1, ...stats.playtime.histogram.map((b) => b.count));
  const maxGenreCount = Math.max(1, ...stats.genre_breakdown.map((g) => g.count));

  return (
    <Shell>
      {stats.total_items === 0 ? (
        <EmptyState
          title="No analytics data yet"
          message="Add games or series to your library and log chapter playtime to unlock your visual dashboard."
        />
      ) : (
        <div className="space-y-8">
          {/* KPI Summary Row */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="liquid-glass rounded-2xl border border-white/10 p-5">
              <p className="text-xs text-slate-400">Total Tracked Titles</p>
              <p className="mt-2 text-2xl font-bold text-white">{stats.total_items}</p>
            </div>
            <div className="liquid-glass rounded-2xl border border-white/10 p-5">
              <p className="text-xs text-slate-400">Total Logged Time</p>
              <p className="mt-2 text-2xl font-bold text-cyan-300">
                {totalHours} hrs{" "}
                <span className="text-xs font-normal text-slate-400">
                  ({stats.playtime.total_minutes} min)
                </span>
              </p>
            </div>
            <div className="liquid-glass rounded-2xl border border-white/10 p-5">
              <p className="text-xs text-slate-400">Video Games</p>
              <p className="mt-2 text-2xl font-bold text-purple-300">
                {stats.media_split.GAME ?? 0}
              </p>
            </div>
            <div className="liquid-glass rounded-2xl border border-white/10 p-5">
              <p className="text-xs text-slate-400">TV Series &amp; Movies</p>
              <p className="mt-2 text-2xl font-bold text-amber-300">
                {(stats.media_split.SERIES ?? 0) + (stats.media_split.MOVIE ?? 0)}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Media Split Ratio */}
            <section className="liquid-glass space-y-4 rounded-2xl border border-white/10 p-6">
              <div>
                <h2 className="text-base font-bold text-white">Media Split Ratio</h2>
                <p className="text-xs text-slate-400">
                  Distribution across video games, TV series, and movies
                </p>
              </div>
              <div className="space-y-3">
                {(["GAME", "SERIES", "MOVIE"] as MediaType[]).map((type) => {
                  const count = stats.media_split[type] ?? 0;
                  const pct =
                    stats.total_items > 0 ? Math.round((count / stats.total_items) * 100) : 0;
                  return (
                    <div key={type} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="font-medium text-slate-200">
                          {MEDIA_TYPE_LABELS[type]}
                        </span>
                        <span className="text-slate-400">
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/5">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-purple-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Genre Breakdown */}
            <section className="liquid-glass space-y-4 rounded-2xl border border-white/10 p-6">
              <div>
                <h2 className="text-base font-bold text-white">Genre Breakdown</h2>
                <p className="text-xs text-slate-400">Most frequent genres in your library</p>
              </div>
              {stats.genre_breakdown.length === 0 ? (
                <p className="text-xs text-slate-400">No genres tagged yet.</p>
              ) : (
                <div className="space-y-2.5">
                  {stats.genre_breakdown.slice(0, 8).map((item) => {
                    const pct = Math.round((item.count / maxGenreCount) * 100);
                    return (
                      <div key={item.genre} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-medium text-slate-200">{item.genre}</span>
                          <span className="text-slate-400">{item.count} titles</span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
                          <div
                            className="h-full rounded-full bg-cyan-400/80"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </section>

            {/* Rating Distribution (1-10) */}
            <section className="liquid-glass space-y-4 rounded-2xl border border-white/10 p-6">
              <div>
                <h2 className="text-base font-bold text-white">Rating Distribution (1–10 ★)</h2>
                <p className="text-xs text-slate-400">Spread of your overall library ratings</p>
              </div>
              <div className="grid grid-cols-10 items-end gap-2 pt-4">
                {Array.from({ length: 10 }, (_, idx) => {
                  const star = String(idx + 1);
                  const count = stats.rating_distribution[star] ?? 0;
                  const heightPct = Math.max(8, Math.round((count / maxRatingCount) * 100));
                  return (
                    <div key={star} className="flex flex-col items-center gap-1.5">
                      <span className="text-[10px] text-slate-400">{count}</span>
                      <div className="flex h-28 w-full items-end rounded-lg bg-white/5 p-1">
                        <div
                          className="w-full rounded-md bg-amber-400/80"
                          style={{ height: `${heightPct}%` }}
                        />
                      </div>
                      <span className="text-[11px] font-semibold text-slate-300">{star}★</span>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Playtime Histogram */}
            <section className="liquid-glass space-y-4 rounded-2xl border border-white/10 p-6">
              <div>
                <h2 className="text-base font-bold text-white">Playtime &amp; Watch Histogram</h2>
                <p className="text-xs text-slate-400">
                  Logged chapter/episode minutes per title
                </p>
              </div>
              {stats.playtime.histogram.length === 0 ? (
                <p className="text-xs text-slate-400">
                  No chapter playtime logged yet. Open any library title to log minutes.
                </p>
              ) : (
                <div className="space-y-3">
                  {stats.playtime.histogram.map((bucket) => {
                    const pct = Math.round((bucket.count / maxBucketCount) * 100);
                    return (
                      <div key={bucket.bucket} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-medium text-slate-200">{bucket.bucket}</span>
                          <span className="text-purple-300">{bucket.count} chapters</span>
                        </div>
                        <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/5">
                          <div
                            className="h-full rounded-full bg-purple-400/80"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </section>
          </div>
        </div>
      )}
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative z-10 mx-auto w-full max-w-7xl space-y-6 px-4 py-8 sm:px-8">
      <div className="border-b border-white/10 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-white">Analytics Dashboard</h1>
        <p className="text-xs text-slate-400">
          Playtime histograms, genre breakdowns, rating distributions, and media split ratios
        </p>
      </div>
      {children}
    </div>
  );
}
