"use client";

import React from "react";

export default function Logo() {
  return (
    <div className="flex items-center gap-3 group select-none">
      {/* Blue Frame Container with Centered Pumpkin Glow */}
      <div className="relative w-12 h-12 flex items-center justify-center bg-[#07090e] rounded-xl border-2 border-blue-500/50 shadow-[0_0_20px_rgba(37,99,235,0.3)] transition-all duration-300 group-hover:border-blue-400 group-hover:shadow-[0_0_25px_rgba(56,189,248,0.5)] overflow-hidden">
        
        {/* Subtle Blue & Sky Sparkle Particles */}
        <div className="absolute inset-0 opacity-50 pointer-events-none">
          <span className="absolute w-1 h-1 bg-blue-400 rounded-full animate-ping top-1.5 left-2" />
          <span className="absolute w-1.5 h-1.5 bg-sky-400 rounded-full animate-pulse bottom-1.5 right-2" />
          <span className="absolute w-0.5 h-0.5 bg-cyan-300 rounded-full top-5 right-2 animate-pulse" />
          <span className="absolute w-1 h-1 bg-blue-500 rounded-full bottom-3 left-2 animate-ping" />
        </div>

        {/* Pixel Art SVG: Centered Pumpkin with Lava Orange Body */}
        <svg
          viewBox="0 0 24 24"
          className="w-10 h-10 pixelated transform group-hover:scale-105 transition-transform duration-300"
          style={{ imageRendering: "pixelated" }}
        >
          {/* Detailed Textured Stem */}
          <path d="M11 1h2v3h-2z" fill="#3D4A1D" />
          <path d="M12 1h1v1h-1z" fill="#606F30" />
          <path d="M11 2h1v2h-1z" fill="#2E3715" />
          <path d="M13 1h1v1h-1z" fill="#3b82f6" className="animate-pulse" />

          {/* Floating Blue Particles */}
          <path d="M4 4h1v1H4z" fill="#38bdf8" className="animate-pulse" />
          <path d="M19 4h1v1h-1z" fill="#60a5fa" className="animate-pulse" />
          <path d="M2 11h1v1H2z" fill="#2563eb" className="animate-pulse" />
          <path d="M21 14h1v1H-1z" fill="#0284c7" className="animate-pulse" />

          {/* Centered Layered Pumpkin Body (Lava Orange & Dark Tones) */}
          <path d="M8 4h8v1h3v2h2v9h-1v2h-2v1H7v-1H5v-2H3v-2H2v-5h1V7h2V5h3V4z" fill="#20052B" />
          <path d="M8 5h8v1h2v1h2v8h-1v2h-2v1H7v-1H5v-2H4v-1H3V8h1V7h2v1h1V6h1V5z" fill="#500010" />
          <path d="M9 6h6v1h2v1h2v6h-1v2h-2v1H8v-1H6v-2H5V9h1V8h1V7h1V6z" fill="#8B0000" />
          <path d="M9 7h6v1h2v5h-1v1H15v1H9v-1H7v-1H6V9h1V8h1V7z" fill="#E51D24" />
          <path d="M10 8h4v4h-1v1h-2v-1H9V9h1V8z" fill="#FF5F1F" />

          {/* Centered Slanted Glowing Lava Eyes */}
          <path d="M6 9h3v1H6z" fill="#20052B" />
          <path d="M15 9h3v1h-3z" fill="#20052B" />
          <path d="M7 9h2v1H7z" fill="#FFC825" />
          <path d="M8 9h1v1H8z" fill="#FFF" />
          <path d="M15 9h2v1h-2z" fill="#FFC825" />
          <path d="M16 9h1v1h-1z" fill="#FFF" />

          {/* Glowing Nose */}
          <path d="M11 10h2v1h-2z" fill="#20052B" />
          <path d="M11 11h2v1h-2z" fill="#FFC825" />
          <path d="M12 11h1v1h-1z" fill="#FFF" />

          {/* Jagged Grin with Core Lava Glow */}
          <path d="M5 12h1v1H5zm13 0h1v1h-1z" fill="#20052B" />
          <path d="M6 13h12v2H6z" fill="#500010" />
          <path d="M7 13h10v1H7z" fill="#FF5F1F" />
          <path d="M8 13h1v1H8zm2 0h1v1H10zm4 0h1v1H14zm2 0h1v1H16z" fill="#FFC825" />
          <path d="M9 14h6v1H9z" fill="#FFF" />
          <path d="M11 15h2v1h-2z" fill="#FFA500" />
        </svg>
      </div>

      {/* Brand Text: OMNI (White) + log (Blue Glow) */}
      <span className="text-xl font-bold font-sans tracking-wide text-white uppercase flex items-center">
        OMNI
        <span className="text-sky-400 drop-shadow-[0_0_15px_rgba(56,189,248,0.85)] animate-pulse lowercase font-semibold ml-1">
          log
        </span>
      </span>
    </div>
  );
}