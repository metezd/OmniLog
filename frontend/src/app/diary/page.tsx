import type { Metadata } from "next";
import Link from "next/link";

import EmptyState from "@/components/states/EmptyState";
import ErrorState from "@/components/states/ErrorState";
import { toErrorState } from "@/lib/server/error-state";
import { getDiary } from "@/lib/server/journal";
import { getLibrary } from "@/lib/server/library";
import type { DiaryEntry } from "@/types/api";

export const metadata: Metadata = {
  title: "Activity Diary | OmniLog",
};

const ACTION_LABELS: Record<string, { label: string; badgeClass: string }> = {
  LIBRARY_ADDED: {
    label: "Added to Library",
    badgeClass: "border-cyan-400/40 bg-cyan-400/15 text-cyan-200",
  },
  STATUS_CHANGED: {
    label: "Status Updated",
    badgeClass: "border-blue-400/40 bg-blue-400/15 text-blue-200",
  },
  RATED: {
    label: "Rated Title",
    badgeClass: "border-amber-400/40 bg-amber-400/15 text-amber-200",
  },
  CHAPTER_RATED: {
    label: "Rated Chapter",
    badgeClass: "border-amber-400/40 bg-amber-400/15 text-amber-200",
  },
  PLAYTIME_LOGGED: {
    label: "Logged Playtime",
    badgeClass: "border-purple-400/40 bg-purple-400/15 text-purple-200",
  },
  DECISION_RECORDED: {
    label: "Narrative Choice",
    badgeClass: "border-fuchsia-400/40 bg-fuchsia-400/15 text-fuchsia-200",
  },
  REVIEW_POSTED: {
    label: "Posted Review",
    badgeClass: "border-emerald-400/40 bg-emerald-400/15 text-emerald-200",
  },
  LIST_CREATED: {
    label: "Created List",
    badgeClass: "border-indigo-400/40 bg-indigo-400/15 text-indigo-200",
  },
  LIST_ITEM_ADDED: {
    label: "Added to List",
    badgeClass: "border-indigo-400/40 bg-indigo-400/15 text-indigo-200",
  },
  LIBRARY_REMOVED: {
    label: "Removed from Library",
    badgeClass: "border-rose-400/40 bg-rose-400/15 text-rose-200",
  },
};

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function summarizePayload(payload: Record<string, unknown> | null): string {
  if (!payload) return "";
  const parts: string[] = [];
  if (typeof payload.status === "string") parts.push(`Status: ${payload.status}`);
  if (typeof payload.rating === "number") parts.push(`Rating: ★ ${payload.rating}`);
  if (typeof payload.minutes === "number") parts.push(`+${payload.minutes} min`);
  if (typeof payload.choice === "string") parts.push(`Choice: "${payload.choice}"`);
  if (typeof payload.contains_spoiler === "boolean") {
    parts.push(payload.contains_spoiler ? "Spoiler Flagged" : "Spoiler-Free");
  }
  if (typeof payload.name === "string") parts.push(`"${payload.name}"`);
  return parts.join(" • ");
}

export default async function DiaryPage() {
  let entries: DiaryEntry[] = [];
  const titleByMediaId = new Map<number, string>();

  try {
    const [diary, library] = await Promise.all([
      getDiary(),
      getLibrary().catch(() => []),
    ]);
    entries = diary;
    library.forEach((entry) => {
      titleByMediaId.set(entry.media_item_id, entry.media_item.title);
    });
  } catch (error) {
    const digest = (error as { digest?: unknown } | null)?.digest;
    if (typeof digest === "string" && digest.startsWith("NEXT_REDIRECT")) throw error;
    const state = toErrorState(error);
    return (
      <Shell>
        <ErrorState kind={state.kind} message={state.message} />
      </Shell>
    );
  }

  return (
    <Shell>
      {entries.length === 0 ? (
        <EmptyState
          title="Your activity diary is empty"
          message="Every library addition, chapter rating, logged playtime, and narrative decision will be recorded here chronologically."
        />
      ) : (
        <div className="space-y-3">
          {entries.map((entry) => {
            const meta = ACTION_LABELS[entry.action] ?? {
              label: entry.action,
              badgeClass: "border-white/20 bg-white/10 text-slate-200",
            };
            const mediaTitle =
              entry.media_item_id !== null
                ? titleByMediaId.get(entry.media_item_id) ?? `Title #${entry.media_item_id}`
                : null;
            const summary = summarizePayload(entry.payload);

            return (
              <div
                key={entry.id}
                className="liquid-glass flex flex-col justify-between gap-2 rounded-2xl border border-white/10 p-4 sm:flex-row sm:items-center"
              >
                <div className="flex flex-wrap items-center gap-3">
                  <span
                    className={`rounded-full border px-3 py-0.5 text-[11px] font-semibold ${meta.badgeClass}`}
                  >
                    {meta.label}
                  </span>

                  {entry.media_item_id !== null && mediaTitle && (
                    <Link
                      href={`/title/${entry.media_item_id}`}
                      className="text-sm font-bold text-white transition-colors hover:text-cyan-300"
                    >
                      {mediaTitle}
                    </Link>
                  )}

                  {summary && <span className="text-xs text-slate-300">{summary}</span>}
                </div>

                <time className="text-xs text-slate-400" dateTime={entry.created_at}>
                  {formatTimestamp(entry.created_at)}
                </time>
              </div>
            );
          })}
        </div>
      )}
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative z-10 mx-auto w-full max-w-7xl space-y-6 px-4 py-8 sm:px-8">
      <div className="border-b border-white/10 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-white">Activity Diary</h1>
        <p className="text-xs text-slate-400">
          Chronological journal of your ratings, episodic playtime logs, and narrative choices
        </p>
      </div>
      {children}
    </div>
  );
}
