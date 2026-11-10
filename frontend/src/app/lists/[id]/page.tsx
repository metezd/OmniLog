import type { Metadata } from "next";
import Link from "next/link";

import AddListItemForm from "@/components/lists/AddListItemForm";
import EmptyState from "@/components/states/EmptyState";
import ErrorState from "@/components/states/ErrorState";
import { removeItemFromListAction } from "@/lib/actions/lists";
import {
  MEDIA_TYPE_BADGE_CLASSES,
  MEDIA_TYPE_CARD_CLASSES,
  MEDIA_TYPE_LABELS,
  MEDIA_TYPE_TITLE_CLASSES,
} from "@/lib/media";
import { toErrorState } from "@/lib/server/error-state";
import { getList } from "@/lib/server/journal";
import { getLibrary } from "@/lib/server/library";
import type { CustomList, LibraryEntry } from "@/types/api";

export const metadata: Metadata = {
  title: "List Details | OmniLog",
};

interface ListDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function ListDetailPage({ params }: ListDetailPageProps) {
  const { id } = await params;
  const listId = Number(id);

  if (!Number.isInteger(listId) || listId <= 0) {
    return (
      <div className="relative z-10 mx-auto w-full max-w-7xl px-4 py-8 sm:px-8">
        <ErrorState kind="not_found" message="This list does not exist." />
      </div>
    );
  }

  let list: CustomList;
  let library: LibraryEntry[] = [];

  try {
    const [fetchedList, fetchedLib] = await Promise.all([
      getList(listId),
      getLibrary().catch(() => []),
    ]);
    list = fetchedList;
    library = fetchedLib;
  } catch (error) {
    const digest = (error as { digest?: unknown } | null)?.digest;
    if (typeof digest === "string" && digest.startsWith("NEXT_REDIRECT")) throw error;
    const state = toErrorState(error);
    return (
      <div className="relative z-10 mx-auto w-full max-w-7xl px-4 py-8 sm:px-8">
        <ErrorState kind={state.kind} message={state.message} />
      </div>
    );
  }

  const mediaById = new Map(library.map((entry) => [entry.media_item_id, entry.media_item]));

  return (
    <div className="relative z-10 mx-auto w-full max-w-7xl space-y-6 px-4 py-8 sm:px-8">
      <div>
        <Link
          href="/lists"
          className="text-xs font-medium text-slate-400 transition-colors hover:text-white"
        >
          ← Back to Custom Lists
        </Link>
      </div>

      <div className="border-b border-white/10 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-white">{list.name}</h1>
        <p className="text-xs text-slate-400">
          {list.items.length} {list.items.length === 1 ? "title" : "titles"} in this custom list
        </p>
      </div>

      <AddListItemForm listId={list.id} library={library} />

      {list.items.length === 0 ? (
        <EmptyState
          title="This list is empty"
          message="Select a title from your library above to add it to this collection."
        />
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {list.items.map((item) => {
            const media = mediaById.get(item.media_item_id);
            return (
              <article
                key={item.id}
                className={`liquid-glass liquid-glass-card ${media ? MEDIA_TYPE_CARD_CLASSES[media.media_type] : ""} flex flex-col justify-between rounded-2xl border border-white/10 p-5`}
              >
                <div className="space-y-2">
                  {media && (
                    <span
                      className={`inline-block rounded-full border px-2.5 py-0.5 text-[10px] font-semibold ${MEDIA_TYPE_BADGE_CLASSES[media.media_type]}`}
                    >
                      {MEDIA_TYPE_LABELS[media.media_type]}
                    </span>
                  )}
                  <h3 className="font-bold tracking-tight text-white">
                    <Link
                      href={`/title/${item.media_item_id}`}
                      className={
                        media
                          ? MEDIA_TYPE_TITLE_CLASSES[media.media_type]
                          : "transition-colors hover:text-cyan-300"
                      }
                    >
                      {media?.title ?? `Title #${item.media_item_id}`}
                    </Link>
                  </h3>
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-white/10 pt-3">
                  <Link
                    href={`/title/${item.media_item_id}`}
                    className="text-xs text-slate-300 hover:text-white"
                  >
                    Details →
                  </Link>
                  <form action={removeItemFromListAction}>
                    <input type="hidden" name="listId" value={list.id} />
                    <input type="hidden" name="mediaItemId" value={item.media_item_id} />
                    <button
                      type="submit"
                      className="text-xs font-medium text-rose-300 hover:text-rose-200"
                    >
                      Remove
                    </button>
                  </form>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
