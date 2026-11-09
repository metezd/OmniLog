"use client";

import { LogOut } from "lucide-react";
import Link from "next/link";

import { useSearch } from "@/context/SearchContext";
import { logoutAction } from "@/lib/actions/auth";
import { USER_NAV_LINKS } from "@/lib/navigation";
import type { CurrentUser } from "@/types/api";
import Logo from "./Logo";

interface NavbarProps {
  /** The logged-in user, or null for a visitor. The layout reads it from the backend. */
  user: CurrentUser | null;
}

export default function Navbar({ user }: NavbarProps) {
  const { searchQuery, setSearchQuery } = useSearch();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-black/40 backdrop-blur-xl">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 gap-4">
        {/* Left: logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <Logo />
        </Link>

        {/* Middle: live search bar */}
        <div className="flex-1 max-w-md mx-2 sm:mx-6">
          <div className="relative flex items-center">
            <svg
              className="absolute left-3.5 w-4 h-4 text-slate-400 pointer-events-none"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>

            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search games, series or titles..."
              className="w-full pl-10 pr-8 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-horizon-cyan focus:ring-1 focus:ring-horizon-cyan transition-all"
            />

            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-3 text-slate-400 hover:text-white text-xs font-bold"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Right: navigation links */}
        <nav className="flex items-center gap-4 shrink-0">
          <Link
            href="/"
            className="text-sm font-medium text-slate-300 hover:text-white transition-colors hidden sm:block"
          >
            Dashboard
          </Link>

          {user ? (
            <>
              {USER_NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
                >
                  {link.label}
                </Link>
              ))}
              <span className="hidden text-xs text-slate-400 md:block" title={user.email}>
                @{user.username}
              </span>
              {/* The logout action removes the session cookie on the server */}
              <form action={logoutAction}>
                <button
                  type="submit"
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs sm:text-sm font-medium text-slate-300 transition-all hover:border-white/25 hover:text-white active:scale-95"
                >
                  <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
                  Log out
                </button>
              </form>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="rounded-xl bg-horizon-crimson/20 border border-horizon-crimson/40 px-3.5 py-1.5 text-xs sm:text-sm font-medium text-rose-200 hover:bg-horizon-crimson/30 hover:border-horizon-crimson hover:text-white transition-all shadow-[0_0_15px_rgba(229,29,36,0.25)] active:scale-95"
              >
                Get Started
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}