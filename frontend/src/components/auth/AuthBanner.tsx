import type { ReactNode } from "react";

interface AuthBannerProps {
  variant: "error" | "success" | "info";
  children: ReactNode;
}

const STYLES = {
  error: "bg-rose-500/10 border border-rose-500/30 p-3 rounded-xl text-xs text-rose-300 text-center",
  success: "bg-emerald-500/10 border border-emerald-500/30 p-3 rounded-xl text-xs text-emerald-300 text-center",
  info: "bg-sky-500/10 border border-sky-500/30 p-3 rounded-xl text-xs text-sky-300 text-center",
} as const;

/** A message for the whole form. An error is announced at once, a success or info note is polite. */
export default function AuthBanner({ variant, children }: AuthBannerProps) {
  return (
    <div role={variant === "error" ? "alert" : "status"} className={STYLES[variant]}>
      {children}
    </div>
  );
}
