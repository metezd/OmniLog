import React from "react";

export default function StatsGrid() {
  return (
    <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Stat 1: Hours Logged */}
      <div className="liquid-glass liquid-glass-card rounded-2xl p-5 border border-white/10 flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Hours Logged</span>
          <span className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </span>
        </div>
        <div className="mt-3">
          <div className="text-3xl font-extrabold text-white tracking-tight">
            384<span className="text-cyan-400 text-lg font-normal">h</span>
          </div>
          <p className="text-[11px] text-emerald-400 font-medium mt-1">
            ↑ +24h past 14 days
          </p>
        </div>
      </div>

      {/* Stat 2: Games Active */}
      <div className="liquid-glass liquid-glass-card rounded-2xl p-5 border border-white/10 flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Active Games</span>
          <span className="p-1.5 rounded-lg bg-horizon-cyan/10 text-horizon-cyan">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </span>
        </div>
        <div className="mt-3">
          <div className="text-3xl font-extrabold text-white tracking-tight">
            4{" "}
            <span className="text-xs text-slate-400 font-normal">
              in progression
            </span>
          </div>
          <p className="text-[11px] text-cyan-300 font-medium mt-1">
            Cyberpunk 2077 leading
          </p>
        </div>
      </div>

      {/* Stat 3: TV Shows Watch */}
      <div className="liquid-glass liquid-glass-card rounded-2xl p-5 border border-white/10 flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>TV Shows Watch</span>
          <span className="p-1.5 rounded-lg bg-horizon-amber/10 text-horizon-amber">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
              />
            </svg>
          </span>
        </div>
        <div className="mt-3">
          <div className="text-3xl font-extrabold text-white tracking-tight">
            7{" "}
            <span className="text-xs text-slate-400 font-normal">
              seasons cached
            </span>
          </div>
          <p className="text-[11px] text-amber-300 font-medium mt-1">
            Arcane Season 2 next
          </p>
        </div>
      </div>

      {/* Stat 4: Completion Ratio */}
      <div className="liquid-glass liquid-glass-card rounded-2xl p-5 border border-white/10 flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Completion Rate</span>
          <span className="p-1.5 rounded-lg bg-horizon-crimson/10 text-rose-400">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </span>
        </div>
        <div className="mt-3">
          <div className="text-3xl font-extrabold text-white tracking-tight">
            88<span className="text-rose-400 text-lg font-normal">%</span>
          </div>
          <div className="w-full bg-white/10 h-1.5 rounded-full mt-2 overflow-hidden">
            <div className="h-full horizon-bar-fill w-[88%] rounded-full" />
          </div>
        </div>
      </div>
    </section>
  );
}