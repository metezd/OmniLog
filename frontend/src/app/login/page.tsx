import type { Metadata } from "next";
import Link from "next/link";

import AuthBanner from "@/components/auth/AuthBanner";
import GoogleSignInButton from "@/components/auth/GoogleSignInButton";
import LoginForm from "@/components/auth/LoginForm";

export const metadata: Metadata = {
  title: "Sign In | OmniLog",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ registered?: string; expired?: string }>;
}) {
  const { registered, expired } = await searchParams;

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

        {expired === "1" && (
          <AuthBanner variant="info">Your session has ended. Please sign in again.</AuthBanner>
        )}

        <GoogleSignInButton />

        <div className="flex items-center gap-3 my-2">
          <div className="flex-1 h-px bg-white/10" />
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">
            or sign in with email
          </span>
          <div className="flex-1 h-px bg-white/10" />
        </div>

        <LoginForm registered={registered === "1"} />

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
