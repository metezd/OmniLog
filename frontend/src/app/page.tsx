"use client";

import React, { useState } from "react";
import AtmosphericHero from "@/components/layout/dashboard/AtmosphericHero";

export default function Home() {
  const [glowOpacity, setGlowOpacity] = useState(0.35);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => {
      setToastMsg(null);
    }, 2200);
  };

  return (
    <div className="relative min-h-[calc(100vh-4rem)] w-full bg-[#05070d]">
      {/* Subtle Toast Notification */}
      <div
        className={`pointer-events-none fixed bottom-16 right-6 z-50 flex items-center gap-2.5 rounded-xl border border-white/15 bg-black/80 px-3.5 py-2 text-xs text-slate-200 shadow-2xl backdrop-blur-md transition-all duration-300 ${
          toastMsg ? "translate-y-0 opacity-100" : "translate-y-12 opacity-0"
        }`}
      >
        <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
        <span>{toastMsg}</span>
      </div>

      <AtmosphericHero
        glowOpacity={glowOpacity}
        setGlowOpacity={setGlowOpacity}
        onToast={showToast}
      />
    </div>
  );
}
