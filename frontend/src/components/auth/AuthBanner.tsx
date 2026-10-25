import type { ReactNode } from "react";

interface AuthBannerProps {
  variant: "error" | "success";
  children: ReactNode;
}

/** A message for the whole form. An error is announced at once, a success note is polite. */
export default function AuthBanner({ variant, children }: AuthBannerProps) {
  const isError = variant === "error";
  return (
    <div
      role={isError ? "alert" : "status"}
      className={
        isError
          ? "bg-rose-500/10 border border-rose-500/30 p-3 rounded-xl text-xs text-rose-300 text-center"
          : "bg-emerald-500/10 border border-emerald-500/30 p-3 rounded-xl text-xs text-emerald-300 text-center"
      }
    >
      {children}
    </div>
  );
}
