"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError("Please fill in all fields.");
      return;
    }
    router.push("/");
  };

  const handleGoogleSignIn = () => {
    console.log("Redirecting to Google Auth...");
    router.push("/");
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4">
      <div className="liquid-glass w-full max-w-md rounded-2xl p-8 border border-white/15 shadow-[0_0_50px_rgba(168,85,247,0.15)] space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Welcome Back
          </h1>
          <p className="text-xs text-slate-400">
            Sign in to access your media logs & friend stream
          </p>
        </div>

        <button
          type="button"
          onClick={handleGoogleSignIn}
          className="w-full flex items-center justify-center gap-3 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 border border-white/20 text-white font-medium text-xs transition-all shadow-lg active:scale-95"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
            />
            <path
              fill="#34A853"
              d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.11-6.72-4.96H1.29v3.15C3.26 21.3 7.31 24 12 24z"
            />
            <path
              fill="#FBBC05"
              d="M5.28 14.24c-.25-.72-.38-1.49-.38-2.24s.13-1.52.38-2.24V6.61H1.29C.47 8.24 0 10.06 0 12s.47 3.76 1.29 5.39l3.99-3.15z"
            />
            <path
              fill="#EA4335"
              d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.26 2.7 1.29 6.61l3.99 3.15c.95-2.85 3.6-4.96 6.72-4.96z"
            />
          </svg>
          <span>Continue with Google</span>
        </button>

        <div className="flex items-center gap-3 my-2">
          <div className="flex-1 h-px bg-white/10" />
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">
            or sign in with email
          </span>
          <div className="flex-1 h-px bg-white/10" />
        </div>

        {error && (
          <div className="bg-rose-500/10 border border-rose-500/30 p-3 rounded-xl text-xs text-rose-300 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300">
              Username or Email
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username..."
              className="w-full rounded-xl bg-black/50 border border-white/10 px-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-horizon-cyan focus:ring-1 focus:ring-horizon-cyan transition-all"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <label className="text-xs font-medium text-slate-300">
                Password
              </label>
              <a
                href="#"
                className="text-[11px] text-horizon-cyan hover:underline"
              >
                Forgot?
              </a>
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-xl bg-black/50 border border-white/10 px-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-horizon-cyan focus:ring-1 focus:ring-horizon-cyan transition-all"
            />
          </div>

          <button
            type="submit"
            className="w-full py-2.5 rounded-xl bg-horizon-crimson/30 hover:bg-horizon-crimson/50 border border-horizon-crimson/60 text-white font-medium text-xs transition-all shadow-[0_0_20px_rgba(229,29,36,0.3)] active:scale-95"
          >
            Sign In
          </button>
        </form>

        <div className="text-center pt-2 border-t border-white/10">
          <p className="text-xs text-slate-400">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              className="text-cyan-400 hover:text-cyan-300 font-semibold underline"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}