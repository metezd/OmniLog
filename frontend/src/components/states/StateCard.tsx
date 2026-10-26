import type { ReactNode } from "react";

interface StateCardProps {
  role: "status" | "alert";
  icon: ReactNode;
  title: string;
  message?: string;
  /** Buttons or links under the message. */
  action?: ReactNode;
}

/** The frame that the empty, error and loading states share. */
export default function StateCard({ role, icon, title, message, action }: StateCardProps) {
  return (
    <section
      role={role}
      className="liquid-glass mx-auto flex w-full max-w-xl flex-col items-center gap-3 rounded-3xl border border-white/10 p-8 text-center sm:p-12"
    >
      <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-300">{icon}</div>
      <h2 className="text-lg font-bold tracking-tight text-white">{title}</h2>
      {message && <p className="max-w-sm text-xs leading-relaxed text-slate-400">{message}</p>}
      {action && <div className="pt-2">{action}</div>}
    </section>
  );
}
