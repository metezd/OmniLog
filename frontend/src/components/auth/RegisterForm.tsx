"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

export default function RegisterForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    router.push("/login");
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-slate-300">Username</label>
        <input
          type="text"
          required
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="johndoe"
          className="w-full rounded-xl bg-black/40 border border-white/10 px-3.5 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-horizon-cyan focus:outline-none focus:ring-1 focus:ring-horizon-cyan transition-all"
        />
      </div>

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
        <label className="text-xs font-medium text-slate-300">Password</label>
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
        className="w-full rounded-xl bg-horizon-crimson/20 border border-horizon-crimson/40 py-2.5 text-sm font-medium text-rose-200 hover:bg-horizon-crimson/30 hover:border-horizon-crimson hover:text-white transition-all shadow-[0_0_15px_rgba(229,29,36,0.25)] active:scale-95 mt-2"
      >
        Create Account
      </button>
    </form>
  );
}