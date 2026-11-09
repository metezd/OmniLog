import type { Metadata } from "next";

import LibraryEntryCard from "@/components/library/LibraryEntryCard";
import EmptyState from "@/components/states/EmptyState";
import ErrorState from "@/components/states/ErrorState";
import { toErrorState } from "@/lib/server/error-state";
import { getLibrary } from "@/lib/server/library";
import type { LibraryEntry } from "@/types/api";

export const metadata: Metadata = {
  title: "Library | OmniLog",
};

// S-04. The data and the states are in place. Filters and editing of status and rating come with
// the next step of the screen.
export default async function LibraryPage() {
  let entries: LibraryEntry[];
  try {
    entries = await getLibrary();
  } catch (error) {
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
        <EmptyState title="Your library is empty" message="Titles that you add will show up here." />
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {entries.map((entry) => (
            <LibraryEntryCard key={entry.id} entry={entry} />
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
        <h1 className="text-xl font-bold tracking-tight text-white">Library</h1>
        <p className="text-xs text-slate-400">Your games and series with their status and rating</p>
      </div>
      {children}
    </div>
  );
}
