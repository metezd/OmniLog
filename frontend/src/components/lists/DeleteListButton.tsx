"use client";

import { useState } from "react";
import { deleteListAction } from "@/lib/actions/lists";

interface DeleteListButtonProps {
  listId: number;
  listName: string;
}

export default function DeleteListButton({ listId, listName }: DeleteListButtonProps) {
  const [confirming, setConfirming] = useState(false);

  if (!confirming) {
    return (
      <button
        type="button"
        onClick={() => setConfirming(true)}
        className="text-xs font-medium text-rose-300 hover:text-rose-200"
      >
        Delete
      </button>
    );
  }

  return (
    <form action={deleteListAction} className="flex items-center gap-2">
      <input type="hidden" name="listId" value={listId} />
      <span className="text-[11px] text-slate-300">Delete &quot;{listName}&quot;?</span>
      <button
        type="submit"
        className="rounded bg-rose-500/20 px-2 py-0.5 text-[11px] font-semibold text-rose-200 hover:bg-rose-500/30"
      >
        Yes
      </button>
      <button
        type="button"
        onClick={() => setConfirming(false)}
        className="text-[11px] text-slate-400 hover:text-white"
      >
        No
      </button>
    </form>
  );
}
