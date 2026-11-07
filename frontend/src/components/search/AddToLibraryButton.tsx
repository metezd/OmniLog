"use client";

import { useActionState } from "react";

import { addToLibraryAction, type AddToLibraryState } from "@/lib/actions/library";

interface AddToLibraryButtonProps {
  mediaItemId: number;
}

const INITIAL_STATE: AddToLibraryState = { status: "idle" };

export default function AddToLibraryButton({ mediaItemId }: AddToLibraryButtonProps) {
  const [state, formAction, isPending] = useActionState(addToLibraryAction, INITIAL_STATE);

  if (state.status === "added") {
    return (
      <div className="w-full rounded-lg border border-emerald-500/20 bg-emerald-500/10 py-1.5 text-center text-xs font-medium text-emerald-300">
        ✓ Added to library
      </div>
    );
  }

  return (
    <form action={formAction} className="space-y-1.5">
      <input type="hidden" name="mediaItemId" value={mediaItemId} />
      <button
        type="submit"
        disabled={isPending}
        className="w-full rounded-lg border border-white/10 bg-white/5 py-1.5 text-xs font-medium text-slate-200 transition-all hover:border-blue-400/40 hover:bg-blue-500/20 hover:text-blue-200 active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isPending ? "Adding..." : "+ Add to Library"}
      </button>
      {state.status === "error" && (
        <p role="alert" className="text-[11px] text-rose-400">
          {state.message}
        </p>
      )}
    </form>
  );
}