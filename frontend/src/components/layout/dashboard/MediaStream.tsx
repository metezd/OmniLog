"use client";

import React, { useState } from "react";

interface MediaItem {
  id: string;
  type: "game" | "tv";
  title: string;
  subtitle: string;
  rating: string;
  badge: string;
  badgeColor: string;
  statusText: string;
  statusValue: string;
  progressPercent: number;
  imageUrl: string;
  actionText: string;
  isCompleted?: boolean;
}

const INITIAL_MEDIA: MediaItem[] = [
  {
    id: "1",
    type: "game",
    title: "Cyberpunk 2077",
    subtitle: "Phantom Liberty DLC • Act II",
    rating: "★ 9.4",
    badge: "Playing",
    badgeColor: "bg-emerald-500/20 border-emerald-400/40 text-emerald-300",
    statusText: "Progress: 72%",
    statusValue: "68h logged",
    progressPercent: 72,
    imageUrl:
      "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=700&q=80",
    actionText: "+ Log +2 Hours",
  },
  {
    id: "2",
    type: "tv",
    title: "Arcane: Season 2",
    subtitle: "Act III: The Reckoning",
    rating: "★ 9.8",
    badge: "Watching",
    badgeColor: "bg-purple-500/20 border-purple-400/40 text-purple-300",
    statusText: "Episodes: 6 / 9",
    statusValue: "66%",
    progressPercent: 66,
    imageUrl:
      "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=700&q=80",
    actionText: "+ Mark Next Episode",
  },
  {
    id: "3",
    type: "game",
    title: "Elden Ring DLC",
    subtitle: "Realm of Shadow • 100%",
    rating: "★ 9.7",
    badge: "Completed",
    badgeColor: "bg-rose-500/20 border-rose-400/40 text-rose-300",
    statusText: "Status: Finished",
    statusValue: "112h",
    progressPercent: 100,
    imageUrl:
      "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=700&q=80",
    actionText: "✓ All Bosses Defeated",
    isCompleted: true,
  },
  {
    id: "4",
    type: "tv",
    title: "Severance",
    subtitle: "Season 1 Finale Rewatch",
    rating: "★ 9.5",
    badge: "In Queue",
    badgeColor: "bg-sky-500/20 border-sky-400/40 text-sky-300",
    statusText: "Episodes: 8 / 9",
    statusValue: "88%",
    progressPercent: 88,
    imageUrl:
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=700&q=80",
    actionText: "+ Finish Season",
  },
];

interface MediaStreamProps {
  onToast: (msg: string) => void;
  searchQuery?: string;
}

export default function MediaStream({
  onToast,
  searchQuery = "",
}: MediaStreamProps) {
  const [filter, setFilter] = useState<"all" | "game" | "tv">("all");
  const [mediaList, setMediaList] = useState<MediaItem[]>(INITIAL_MEDIA);

  const handleAction = (item: MediaItem) => {
    if (item.isCompleted) return;
    onToast(`Logged activity for ${item.title}`);
    setMediaList((prev) =>
      prev.map((m) =>
        m.id === item.id
          ? {
              ...m,
              progressPercent: Math.min(100, m.progressPercent + 5),
            }
          : m
      )
    );
  };

  const filteredMedia = mediaList.filter((item) => {
    const matchesFilter = filter === "all" || item.type === filter;
    const matchesSearch =
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.subtitle.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <section id="library" className="space-y-6">
      {/* Header & Filter Tabs */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Active Media Stream
          </h2>
          <p className="text-xs text-slate-400">
            Track and update individual progression records
          </p>
        </div>

        {/* Filter Pill Tabs */}
        <div className="flex items-center gap-1.5 bg-black/40 p-1 rounded-xl border border-white/10">
          <button
            type="button"
            onClick={() => setFilter("all")}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === "all"
                ? "text-white bg-white/15 shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            All Media
          </button>
          <button
            type="button"
            onClick={() => setFilter("game")}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === "game"
                ? "text-white bg-white/15 shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Video Games
          </button>
          <button
            type="button"
            onClick={() => setFilter("tv")}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === "tv"
                ? "text-white bg-white/15 shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            TV Series
          </button>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {filteredMedia.map((item) => (
          <div
            key={item.id}
            className="liquid-glass liquid-glass-card rounded-2xl overflow-hidden flex flex-col group"
          >
            {/* Image Banner */}
            <div className="relative h-44 w-full overflow-hidden">
              <img
                src={item.imageUrl}
                alt={item.title}
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#090C15] via-[#090C15]/40 to-transparent" />
              <span
                className={`absolute top-3 left-3 px-2 py-0.5 rounded-full text-[10px] font-semibold backdrop-blur-md ${
                  item.type === "game"
                    ? "bg-horizon-cyan/20 border border-horizon-cyan/40 text-cyan-300"
                    : "bg-horizon-amber/20 border border-horizon-amber/40 text-amber-300"
                }`}
              >
                {item.type === "game" ? "Game" : "TV Series"}
              </span>
              <span
                className={`absolute top-3 right-3 px-2 py-0.5 rounded-full text-[10px] font-semibold border backdrop-blur-md ${item.badgeColor}`}
              >
                {item.badge}
              </span>
            </div>

            {/* Body */}
            <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-white tracking-tight">
                    {item.title}
                  </h3>
                  <span className="text-xs font-semibold text-amber-400">
                    {item.rating}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">{item.subtitle}</p>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-[11px] text-slate-400">
                  <span>{item.statusText}</span>
                  <span className="text-slate-300 font-mono">
                    {item.statusValue}
                  </span>
                </div>
                <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      item.isCompleted ? "bg-emerald-400" : "horizon-bar-fill"
                    }`}
                    style={{ width: `${item.progressPercent}%` }}
                  />
                </div>
              </div>

              {/* Action Button */}
              <button
                type="button"
                onClick={() => handleAction(item)}
                disabled={item.isCompleted}
                className={`w-full py-1.5 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1.5 active:scale-95 ${
                  item.isCompleted
                    ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 cursor-default"
                    : "bg-white/5 hover:bg-cyan-500/20 text-slate-200 hover:text-cyan-200 border border-white/10 hover:border-cyan-400/40"
                }`}
              >
                <span>{item.actionText}</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}