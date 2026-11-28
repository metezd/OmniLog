import type { Metadata } from "next";
import Link from "next/link";

import LocalTime from "@/components/common/LocalTime";
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

/** Events per page of the diary. The backend allows up to 500. */
const DIARY_PAGE_SIZE = 100;

type DiaryPageProps = { searchParams?: Promise<{ page?: string | string[] }> };

/** The page number from the address, 1 when it is missing or not a whole number from 1 up. */
function pageNumber(value: string | string[] | undefined): number {
  const text = Array.isArray(value) ? value[0] : value;
  const page = Number(text);
  return Number.isInteger(page) && page >= 1 && page <= 100_000 ? page : 1;
}

export default async function DiaryPage({ searchParams }: DiaryPageProps) {
  const params = searchParams ? await searchParams : {};
  const page = pageNumber(params.page);
  let entries: DiaryEntry[] = [];
  let hasOlder = false;
  const titleByMediaId = new Map<number, string>();

  try {
    // One event more than the page shows tells whether an older page exists (#418)
    const [diary, library] = await Promise.all([
      getDiary({ limit: DIARY_PAGE_SIZE + 1, offset: (page - 1) * DIARY_PAGE_SIZE }),
      getLibrary().catch(() => []),
    ]);
    hasOlder = diary.length > DIARY_PAGE_SIZE;
    entries = diary.slice(0, DIARY_PAGE_SIZE);
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
      {entries.length === 0 && page === 1 ? (
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
            const summary = entry.details;

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

                <LocalTime className="text-xs text-slate-400" iso={entry.created_at} />
              </div>
            );
          })}
          <DiaryPager page={page} hasOlder={hasOlder} />
        </div>
      )}
    </Shell>
  );
}

function DiaryPager({ page, hasOlder }: { page: number; hasOlder: boolean }) {
  if (page === 1 && !hasOlder) return null;
  const linkClass =
    "rounded-full border border-white/15 px-4 py-1.5 text-xs font-semibold text-slate-200 transition-colors hover:border-cyan-300/60 hover:text-cyan-200";
  return (
    <nav aria-label="Diary pages" className="flex items-center justify-between pt-2">
      {page > 1 ? (
        <Link href={page === 2 ? "/diary" : `/diary?page=${page - 1}`} className={linkClass}>
          Newer events
        </Link>
      ) : (
        <span />
      )}
      <span className="text-xs text-slate-400">Page {page}</span>
      {hasOlder ? (
        <Link href={`/diary?page=${page + 1}`} className={linkClass}>
          Older events
        </Link>
      ) : (
        <span />
      )}
    </nav>
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
