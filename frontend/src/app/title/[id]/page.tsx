import type { Metadata } from "next";
import Link from "next/link";

import AddToLibraryButton from "@/components/search/AddToLibraryButton";
import ErrorState from "@/components/states/ErrorState";
import ChapterProgressCard from "@/components/title/ChapterProgressCard";
import LibraryControls from "@/components/title/LibraryControls";
import ReviewSection from "@/components/title/ReviewSection";
import { MEDIA_TYPE_LABELS, releaseYear } from "@/lib/media";
import { getTitleDetails } from "@/lib/server/catalog";
import { getChapterProgress } from "@/lib/server/chapters";
import { toErrorState } from "@/lib/server/error-state";
import { getLibrary } from "@/lib/server/library";
import { getReview } from "@/lib/server/reviews";
import type { Chapter, ChapterProgress, LibraryEntry, MediaDetail, Review } from "@/types/api";

export const metadata: Metadata = {
  title: "Title Details | OmniLog",
};

interface TitlePageProps {
  params: Promise<{ id: string }>;
}

function collectChapters(detail: MediaDetail): Chapter[] {
  if (detail.seasons.length > 0) {
    return detail.seasons.flatMap((season) => season.episodes);
  }
  return detail.chapters;
}

export default async function TitleDetailPage({ params }: TitlePageProps) {
  const { id } = await params;
  const mediaId = Number(id);

  if (!Number.isInteger(mediaId) || mediaId <= 0) {
    return (
      <div className="relative z-10 mx-auto w-full max-w-7xl px-4 py-8 sm:px-8">
        <ErrorState kind="not_found" message="This catalog title does not exist." />
      </div>
    );
  }

  let detail: MediaDetail;
  let libraryEntry: LibraryEntry | undefined;
  let review: Review | null = null;
  const progressMap = new Map<number, ChapterProgress>();

  try {
    const [fetchedDetail, library] = await Promise.all([
      getTitleDetails(mediaId),
      getLibrary().catch(() => []),
    ]);
    detail = fetchedDetail;
    libraryEntry = library.find((entry) => entry.media_item_id === mediaId);

    if (libraryEntry) {
      const allChapters = collectChapters(detail);
      const [fetchedReview, ...progressList] = await Promise.all([
        getReview(libraryEntry.id),
        ...allChapters.map((ch) =>
          getChapterProgress(libraryEntry!.id, ch.id).catch(() => null),
        ),
      ]);
      review = fetchedReview;
      progressList.forEach((prog) => {
        if (prog) progressMap.set(prog.chapter_id, prog);
      });
    }
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

  const year = releaseYear(detail.release_date);

  return (
    <div className="relative z-10 mx-auto w-full max-w-7xl space-y-8 px-4 py-8 sm:px-8">
      <div>
        <Link
          href="/library"
          className="text-xs font-medium text-slate-400 transition-colors hover:text-white"
        >
          ← Back to Library
        </Link>
      </div>

      {/* Hero Header */}
      <div className="liquid-glass grid grid-cols-1 gap-6 rounded-3xl border border-white/10 p-6 md:grid-cols-[220px_1fr]">
        <div className="relative h-72 w-full overflow-hidden rounded-2xl bg-black/40 md:h-80">
          {detail.poster_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={detail.poster_url}
              alt={`Poster of ${detail.title}`}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-xs text-slate-500">
              No poster
            </div>
          )}
        </div>

        <div className="flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-horizon-cyan/40 bg-horizon-cyan/20 px-3 py-0.5 text-xs font-semibold text-cyan-300">
                {MEDIA_TYPE_LABELS[detail.media_type]}
              </span>
              {year && <span className="text-xs text-slate-400">{year}</span>}
            </div>

            <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
              {detail.title}
            </h1>

            {detail.genres.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {detail.genres.map((genre) => (
                  <span
                    key={genre}
                    className="rounded-md border border-white/10 bg-white/5 px-2.5 py-0.5 text-xs text-slate-300"
                  >
                    {genre}
                  </span>
                ))}
              </div>
            )}

            {detail.description && (
              <p className="text-sm leading-relaxed text-slate-300">{detail.description}</p>
            )}
          </div>

          {!libraryEntry && (
            <div className="max-w-xs pt-2">
              <AddToLibraryButton mediaItemId={detail.id} />
            </div>
          )}
        </div>
      </div>

      {/* Library Status & Review Moderation Controls */}
      {libraryEntry && (
        <div className="space-y-6">
          <LibraryControls entry={libraryEntry} />
          <ReviewSection
            entryId={libraryEntry.id}
            mediaItemId={detail.id}
            initialReview={review}
          />
        </div>
      )}

      {/* Seasons / Episodes (Series) */}
      {detail.seasons.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-lg font-bold text-white">Seasons &amp; Episodes</h2>
          {detail.seasons.map((season) => (
            <div key={season.id} className="space-y-4">
              <h3 className="text-sm font-semibold text-cyan-300">
                Season {season.season_number}
                {season.title ? `: ${season.title}` : ""}
              </h3>
              <div className="space-y-4">
                {season.episodes.map((ep) => (
                  <ChapterProgressCard
                    key={ep.id}
                    chapter={ep}
                    entryId={libraryEntry?.id}
                    mediaItemId={detail.id}
                    progress={progressMap.get(ep.id)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Chapters (Games / Standalone Episodic) */}
      {detail.seasons.length === 0 && detail.chapters.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-white">Chapters &amp; Narrative Choices</h2>
          <div className="space-y-4">
            {detail.chapters.map((chapter) => (
              <ChapterProgressCard
                key={chapter.id}
                chapter={chapter}
                entryId={libraryEntry?.id}
                mediaItemId={detail.id}
                progress={progressMap.get(chapter.id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
