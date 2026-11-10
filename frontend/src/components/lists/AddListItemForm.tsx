"use client";

import { useActionState } from "react";

import { addItemToListAction, type ListActionState } from "@/lib/actions/lists";
import type { LibraryEntry } from "@/types/api";

interface AddListItemFormProps {
  listId: number;
  library: LibraryEntry[];
}

const INITIAL_STATE: ListActionState = { status: "idle" };

export default function AddListItemForm({ listId, library }: AddListItemFormProps) {
  const [state, formAction, pending] = useActionState(addItemToListAction, INITIAL_STATE);

  if (library.length === 0) {
    return (
      <div className="liquid-glass rounded-2xl border border-white/10 p-4 text-xs text-slate-400">
        Add titles to your library first so you can organize them into custom lists.
      </div>
    );
  }

  return (
    <form
      action={formAction}
      className="liquid-glass flex flex-col gap-3 rounded-2xl border border-white/10 p-4 sm:flex-row sm:items-center"
    >
      <input type="hidden" name="listId" value={listId} />
      <select
        name="mediaItemId"
        required
        className="flex-1 rounded-xl border border-white/15 bg-slate-900/90 px-3.5 py-2 text-xs text-white focus:outline-none"
      >
        <option value="">Select a title from your library…</option>
        {library.map((entry) => (
          <option key={entry.media_item_id} value={entry.media_item_id}>
            {entry.media_item.title} ({entry.media_item.media_type})
          </option>
        ))}
      </select>
      <button
        type="submit"
        disabled={pending}
        className="rounded-xl border border-horizon-cyan/40 bg-horizon-cyan/20 px-4 py-2 text-xs font-semibold text-cyan-200 transition-all hover:bg-horizon-cyan/30 disabled:opacity-50"
      >
        {pending ? "Adding…" : "+ Add Title"}
      </button>
      {state.status === "error" && (
        <span role="alert" className="text-xs text-rose-300">
          {state.message}
        </span>
      )}
    </form>
  );
}
