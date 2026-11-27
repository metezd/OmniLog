"use client";

import { useActionState } from "react";

import { type ActionState, logTitlePlaytimeAction } from "@/lib/actions/library";
import { formatPlaytime } from "@/lib/media";
import type { LibraryEntry } from "@/types/api";

interface TitlePlaytimeCardProps {
  entry: LibraryEntry;
  /** Minutes logged on the chapters of the title. They count in the total, but are logged there. */
  chapterMinutes?: number;
  /** "Playtime" for a game, "Watch time" for a movie. */
  label?: string;
}

const INITIAL_STATE: ActionState = { status: "idle" };

/** Playtime of a whole game or movie, logged without a chapter (US-11, #413). */
export default function TitlePlaytimeCard({
  entry,
  chapterMinutes = 0,
  label = "Playtime",
}: TitlePlaytimeCardProps) {
  const [state, formAction, pending] = useActionState(logTitlePlaytimeAction, INITIAL_STATE);
  const totalMinutes = entry.playtime_minutes + chapterMinutes;

  return (
    <div className="liquid-glass space-y-4 rounded-2xl border border-white/10 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-white">{label} Logging</h2>
          <p className="text-xs text-slate-400">
            Log a session in hours and minutes. Every session adds to the total.
          </p>
        </div>
        <span
          data-testid="title-playtime-total"
          className="rounded-lg border border-purple-400/30 bg-purple-400/10 px-2.5 py-1 text-xs font-medium text-purple-200"
        >
          {formatPlaytime(totalMinutes)} logged
        </span>
      </div>

      {chapterMinutes > 0 && (
        <p className="text-[11px] text-slate-400">
          Includes {formatPlaytime(chapterMinutes)} logged on chapters.
        </p>
      )}

      <form action={formAction} className="space-y-2 border-t border-white/10 pt-4">
        <input type="hidden" name="entryId" value={entry.id} />
        <input type="hidden" name="mediaItemId" value={entry.media_item_id} />
        <div className="flex flex-wrap items-end gap-2">
          <div className="space-y-1">
            <label htmlFor={`title-hours-${entry.id}`} className="block text-xs font-medium text-slate-300">
              Hours
            </label>
            <input
              id={`title-hours-${entry.id}`}
              type="number"
              name="hours"
              min={0}
              max={1666}
              step={1}
              placeholder="e.g. 1"
              className="w-24 rounded-lg border border-white/15 bg-slate-900/80 px-2.5 py-1 text-xs text-white focus:outline-none"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor={`title-minutes-${entry.id}`} className="block text-xs font-medium text-slate-300">
              Minutes
            </label>
            <input
              id={`title-minutes-${entry.id}`}
              type="number"
              name="minutes"
              min={0}
              max={100000}
              step={1}
              placeholder="e.g. 60"
              className="w-24 rounded-lg border border-white/15 bg-slate-900/80 px-2.5 py-1 text-xs text-white focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={pending}
            className="rounded-lg border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-slate-200 hover:bg-white/20 disabled:opacity-50"
          >
            {pending ? "Logging…" : "+ Log Time"}
          </button>
        </div>
        {state.status === "saved" && (
          <p className="text-[11px] text-emerald-300">{state.message}</p>
        )}
        {state.status === "error" && (
          <p className="text-[11px] text-rose-300">{state.message}</p>
        )}
      </form>
    </div>
  );
}
