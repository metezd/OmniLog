import React from "react";

export interface LogoProps {
  className?: string;
  size?: number;
  showText?: boolean;
}

export function Logo({
  className = "",
  size = 32,
  showText = false,
}: LogoProps) {
  return (
    <div className={`inline-flex items-center gap-2.5 select-none ${className}`}>
      {/* Liquid Glass Infinity Mark */}
      <svg
        style={{ width: size, height: size / 2 }}
        viewBox="0 0 160 80"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0"
      >
        <defs>
          <linearGradient id="glassLinear" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.9" />
            <stop offset="45%" stopColor="#94A3B8" stopOpacity="0.3" />
            <stop offset="70%" stopColor="#FFFFFF" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.4" />
          </linearGradient>

          <filter id="glassDrop" x="-20%" y="-20%" width="150%" height="150%">
            <feDropShadow
              dx="0"
              dy="3"
              stdDeviation="4"
              floodColor="#000000"
              floodOpacity="0.4"
            />
            <feDropShadow
              dx="0"
              dy="1"
              stdDeviation="2"
              floodColor="#38BDF8"
              floodOpacity="0.25"
            />
          </filter>
        </defs>

        <path
          d="M 50 40 C 25 10, 10 30, 20 50 C 30 70, 60 65, 80 40 C 100 15, 130 10, 140 30 C 150 50, 135 70, 110 65"
          stroke="#06B6D4"
          strokeWidth="10"
          strokeOpacity="0.15"
          strokeLinecap="round"
          className="blur-[4px]"
        />

        <path
          d="M 50 40 C 25 10, 10 30, 20 50 C 30 70, 60 65, 80 40 C 100 15, 130 10, 140 30 C 150 50, 135 70, 110 65"
          stroke="url(#glassLinear)"
          strokeWidth="8"
          strokeLinecap="round"
          fill="none"
          filter="url(#glassDrop)"
        />

        <path
          d="M 48 38 C 28 14, 16 30, 22 46 C 28 62, 54 58, 80 40 C 102 18, 128 14, 136 30"
          stroke="#FFFFFF"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeOpacity="0.8"
          fill="none"
        />

        <circle
          cx="140"
          cy="48"
          r="3"
          fill="#FFFFFF"
          fillOpacity="0.9"
          filter="drop-shadow(0 0 3px #38BDF8)"
        />
      </svg>

      {showText && (
        <span className="font-semibold tracking-tight text-white font-sans">
          Omni<span className="text-cyan-400 font-light">Log</span>
        </span>
      )}
    </div>
  );
}

// Navbar.tsx içindeki <LogoMark size={32} /> çağrısıyla eşleşmesi için alias
export const LogoMark = Logo;
export default Logo;
