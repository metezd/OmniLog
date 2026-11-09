import { CloudOff, SearchX, TriangleAlert } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import type { ErrorKind } from "@/types/state";
import RetryButton from "./RetryButton";
import StateCard from "./StateCard";

interface ErrorStateProps {
  kind: ErrorKind;
  /** Shown under the title. Take it from toErrorState() or write one. */
  message?: string;
  /** Replaces the default title of the kind. */
  title?: string;
  /** Replaces the default button: a retry button, or for not_found a link to the library. */
  action?: ReactNode;
}

const DEFAULTS: Record<ErrorKind, { title: string; icon: ReactNode }> = {
  unavailable: { title: "Service unavailable", icon: <CloudOff className="h-6 w-6" aria-hidden="true" /> },
  not_found: { title: "Not found", icon: <SearchX className="h-6 w-6" aria-hidden="true" /> },
  error: { title: "Something went wrong", icon: <TriangleAlert className="h-6 w-6" aria-hidden="true" /> },
};

/** The error state of a screen (S-15): a 503 or a network failure, a 404, or anything else. */
export default function ErrorState({ kind, message, title, action }: ErrorStateProps) {
  const defaults = DEFAULTS[kind];
  const defaultAction =
    kind === "not_found" ? (
      <Link
        href="/library"
        className="inline-flex rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-slate-200 transition-all hover:border-cyan-400/40 hover:bg-cyan-500/20 hover:text-cyan-200"
      >
        Go to library
      </Link>
    ) : (
      <RetryButton />
    );

  return (
    <StateCard
      role="alert"
      icon={defaults.icon}
      title={title ?? defaults.title}
      message={message}
      action={action ?? defaultAction}
    />
  );
}
