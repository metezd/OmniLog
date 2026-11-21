"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { CurrentUser, LibraryEntry } from "@/types/api";

type MediaFilter = "ALL" | "GAME" | "SERIES" | "MOVIE";

export interface AtmosphericHeroProps {
  user?: CurrentUser | null;
  entries?: LibraryEntry[];
  children?: React.ReactNode;
}

const MAIN_FEATURES = [
  {
    title: "Unified Cross-Media Library",
    description:
      "Track video games, TV series, and movies in one place with status filters and 1–10 ratings.",
  },
  {
    title: "Episodic & Decision Logging",
    description:
      "Rate individual episodes and game chapters (1–5 stars), log playtime, and record branching choices.",
  },
  {
    title: "AI Recommendations & Spoiler Shield",
    description:
      "Discover cross-media recommendations with automated NLP spoiler detection on community reviews.",
  },
  {
    title: "Activity Diary, Lists & Analytics",
    description:
      "Curate custom themed lists, follow your chronological diary, and explore personal stats charts.",
  },
] as const;

export default function AtmosphericHero({
  user = null,
  entries = [],
  children,
}: AtmosphericHeroProps) {
  const router = useRouter();
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const [pureCanvas, setPureCanvas] = useState(false);
  const [query, setQuery] = useState("");
  const [mediaFilter, setMediaFilter] = useState<MediaFilter>("ALL");

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement | null)?.tagName;
      const inInput = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";

      if (e.key === "/" && !inInput && searchInputRef.current) {
        e.preventDefault();
        setPureCanvas(false);
        setTimeout(() => searchInputRef.current?.focus(), 20);
      } else if ((e.key === "h" || e.key === "H") && !inInput) {
        setPureCanvas((prev) => !prev);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    const params = new URLSearchParams();
    if (trimmed) params.set("q", trimmed);
    if (mediaFilter !== "ALL") {
      params.set("type", mediaFilter);
    }
    const qs = params.toString();
    router.push(qs ? `/search?${qs}` : "/search");
  };

  return (
    <section className="relative flex min-h-[calc(100vh-8rem)] w-full select-none flex-col items-center justify-center bg-transparent px-4 py-8">
      <div
        className={`pointer-events-none relative z-40 flex w-full flex-col items-center justify-center text-center transition-opacity duration-300 ${
          pureCanvas ? "opacity-0" : "opacity-100"
        }`}
      >
        {children ?? (
          <div className="liquid-glass pointer-events-auto w-full max-w-2xl space-y-6 rounded-3xl border border-white/15 bg-white/[0.03] p-6 shadow-2xl backdrop-blur-md sm:p-8">
            <div className="space-y-2.5">
              <span className="inline-block rounded-full border border-white/15 bg-white/[0.05] px-3 py-0.5 font-mono text-[10px] tracking-widest text-slate-300 uppercase">
                OMNILOG // CROSS-MEDIA ARCHIVE
              </span>
              <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-4xl">
                Every story, choice &amp; chapter.
              </h1>
              <p className="mx-auto max-w-xl text-xs leading-relaxed text-slate-300 sm:text-sm">
                OmniLog is a cross-media tracking and narrative journaling platform for video games,
                TV series, and movies — track your library, rate chapters and episodes, log playtime
                and branching decisions, and explore spoiler-safe recommendations.
              </p>
            </div>

            {user ? (
              <div className="space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-left">
                  <div>
                    <p className="text-xs font-medium text-white">
                      Welcome back, <span className="text-cyan-300">@{user.username}</span>
                    </p>
                    <p className="text-[11px] text-slate-300">
                      {entries.length === 1
                        ? "1 title in your personal library"
                        : `${entries.length} titles in your personal library`}
                    </p>
                  </div>
                  <Link
                    href="/library"
                    className="rounded-xl border border-cyan-400/40 bg-cyan-500/20 px-3.5 py-1.5 text-xs font-medium text-cyan-100 transition-colors hover:bg-cyan-500/30"
                  >
                    Open Library
                  </Link>
                </div>

                <form
                  onSubmit={handleSearchSubmit}
                  className="liquid-glass flex items-center gap-2 rounded-2xl border border-white/15 bg-white/[0.04] px-3.5 py-2 focus-within:border-cyan-400/50"
                >
                  <span className="font-mono text-xs text-slate-400">/</span>
                  <input
                    ref={searchInputRef}
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search games, series, movies..."
                    aria-label="Search catalog"
                    className="w-full bg-transparent text-xs text-white placeholder-slate-400 focus:outline-none sm:text-sm"
                  />
                  <button
                    type="submit"
                    className="rounded-xl border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-white transition-colors hover:border-cyan-400/40 hover:bg-cyan-500/20"
                  >
                    Search
                  </button>
                </form>

                <div className="flex flex-wrap items-center justify-center gap-1.5">
                  {(
                    [
                      { key: "ALL", label: "All Media" },
                      { key: "GAME", label: "Video Games" },
                      { key: "SERIES", label: "TV Series" },
                      { key: "MOVIE", label: "Movies" },
                    ] as const
                  ).map((f) => (
                    <button
                      key={f.key}
                      type="button"
                      onClick={() => setMediaFilter(f.key)}
                      className={`rounded-full border px-3 py-1 text-[11px] font-medium transition-all ${
                        mediaFilter === f.key
                          ? "border-cyan-400/40 bg-cyan-500/20 text-cyan-200"
                          : "border-white/10 bg-white/[0.04] text-slate-300 hover:text-white"
                      }`}
                    >
                      {f.label}
                    </button>
                  ))}

                  <span className="mx-1 h-3 w-px bg-white/15" />

                  <Link
                    href="/library"
                    className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] font-medium text-slate-200 transition-colors hover:border-white/25 hover:text-white"
                  >
                    Library
                  </Link>
                  <Link
                    href="/lists"
                    className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] font-medium text-slate-200 transition-colors hover:border-white/25 hover:text-white"
                  >
                    Lists
                  </Link>
                  <Link
                    href="/diary"
                    className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] font-medium text-slate-200 transition-colors hover:border-white/25 hover:text-white"
                  >
                    Diary
                  </Link>
                  <Link
                    href="/recommendations"
                    className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] font-medium text-slate-200 transition-colors hover:border-white/25 hover:text-white"
                  >
                    Recommendations
                  </Link>
                  <Link
                    href="/stats"
                    className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] font-medium text-slate-200 transition-colors hover:border-white/25 hover:text-white"
                  >
                    Stats
                  </Link>
                </div>

                {entries.length > 0 && (
                  <div className="space-y-2 text-left">
                    <div className="flex items-center justify-between">
                      <h2 className="font-mono text-[11px] tracking-wider text-slate-300 uppercase">
                        Recent in Your Library
                      </h2>
                      <Link
                        href="/library"
                        className="text-[11px] font-medium text-cyan-300 hover:underline"
                      >
                        View all →
                      </Link>
                    </div>
                    <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                      {entries.slice(0, 4).map((entry) => (
                        <Link
                          key={entry.id}
                          href={`/title/${entry.media_item_id}`}
                          className="flex items-center justify-between gap-2 rounded-2xl border border-white/10 bg-white/[0.03] px-3.5 py-2.5 transition-colors hover:border-cyan-400/40 hover:bg-white/[0.06]"
                        >
                          <div className="min-w-0">
                            <p className="truncate text-xs font-semibold text-white">
                              {entry.media_item.title}
                            </p>
                            <p className="text-[10px] text-slate-400">
                              {entry.media_item.media_type} • {entry.status.replace(/_/g, " ")}
                            </p>
                          </div>
                          {entry.rating !== null && (
                            <span className="shrink-0 rounded-full border border-amber-400/30 bg-amber-500/15 px-2 py-0.5 text-[11px] font-semibold text-amber-200">
                              ★ {entry.rating}
                            </span>
                          )}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex flex-wrap items-center justify-center gap-3">
                  <Link
                    href="/register"
                    className="rounded-2xl border border-cyan-400/50 bg-cyan-500/20 px-5 py-2.5 text-xs font-semibold text-white shadow-lg transition-all hover:border-cyan-300 hover:bg-cyan-500/30 sm:text-sm"
                  >
                    Register
                  </Link>
                  <Link
                    href="/login"
                    className="rounded-2xl border border-white/15 bg-white/[0.05] px-5 py-2.5 text-xs font-semibold text-slate-200 transition-all hover:border-white/30 hover:bg-white/10 hover:text-white sm:text-sm"
                  >
                    Log in
                  </Link>
                </div>

                <div className="grid grid-cols-1 gap-3 text-left sm:grid-cols-2">
                  {MAIN_FEATURES.map((feature) => (
                    <div
                      key={feature.title}
                      className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"
                    >
                      <h2 className="text-xs font-semibold text-white sm:text-sm">
                        {feature.title}
                      </h2>
                      <p className="mt-1 text-[11px] leading-relaxed text-slate-300">
                        {feature.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="pointer-events-none fixed inset-x-0 bottom-4 z-40 flex items-center justify-between px-6">
        <span className="hidden font-mono text-[11px] text-slate-400 sm:inline">
          CLICK EMPTY SPACE TO SCATTER • PRESS &apos;H&apos; FOR PURE CANVAS
        </span>
        <button
          type="button"
          onClick={() => setPureCanvas((p) => !p)}
          className="liquid-glass pointer-events-auto ml-auto rounded-xl border border-white/15 bg-white/[0.05] px-3 py-1.5 font-mono text-xs text-slate-200 backdrop-blur-md transition-colors hover:border-white/25 hover:text-white"
        >
          UI: {pureCanvas ? "Pure Canvas" : "Minimal"}
        </button>
      </div>
    </section>
  );
}
