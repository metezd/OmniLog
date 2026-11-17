"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

type MediaFilter = "ALL" | "GAME" | "SERIES" | "MOVIE";

export interface AtmosphericHeroProps {
  glowOpacity?: number;
  setGlowOpacity?: React.Dispatch<React.SetStateAction<number>>;
  onToast?: (msg: string) => void;
  children?: React.ReactNode;
}

export default function AtmosphericHero({ children }: AtmosphericHeroProps) {
  const router = useRouter();
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const [pureCanvas, setPureCanvas] = useState(false);
  const [query, setQuery] = useState("");
  const [mediaFilter, setMediaFilter] = useState<MediaFilter>("ALL");

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement | null)?.tagName;
      const inInput = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";

      if (e.key === "/" && !inInput) {
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
    <section className="relative min-h-[calc(100vh-8rem)] w-full select-none flex flex-col items-center justify-center px-4 bg-transparent">
      <div
        className={`pointer-events-none relative z-40 flex flex-col items-center justify-center text-center transition-opacity duration-300 ${
          pureCanvas ? "opacity-0" : "opacity-100"
        }`}
      >
        {children ?? (
          <div className="liquid-glass pointer-events-auto w-full max-w-xl space-y-5 rounded-3xl border border-white/15 bg-white/[0.03] p-6 shadow-2xl backdrop-blur-md sm:p-8">
            <div className="space-y-2">
              <span className="inline-block rounded-full border border-white/15 bg-white/[0.05] px-3 py-0.5 font-mono text-[10px] tracking-widest text-slate-300 uppercase">
                OMNILOG // MEDIA ARCHIVE
              </span>
              <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-4xl">
                Every story, choice &amp; chapter.
              </h1>
              <p className="text-xs text-slate-300">
                Click anywhere on empty space to scatter the ASCII swarm, or search the catalog below.
              </p>
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

            <div className="flex flex-wrap items-center justify-center gap-1.5 pt-1">
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
          </div>
        )}
      </div>

      <div className="pointer-events-none fixed inset-x-0 bottom-4 z-40 flex items-center justify-between px-6">
        <span className="hidden sm:inline font-mono text-[11px] text-slate-400">
          CLICK EMPTY SPACE TO SCATTER • PRESS &apos;/&apos; TO SEARCH • &apos;H&apos; FOR PURE CANVAS
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
