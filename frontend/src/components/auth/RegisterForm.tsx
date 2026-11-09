"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import AuthBanner from "@/components/auth/AuthBanner";
import { register } from "@/lib/services/auth";

export default function RegisterForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    if (username.includes("@")) {
      setError("Username must not contain '@' symbol.");
      return;
    }

    setPending(true);

    try {
      await register({ username, email, password });
      router.push("/login?registered=true");
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Registration failed. Please try again.";
      setError(message);
    } finally {
      setPending(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <AuthBanner variant="error">{error}</AuthBanner>}

      <div className="space-y-1.5">
        <label className="block text-xs font-medium text-slate-300">
          Username
        </label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          minLength={3}
          maxLength={50}
          className="w-full rounded-xl bg-black/50 border border-white/10 px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-horizon-cyan transition-colors"
          placeholder="Choose a username (min 3 chars, no @)..."
        />
      </div>

      <div className="space-y-1.5">
        <label className="block text-xs font-medium text-slate-300">
          Email
        </label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          maxLength={100}
          className="w-full rounded-xl bg-black/50 border border-white/10 px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-horizon-cyan transition-colors"
          placeholder="you@example.com"
        />
      </div>

      <div className="space-y-1.5">
        <label className="block text-xs font-medium text-slate-300">
          Password
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          className="w-full rounded-xl bg-black/50 border border-white/10 px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-horizon-cyan transition-colors"
          placeholder="At least 8 characters..."
        />
      </div>

      <button
        type="submit"
        disabled={pending}
        className="w-full py-2.5 rounded-xl bg-horizon-crimson/30 hover:bg-horizon-crimson/50 border border-horizon-crimson/60 text-white font-medium text-xs transition-all shadow-[0_0_20px_rgba(229,29,36,0.3)] active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {pending ? "Creating account..." : "Create Account"}
      </button>
    </form>
  );
}