import React from "react";

export default function Footer() {
  return (
    <footer className="border-t border-white/5 py-8 text-center text-xs text-slate-500 bg-[#090C15]/40 backdrop-blur-sm">
      <div className="max-w-6xl mx-auto px-4">
        <p>&copy; {new Date().getFullYear()} OmniLog. Media & Game Tracker.</p>
      </div>
    </footer>
  );
}