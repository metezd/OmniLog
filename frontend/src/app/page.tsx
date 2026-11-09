"use client";

import React, { useState } from "react";
import AtmosphericHero from "@/components/layout/dashboard/AtmosphericHero";
import StatsGrid from "@/components/layout/dashboard/StatsGrid";
import MediaStream from "@/components/layout/dashboard/MediaStream";
import PaletteTool from "@/components/layout/dashboard/PaletteTool";

export default function Home() {
  const [glowOpacity, setGlowOpacity] = useState(0.35);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => {
      setToastMsg(null);
    }, 2600);
  };

  return (
    <>
      {/* Dynamic Background Flare Bar */}
      <div
        className="horizon-flare pointer-events-none fixed -top-36 left-1/2 -translate-x-1/2 w-[1100px] h-[340px] rounded-full z-0 transition-opacity duration-300"
        style={{ opacity: glowOpacity }}
      />

      {/* Bottom Underglow */}
      <div className="pointer-events-none fixed -bottom-48 right-10 w-[550px] h-[280px] bg-gradient-to-r from-horizon-burgundy via-horizon-amber to-transparent blur-[110px] opacity-20 z-0" />

      {/* Toast Notification Container */}
      <div
        className={`fixed bottom-6 right-6 z-50 transition-all duration-300 pointer-events-none liquid-glass px-4 py-3 rounded-xl border border-cyan-400/30 flex items-center gap-3 text-sm shadow-2xl ${
          toastMsg
            ? "translate-y-0 opacity-100"
            : "translate-y-24 opacity-0"
        }`}
      >
        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
        <span className="font-medium text-slate-200">{toastMsg}</span>
      </div>

      {/* Main Dashboard Container */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-8 py-8 space-y-12">
        <AtmosphericHero
          glowOpacity={glowOpacity}
          setGlowOpacity={setGlowOpacity}
          onToast={showToast}
        />
        <StatsGrid />
        <MediaStream onToast={showToast} />
        <PaletteTool onToast={showToast} />
      </div>
    </>
  );
}