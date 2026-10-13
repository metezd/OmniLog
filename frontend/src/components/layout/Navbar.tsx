"use client";

import React, { useState } from "react";
import Link from "next/link";
import Logo from "./Logo";

const NAV_LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/login", label: "Sign In" },
  { href: "/register", label: "Sign Up" },
];

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav
      aria-label="Main navigation"
      className="sticky top-0 z-50 w-full border-b border-white/10 bg-horizon-abyss/85 backdrop-blur-xl transition-all duration-300 shadow-[0_4px_30px_rgba(0,0,0,0.5)]"
    >
      <div className="mx-auto flex h-20 max-w-6xl items-center justify-between px-4 sm:px-6">
        {/* Brand / Logo */}
        <Link
          href="/"
          className="flex items-center gap-3 transition-transform duration-200 hover:scale-[1.03]"
          onClick={() => setIsOpen(false)}
        >
          <Logo size={52} showText={true} />
        </Link>

        {/* Desktop Navigation Links & Action */}
        <div className="hidden items-center gap-6 md:flex">
          <ul className="flex items-center gap-1.5">
            {NAV_LINKS.map(({ href, label }) => (
              <li key={href}>
                <Link
                  href={href}
                  className="rounded-lg px-3.5 py-2 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/5 hover:text-white hover:shadow-[0_0_12px_rgba(0,155,185,0.2)]"
                >
                  {label}
                </Link>
              </li>
            ))}
          </ul>

          <Link
            href="/register"
            className="rounded-lg border border-horizon-crimson/50 bg-horizon-crimson/20 px-4 py-2 text-sm font-medium text-white shadow-[0_0_15px_rgba(229,29,36,0.35)] backdrop-blur-md transition-all duration-200 hover:border-horizon-crimson hover:bg-horizon-crimson/40 hover:shadow-[0_0_22px_rgba(229,29,36,0.55)] active:scale-95"
          >
            Get Started
          </Link>
        </div>

        {/* Mobile Hamburger Toggle Button */}
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Toggle navigation menu"
          className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-slate-300 transition-colors hover:bg-white/10 hover:text-white md:hidden"
        >
          <svg
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            {isOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Drawer Menu */}
      {isOpen && (
        <div className="border-b border-white/10 bg-horizon-abyss/95 px-4 pt-3 pb-6 backdrop-blur-2xl md:hidden">
          <ul className="flex flex-col gap-2">
            {NAV_LINKS.map(({ href, label }) => (
              <li key={href}>
                <Link
                  href={href}
                  onClick={() => setIsOpen(false)}
                  className="block rounded-lg px-3 py-2 text-base font-medium text-slate-200 transition-colors hover:bg-white/10 hover:text-white"
                >
                  {label}
                </Link>
              </li>
            ))}
            <li className="pt-2">
              <Link
                href="/register"
                onClick={() => setIsOpen(false)}
                className="block text-center rounded-lg border border-horizon-crimson/50 bg-horizon-crimson/25 px-4 py-2.5 text-base font-medium text-white shadow-[0_0_15px_rgba(229,29,36,0.3)] transition-all hover:bg-horizon-crimson/40"
              >
                Get Started
              </Link>
            </li>
          </ul>
        </div>
      )}
    </nav>
  );
}