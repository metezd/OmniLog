"use client";

import React from "react";

export interface LogoProps {
  size?: number;
  showText?: boolean;
}

export function LogoMark({ size = 52 }: { size?: number }) {
  return (
    <svg
      style={{ width: size, height: size }}
      viewBox="0 0 128 128"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="shrink-0 scale-100 hover:scale-[1.05] transition-transform duration-300"
    >
      <defs>
        {/* Glow / Refraction Shadow for Pixel Pumpkin */}
        <filter id="cyberPumpkinGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow
            dx="0"
            dy="3"
            stdDeviation="4"
            floodColor="#E51D24"
            floodOpacity="0.85"
          />
          <feDropShadow
            dx="0"
            dy="0"
            stdDeviation="8"
            floodColor="#E26D22"
            floodOpacity="0.5"
          />
        </filter>

        {/* Dynamic Multi-layered Blaze/Alev Gradient */}
        <linearGradient id="blazeGrad" x1="0%" y1="100%" x2="0%" y2="0%">
          <stop offset="0%" stopColor="#7A0C22" />
          <stop offset="30%" stopColor="#E51D24" />
          <stop offset="70%" stopColor="#FB923C" />
          <stop offset="100%" stopColor="#FFF066" />
        </linearGradient>

        <style>
          {`
            @keyframes pixelFlicker {
              0%, 100% { opacity: 0.8; filter: brightness(0.95) drop-shadow(0 0 1px #E51D24); }
              50% { opacity: 1; filter: brightness(1.25) drop-shadow(0 0 3px #FFF066); }
            }
            .fire-core {
              animation: pixelFlicker 0.4s infinite alternate ease-in-out;
            }
            .spark {
              animation: pixelFlicker 0.8s infinite alternate ease-in-out;
            }
          `}
        </style>
      </defs>

      <g filter="url(#cyberPumpkinGlow)">
        {/* Step 1: Deep Background Shadow Mesh (To maintain pixel consistency) */}
        <rect x="16" y="16" width="96" height="96" rx="4" fill="#0D0407" opacity="0.95" />

        {/* Step 2: Stem / Witch Hat Accent on Top (Pixel Style) */}
        {/* Stem Back - Witchy bend at the top */}
        <path d="M 60 12 h 8 v 4 h -4 v 4 h -4 v -8 Z" fill="#7A0C22" />
        <path d="M 52 20 h 24 v 4 h -24 Z" fill="#E51D24" />
        <path d="M 56 16 h 12 v 4 h -12 Z" fill="#E51D24" />

        {/* Step 3: Main Pumpkin Body Outer Border (Retro pixel layers) */}
        {/* Dark crimson outer edge */}
        <path
          d="
            M 48 20 h 32 v 4 h 8 v 4 h 8 v 4 h 4 v 8 h 4 v 12 h 4 v 24 h -4 v 16 h -4 v 8 h -8 v 4 h -8 v 4 h -24 v -4 h -12 v -4 h -8 v -8 h -4 v -16 h -4 v -24 h 4 v -12 h 4 v -8 h 8 v -4 h 8 v -4 Z
          "
          fill="#5c0615"
        />
        {/* Glowing bright crimson outline pixels */}
        <path
          d="
            M 44 24 h 40 v 4 h 8 v 4 h 4 v 8 h 4 v 12 h 4 v 20 h -4 v 16 h -4 v 8 h -8 v 4 h -8 v 4 h -24 v -4 h -8 v -4 h -8 v -8 h -4 v -16 h -4 v -20 h 4 v -12 h 4 v -8 h 4 v -4 h 8 v -4 Z
          "
          fill="#E51D24"
        />
        {/* Hot Pink inner specular highlights (Double border look) */}
        <path
          d="
            M 48 28 h 32 v 4 h 8 v 4 h 4 v 8 h 4 v 8 h 4 v 16 h -4 v 12 h -4 v 8 h -8 v 4 h -4 v 4 h -16 v -4 h -8 v -4 h -8 v -8 h -4 v -12 h -4 v -16 h 4 v -8 h 4 v -8 h 4 v -4 h 8 Z
          "
          fill="#FF3366"
          opacity="0.85"
        />

        {/* Step 4: Highly visible pixelated "X" and "+" text patterns (Texture) */}
        {/* We use pixel SVG text elements to explicitly create the requested retro patterns */}
        <g fill="#FF2E5B" opacity="0.45" fontFamily="monospace" fontSize="8" fontWeight="900" letterSpacing="0">
          <text x="36" y="36">× × × × × × ×</text>
          <text x="32" y="44">× × × × × × × × ×</text>
          <text x="24" y="52">× × × × + + × × × × ×</text>
          <text x="20" y="60">+ + + × × × × × + + +</text>
          <text x="24" y="68">× × × × + + × × × ×</text>
          <text x="28" y="76">× × × × × × × ×</text>
          <text x="36" y="84">× × × × × ×</text>
          <text x="44" y="92">+ + + +</text>
        </g>

        {/* Plus / X Highlight accents scattered throughout the body (For pixel depth) */}
        <g fill="#FFA3B1" opacity="0.7" fontFamily="monospace" fontSize="7" fontWeight="bold">
          <text x="48" y="31">++ ++</text>
          <text x="54" y="16" fill="#FFF">++</text>
          <text x="44" y="48">×</text>
          <text x="80" y="48">×</text>
          <text x="48" y="72">+</text>
          <text x="76" y="72">+</text>
          <text x="36" y="64">+</text>
          <text x="88" y="64">+</text>
        </g>

        {/* Step 5: High contrast digital faces with a natural pixel look & animation */}
        <g className="fire-core">
          {/* Evil Fire Eyes (Left & Right) */}
          {/* Left Eye: Angry look */}
          <path d="M 32 44 h 16 v 4 h -4 v 4 h -4 v 4 h -8 v -12 Z" fill="url(#blazeGrad)" />
          {/* Right Eye: Angry look */}
          <path d="M 80 44 h -16 v 4 h 4 v 4 h 4 v 4 h 8 v -12 Z" fill="url(#blazeGrad)" />

          {/* Slashed Nose */}
          <path d="M 60 56 h 8 v 4 h -8 Z M 64 60 h 4 v 4 h -4 Z" fill="url(#blazeGrad)" />

          {/* Slashed Tooth & Smile (Carved jack-o'-lantern) */}
          <path
            d="
              M 32 68 h 4 v 4 h 4 v 4 h 8 v -4 h 4 v -4 h 8 v 4 h 4 v 4 h 8 v -4 h 4 v -4 h 8 v 4 h 4 v 4 h -4 v 4 h -4 v 4 h -8 v -4 h -4 v -4 h -8 v 4 h -4 v 4 h -16 v -4 h -4 v -4 h -8 v -4 h -4 v -4 Z
            "
            fill="url(#blazeGrad)"
          />
          
          {/* Innermost Core Glow Overlay for high intensity */}
          <path d="M 36 48 h 4 v 4 h -4 Z M 88 48 h -4 v 4 h 4 Z" fill="#FFF066" />
          <path d="M 44 76 h 8 v 4 h -8 Z M 76 76 h 8 v 4 h -8 Z" fill="#FFF066" opacity="0.9" />
          <path d="M 56 68 h 16 v 4 h -16 Z" fill="#FFF066" />
        </g>

        {/* Sparks and glitch embers around the pumpkin (Like digital pixel decay) */}
        <g className="spark" fill="#E26D22">
          <rect x="100" y="32" width="3" height="3" />
          <rect x="24" y="24" width="2" height="2" fill="#E51D24" />
          <rect x="12" y="56" width="3" height="3" />
          <rect x="108" y="68" width="4" height="2" />
          <rect x="44" y="96" width="3" height="3" fill="#FFF066" />
          <rect x="80" y="96" width="3" height="2" fill="#FF3366" />
          <rect x="92" y="84" width="2" height="2" />
          <rect x="32" y="88" width="3" height="3" />
        </g>
      </g>
    </svg>
  );
}

export default function Logo({ size = 52, showText = true }: LogoProps) {
  return (
    <div className="inline-flex items-center gap-3.5 select-none">
      <LogoMark size={size} />
      {showText && (
        <span className="font-bold tracking-wider text-white font-sans text-sm sm:text-base leading-none uppercase">
          Omni<span className="text-horizon-cyan font-light lowercase">Log</span>
        </span>
      )}
    </div>
  );
}