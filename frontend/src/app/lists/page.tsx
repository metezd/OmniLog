import type { Metadata } from "next";
import Link from "next/link";

import CreateListForm from "@/components/lists/CreateListForm";
import DeleteListButton from "@/components/lists/DeleteListButton";
import EmptyState from "@/components/states/EmptyState";
import ErrorState from "@/components/states/ErrorState";
import { toErrorState } from "@/lib/server/error-state";
import { getLists } from "@/lib/server/journal";
import type { CustomList } from "@/types/api";

export const metadata: Metadata = {
  title: "Custom Lists | OmniLog",
};

export default async function ListsPage() {
  let lists: CustomList[];
  try {
    lists = await getLists();
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
      <CreateListForm />

      {lists.length === 0 ? (
        <EmptyState
          title="No custom lists yet"
          message="Create a list above to group your favorite games and series by theme."
        />
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {lists.map((list) => (
            <article
              key={list.id}
              className="liquid-glass liquid-glass-card flex flex-col justify-between gap-4 rounded-2xl border border-white/10 p-5"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <Link
                    href={`/lists/${list.id}`}
                    className="text-base font-bold text-white transition-colors hover:text-cyan-300"
                  >
                    {list.name}
                  </Link>
                  <span className="rounded-full border border-white/15 bg-white/5 px-2.5 py-0.5 text-[11px] font-medium text-slate-300">
                    {list.items.length} {list.items.length === 1 ? "title" : "titles"}
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  Click to view or manage titles in this collection
                </p>
              </div>

              <div className="flex items-center justify-between border-t border-white/10 pt-3">
                <Link
                  href={`/lists/${list.id}`}
                  className="text-xs font-medium text-cyan-300 hover:underline"
                >
                  Open List →
                </Link>
                <DeleteListButton listId={list.id} listName={list.name} />
              </div>
            </article>
          ))}
        </div>
      )}
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative z-10 mx-auto w-full max-w-7xl space-y-6 px-4 py-8 sm:px-8">
      <div className="border-b border-white/10 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-white">Custom Lists</h1>
        <p className="text-xs text-slate-400">
          Curate cross-media collections of video games, TV series, and movies
        </p>
      </div>
      {children}
    </div>
  );
}


