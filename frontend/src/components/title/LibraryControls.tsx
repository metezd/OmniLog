"use client";

import { useActionState } from "react";

import {
  type ActionState,
  removeLibraryEntryAction,
  updateLibraryEntryAction,
} from "@/lib/actions/library";
import { STATUS_LABELS } from "@/lib/media";
import type { LibraryEntry, WatchStatus } from "@/types/api";

interface LibraryControlsProps {
  entry: LibraryEntry;
}

const INITIAL_STATE: ActionState = { status: "idle" };
const STATUS_OPTIONS: WatchStatus[] = ["IN_PROGRESS", "COMPLETED", "PLAN_TO_WATCH", "DROPPED"];
const RATING_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

export default function LibraryControls({ entry }: LibraryControlsProps) {
  const [state, formAction, pending] = useActionState(updateLibraryEntryAction, INITIAL_STATE);

  return (
    <div className="liquid-glass space-y-4 rounded-2xl border border-white/10 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-white">Your Library Status</h2>
          <p className="text-xs text-slate-400">
            Update watch status or rate this title from 1 to 10
          </p>
        </div>
        <form action={removeLibraryEntryAction}>
          <input type="hidden" name="entryId" value={entry.id} />
          <input type="hidden" name="mediaItemId" value={entry.media_item_id} />
          <button
            type="submit"
            className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-xs font-medium text-rose-300 transition-all hover:bg-rose-500/20"
          >
            Remove from Library
          </button>
        </form>
      </div>

      <form action={formAction} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <input type="hidden" name="entryId" value={entry.id} />
        <input type="hidden" name="mediaItemId" value={entry.media_item_id} />

        <label className="space-y-1 text-xs text-slate-300">
          <span className="font-medium">Status</span>
          <select
            name="status"
            defaultValue={entry.status}
            className="w-full rounded-xl border border-white/15 bg-slate-900/90 px-3 py-2 text-xs text-white focus:outline-none"
          >
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {STATUS_LABELS[status]}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-1 text-xs text-slate-300">
          <span className="font-medium">Overall Rating (1–10)</span>
          <select
            name="rating"
            defaultValue={entry.rating ?? ""}
            className="w-full rounded-xl border border-white/15 bg-slate-900/90 px-3 py-2 text-xs text-white focus:outline-none"
          >
            <option value="">Not rated</option>
            {RATING_OPTIONS.map((value) => (
              <option key={value} value={value}>
                ★ {value} / 10
              </option>
            ))}
          </select>
        </label>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={pending}
            className="w-full rounded-xl border border-horizon-cyan/40 bg-horizon-cyan/20 px-4 py-2 text-xs font-semibold text-cyan-200 transition-all hover:bg-horizon-cyan/30 disabled:opacity-50"
          >
            {pending ? "Saving…" : "Save Changes"}
          </button>
        </div>
      </form>

      {state.status === "saved" && (
        <p className="text-xs text-emerald-300">✓ {state.message}</p>
      )}
      {state.status === "error" && (
        <p role="alert" className="text-xs text-rose-300">
          {state.message}
        </p>
      )}
    </div>
  );
}
