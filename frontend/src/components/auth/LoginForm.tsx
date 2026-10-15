"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Temporary redirect to dashboard
    router.push("/");
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-slate-300">Email address</label>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="name@example.com"
          className="w-full rounded-xl bg-black/40 border border-white/10 px-3.5 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-horizon-cyan focus:outline-none focus:ring-1 focus:ring-horizon-cyan transition-all"
        />
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label className="text-xs font-medium text-slate-300">Password</label>
        </div>
        <input
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          className="w-full rounded-xl bg-black/40 border border-white/10 px-3.5 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-horizon-cyan focus:outline-none focus:ring-1 focus:ring-horizon-cyan transition-all"
        />
      </div>

      <button
        type="submit"
        className="w-full rounded-xl bg-horizon-cyan/20 border border-horizon-cyan/40 py-2.5 text-sm font-medium text-cyan-200 hover:bg-horizon-cyan/30 hover:border-horizon-cyan hover:text-white transition-all shadow-[0_0_15px_rgba(0,155,185,0.25)] active:scale-95 mt-2"
      >
        Sign In
      </button>
    </form>
  );
}