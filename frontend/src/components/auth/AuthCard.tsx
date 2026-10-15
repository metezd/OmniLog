import React from "react";

interface AuthCardProps {
  title: string;
  description: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export default function AuthCard({
  title,
  description,
  children,
  footer,
}: AuthCardProps) {
  return (
    <div className="flex min-h-[calc(100vh-10rem)] items-center justify-center px-4 py-12">
      <div className="liquid-glass w-full max-w-md rounded-3xl p-8 border border-white/10 shadow-2xl backdrop-blur-xl relative overflow-hidden">
        {/* Subtle Background Glow */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-horizon-cyan/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-horizon-crimson/20 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-6">
          <div className="space-y-2 text-center">
            <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
              {title}
            </h1>
            <p className="text-xs text-slate-400">{description}</p>
          </div>

          {children}

          {footer && (
            <div className="border-t border-white/10 pt-4 text-center text-xs text-slate-400">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}