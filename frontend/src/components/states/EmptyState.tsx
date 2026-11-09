import { Inbox } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import StateCard from "./StateCard";

interface EmptyStateProps {
  title: string;
  message?: string;
  /** An optional link under the message, for example to the catalog search. */
  action?: { href: string; label: string };
  icon?: ReactNode;
}

/** A screen that works but has nothing to show yet (S-15). */
export default function EmptyState({ title, message, action, icon }: EmptyStateProps) {
  return (
    <StateCard
      role="status"
      icon={icon ?? <Inbox className="h-6 w-6" aria-hidden="true" />}
      title={title}
      message={message}
      action={
        action && (
          <Link
            href={action.href}
            className="inline-flex rounded-xl border border-horizon-crimson/40 bg-horizon-crimson/20 px-4 py-2 text-xs font-medium text-rose-200 transition-all hover:border-horizon-crimson hover:bg-horizon-crimson/30 hover:text-white"
          >
            {action.label}
          </Link>
        )
      }
    />
  );
}
