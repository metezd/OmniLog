"use client";

import React from "react";

interface PaletteToolProps {
  onToast: (msg: string) => void;
}

interface ColorToken {
  name: string;
  hex: string;
  usage: string;
  boxStyle: string;
}

const TOKENS: ColorToken[] = [
  {
    name: "Abyss Black",
    hex: "#090C15",
    usage: "Root Surface",
    boxStyle: "bg-[#090C15] border border-white/20 shadow-inner",
  },
  {
    name: "Twilight Plum",
    hex: "#1E1622",
    usage: "Card Smoked Fill",
    boxStyle: "bg-[#1E1622] border border-white/20 shadow-inner",
  },
  {
    name: "Horizon Cyan",
    hex: "#009BB9",
    usage: "Primary Flare / Link",
    boxStyle: "bg-[#009BB9] shadow-[0_0_15px_rgba(0,155,185,0.65)]",
  },
  {
    name: "Dusk Amber",
    hex: "#E26D22",
    usage: "Media Warm Badge",
    boxStyle: "bg-[#E26D22] shadow-[0_0_15px_rgba(226,109,34,0.65)]",
  },
  {
    name: "Horizon Crimson",
    hex: "#E51D24",
    usage: "Vivid Highlight",
    boxStyle: "bg-[#E51D24] shadow-[0_0_15px_rgba(229,29,36,0.65)]",
  },
  {
    name: "Deep Burgundy",
    hex: "#7A0C22",
    usage: "Atmosphere Glow",
    boxStyle: "bg-[#7A0C22] shadow-[0_0_10px_rgba(122,12,34,0.65)]",
  },
];

export default function PaletteTool({ onToast }: PaletteToolProps) {
  const copyColor = (hex: string, name: string) => {
    navigator.clipboard
      .writeText(hex)
      .then(() => {
        onToast(`Copied ${name} (${hex}) to clipboard!`);
      })
      .catch(() => {
        onToast(`Selected ${name} (${hex})`);
      });
  };

  return (
    <section
      id="inspector"
      className="liquid-glass rounded-3xl p-6 sm:p-8 border border-white/10 space-y-6"
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Cinematic Horizon Design System Tokens
          </h2>
          <p className="text-xs text-slate-400">
            Click any swatch to copy its exact hex value to your clipboard
          </p>
        </div>
        <div className="text-[11px] font-mono text-cyan-400 bg-cyan-950/40 px-3 py-1 rounded-lg border border-cyan-500/30">
          Ready for Tailwind & Figma
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {TOKENS.map((token) => (
          <button
            key={token.hex}
            type="button"
            onClick={() => copyColor(token.hex, token.name)}
            className="group p-3 rounded-2xl bg-black/40 hover:bg-black/60 border border-white/10 hover:border-cyan-400/50 transition-all text-left flex flex-col justify-between h-36 active:scale-95"
          >
            <div className={`w-full h-12 rounded-xl ${token.boxStyle}`} />
            <div>
              <div className="text-xs font-semibold text-white group-hover:text-cyan-300 transition-colors">
                {token.name}
              </div>
              <div className="text-[10px] font-mono text-slate-400">
                {token.hex}
              </div>
              <div className="text-[9px] text-slate-500 mt-0.5">
                {token.usage}
              </div>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}