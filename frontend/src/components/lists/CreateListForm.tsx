"use client";

import { useActionState } from "react";

import { createListAction, type ListActionState } from "@/lib/actions/lists";

const INITIAL_STATE: ListActionState = { status: "idle" };

export default function CreateListForm() {
  const [state, formAction, pending] = useActionState(createListAction, INITIAL_STATE);

  return (
    <form
      action={formAction}
      className="liquid-glass flex flex-col gap-3 rounded-2xl border border-white/10 p-4 sm:flex-row sm:items-center"
    >
      <input
        type="text"
        name="name"
        placeholder="New list name (e.g. Best Time-Travel Narratives)..."
        required
        maxLength={120}
        className="flex-1 rounded-xl border border-white/15 bg-slate-900/80 px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none"
      />
      <button
        type="submit"
        disabled={pending}
        className="rounded-xl border border-horizon-cyan/40 bg-horizon-cyan/20 px-4 py-2 text-xs font-semibold text-cyan-200 transition-all hover:bg-horizon-cyan/30 disabled:opacity-50"
      >
        {pending ? "Creating…" : "+ Create List"}
      </button>
      {state.status === "error" && (
        <span role="alert" className="text-xs text-rose-300">
          {state.message}
        </span>
      )}
    </form>
  );
}
