"use client";

import { RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { useTransition } from "react";

interface RetryButtonProps {
  /**
   * What to do on a click. Without it the page is loaded again from the server, which is what a
   * Server Component needs. An error boundary (error.tsx) passes the retry() that Next.js gives.
   */
  onRetry?: () => void;
}

export default function RetryButton({ onRetry }: RetryButtonProps) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  const handleClick = () => {
    if (onRetry) {
      onRetry();
      return;
    }
    startTransition(() => router.refresh());
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={pending}
      className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-slate-200 transition-all hover:border-cyan-400/40 hover:bg-cyan-500/20 hover:text-cyan-200 active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
    >
      <RefreshCw className={`h-3.5 w-3.5 ${pending ? "animate-spin" : ""}`} aria-hidden="true" />
      {pending ? "Trying again..." : "Try again"}
    </button>
  );
}
