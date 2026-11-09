"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import AuthBanner from "@/components/auth/AuthBanner";
import { login } from "@/lib/services/auth";

interface LoginFormProps {
  registered?: boolean;
}

export default function LoginForm({ registered = false }: LoginFormProps) {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setPending(true);

    try {
      await login({ username, password });
      router.push("/");
      router.refresh();
    } catch (err: any) {
      setError(err?.message || "Sign in failed. Please check your credentials.");
    } finally {
      setPending(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {registered && (
        <AuthBanner variant="success">
          Your account was created. Please sign in.
        </AuthBanner>
      )}
      {error && <AuthBanner variant="error">{error}</AuthBanner>}

      <div className="space-y-1.5">
        <label className="block text-xs font-medium text-slate-300">
          Username or Email
        </label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          minLength={1}
          maxLength={100}
          className="w-full rounded-xl bg-black/50 border border-white/10 px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-horizon-cyan transition-colors"
          placeholder="Enter your username or email..."
        />
      </div>

      <div className="space-y-1.5">
        <div className="flex justify-between items-center">
          <label className="block text-xs font-medium text-slate-300">
            Password
          </label>
          <a href="#" className="text-[11px] text-horizon-cyan hover:underline">
            Forgot?
          </a>
        </div>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={1}
          maxLength={128}
          className="w-full rounded-xl bg-black/50 border border-white/10 px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-horizon-cyan transition-colors"
          placeholder="••••••••"
        />
      </div>

      <button
        type="submit"
        disabled={pending}
        className="w-full py-2.5 rounded-xl bg-horizon-crimson/30 hover:bg-horizon-crimson/50 border border-horizon-crimson/60 text-white font-medium text-xs transition-all shadow-[0_0_20px_rgba(229,29,36,0.3)] active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {pending ? "Signing in..." : "Sign In"}
      </button>
    </form>
  );
}