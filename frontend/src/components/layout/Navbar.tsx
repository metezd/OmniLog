"use client";

import React from "react";
import Link from "next/link";
import Logo from "./Logo";

export default function Navbar() {
  return (
    <header className="sticky top-4 z-50 w-full px-4 sm:px-8 select-none">
      <div className="max-w-7xl mx-auto">
        {/* Floating Island Container that stays fixed at the top on scroll */}
        <nav className="liquid-glass flex items-center justify-between px-6 py-3 rounded-2xl border border-white/15 shadow-[0_8px_32px_rgba(0,0,0,0.5)] backdrop-blur-xl bg-[#09030e]/80 transition-all duration-300">
          
          {/* Left: Logo */}
          <Link href="/" className="flex items-center gap-2">
            <Logo />
          </Link>

          {/* Center: Navigation Links */}
          <div className="hidden md:flex items-center gap-8 text-xs font-medium text-slate-300">
            <Link href="/" className="hover:text-white transition-colors">
              Library
            </Link>
            <Link href="/search" className="hover:text-white transition-colors">
              Search
            </Link>
            <Link href="/dashboard" className="hover:text-white transition-colors">
              Dashboard
            </Link>
            <a
              href="https://github.com/metezd/OmniLog"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white transition-colors flex items-center gap-1.5"
            >
              <span>★ GitHub</span>
            </a>
          </div>

          {/* Right: Actions (Sign In / Get Started) */}
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-xs font-medium text-slate-300 hover:text-white px-3 py-2 transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="rounded-xl bg-horizon-crimson/30 hover:bg-horizon-crimson/50 border border-horizon-crimson/60 px-4 py-2 text-xs font-medium text-white transition-all shadow-[0_0_20px_rgba(229,29,36,0.3)] active:scale-95"
            >
              Get Started
            </Link>
          </div>
        </nav>
      </div>
    </header>
  );
}