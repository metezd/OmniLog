"use client";

import React, { useState, useEffect } from "react";

interface AtmosphericHeroProps {
  glowOpacity: number;
  setGlowOpacity: (val: number) => void;
  onToast: (msg: string) => void;
}

export default function AtmosphericHero({
  glowOpacity,
  setGlowOpacity,
  onToast,
}: AtmosphericHeroProps) {
  const [frost, setFrostState] = useState(20);

  const handleFrostChange = (level: number) => {
    setFrostState(level);
    document.documentElement.style.setProperty("--glass-blur", `${level}px`);
    onToast(`Frost blur tuned to ${level}px`);
  };

  return (
    <section className="liquid-glass rounded-3xl p-6 sm:p-8 relative overflow-hidden border border-white/10">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
        {/* Sol Metin & Rozet */}
        <div className="space-y-3 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-horizon-burgundy/40 text-rose-300 border border-rose-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
            Cinematic Horizon • Liquid Glass v2.4
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Centralized Media Logs &{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-amber-400 to-rose-400">
              Atmospheric Tracking
            </span>
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Monitor real-time progress across games and television with frosted
            refraction optics and twilight horizon color dynamics.
          </p>
        </div>

        {/* Canlı Işık & Cam Kontrol Paneli */}
        <div className="bg-black/40 backdrop-blur-md p-4 rounded-2xl border border-white/10 flex flex-col gap-3 min-w-[280px]">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-slate-300">Atmosphere Flare Glow</span>
            <span className="font-mono text-cyan-400 font-semibold">
              {Math.round(glowOpacity * 100)}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="80"
            value={Math.round(glowOpacity * 100)}
            onChange={(e) => setGlowOpacity(Number(e.target.value) / 100)}
            className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-white/10 rounded-lg appearance-none"
          />

          <div className="flex items-center justify-between text-xs pt-2 border-t border-white/5">
            <span className="text-slate-400">Glass Refraction Frost</span>
            <div className="flex gap-1.5">
              <button
                type="button"
                onClick={() => handleFrostChange(10)}
                className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                  frost === 10
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                    : "bg-white/5 hover:bg-white/15 text-slate-300"
                }`}
              >
                Subtle
              </button>
              <button
                type="button"
                onClick={() => handleFrostChange(20)}
                className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                  frost === 20
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                    : "bg-white/5 hover:bg-white/15 text-slate-300"
                }`}
              >
                Deep
              </button>
              <button
                type="button"
                onClick={() => handleFrostChange(36)}
                className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                  frost === 36
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                    : "bg-white/5 hover:bg-white/15 text-slate-300"
                }`}
              >
                Max
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}