"use client";

import { useActionState } from "react";

import {
  type ChapterActionState,
  logPlaytimeAction,
  rateChapterAction,
  recordDecisionAction,
} from "@/lib/actions/chapters";
import type { Chapter, ChapterProgress } from "@/types/api";

interface ChapterProgressCardProps {
  chapter: Chapter;
  entryId?: number;
  mediaItemId: number;
  progress?: ChapterProgress;
}

const INITIAL_STATE: ChapterActionState = { status: "idle" };
const STAR_OPTIONS = [1, 2, 3, 4, 5];

export default function ChapterProgressCard({
  chapter,
  entryId,
  mediaItemId,
  progress,
}: ChapterProgressCardProps) {
  const [rateState, rateFormAction, ratePending] = useActionState(rateChapterAction, INITIAL_STATE);
  const [playState, playFormAction, playPending] = useActionState(logPlaytimeAction, INITIAL_STATE);
  const [doneState, doneFormAction, donePending] = useActionState(logPlaytimeAction, INITIAL_STATE);
  const [decState, decFormAction, decPending] = useActionState(
    recordDecisionAction,
    INITIAL_STATE,
  );

  const currentRating = progress?.rating ?? null;
  const totalMinutes = progress?.playtime_minutes ?? 0;
  const decisionsByPoint = new Map(
    (progress?.decisions ?? []).map((d) => [d.decision_point_id, d.choice]),
  );

  // Logging adds to the total, so "completed" logs only what is still missing from the full length.
  const runtimeMinutes = chapter.runtime_minutes ?? 0;
  const hasRuntime = runtimeMinutes > 0;
  const remainingMinutes = Math.max(runtimeMinutes - totalMinutes, 0);
  const isCompleted = hasRuntime && remainingMinutes === 0;
  const chapterName = chapter.title ?? `Chapter ${chapter.number}`;

  return (
    <div className="liquid-glass space-y-4 rounded-2xl border border-white/10 p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-cyan-300">
            Episode / Chapter {chapter.number}
          </span>
          <h3 className="text-sm font-bold text-white">{chapterName}</h3>
          {(chapter.release_date || chapter.runtime_minutes) && (
            <p className="mt-1 text-xs text-slate-400">
              {[
                chapter.release_date,
                chapter.runtime_minutes ? `${chapter.runtime_minutes} min` : null,
              ]
                .filter(Boolean)
                .join(" • ")}
            </p>
          )}
        </div>
        {entryId && (
          <div className="flex items-center gap-2 text-xs">
            <span className="rounded-lg border border-amber-400/30 bg-amber-400/10 px-2.5 py-1 font-medium text-amber-300">
              {currentRating ? `★ ${currentRating}/5` : "Unrated"}
            </span>
            <span className="rounded-lg border border-purple-400/30 bg-purple-400/10 px-2.5 py-1 font-medium text-purple-200">
              {totalMinutes} min logged
            </span>
          </div>
        )}
      </div>

      {entryId ? (
        <div className="grid grid-cols-1 gap-4 border-t border-white/10 pt-4 md:grid-cols-2">
          {/* Chapter 5-Star Rating (US-10) */}
          <form action={rateFormAction} className="space-y-2">
            <input type="hidden" name="entryId" value={entryId} />
            <input type="hidden" name="chapterId" value={chapter.id} />
            <input type="hidden" name="mediaItemId" value={mediaItemId} />
            <span className="block text-xs font-medium text-slate-300">
              Chapter Rating (1–5 ★)
            </span>
            <div className="flex flex-wrap items-center gap-1.5">
              {STAR_OPTIONS.map((stars) => (
                <button
                  key={stars}
                  type="submit"
                  name="rating"
                  value={stars}
                  disabled={ratePending}
                  className={`rounded-lg border px-2.5 py-1 text-xs font-semibold transition-all ${
                    currentRating === stars
                      ? "border-amber-400/60 bg-amber-400/20 text-amber-200"
                      : "border-white/10 bg-white/5 text-slate-300 hover:bg-white/15"
                  }`}
                >
                  {stars} ★
                </button>
              ))}
            </div>
            {rateState.status === "saved" && (
              <p className="text-[11px] text-emerald-300">{rateState.message}</p>
            )}
            {rateState.status === "error" && (
              <p className="text-[11px] text-rose-300">{rateState.message}</p>
            )}
          </form>

          <div className="space-y-3">
            {/* Playtime Logging (US-11) */}
            <form action={playFormAction} className="space-y-2">
              <input type="hidden" name="entryId" value={entryId} />
              <input type="hidden" name="chapterId" value={chapter.id} />
              <input type="hidden" name="mediaItemId" value={mediaItemId} />
              <label htmlFor={`minutes-${chapter.id}`} className="block text-xs font-medium text-slate-300">
                Log Playtime / Watch Time (minutes)
              </label>
              <div className="flex items-center gap-2">
                <input
                  id={`minutes-${chapter.id}`}
                  type="number"
                  name="minutes"
                  min={1}
                  max={1440}
                  placeholder="e.g. 45"
                  required
                  className="w-28 rounded-lg border border-white/15 bg-slate-900/80 px-2.5 py-1 text-xs text-white focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={playPending}
                  className="rounded-lg border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-slate-200 hover:bg-white/20 disabled:opacity-50"
                >
                  {playPending ? "Logging…" : "+ Log Time"}
                </button>
              </div>
              {playState.status === "saved" && (
                <p className="text-[11px] text-emerald-300">{playState.message}</p>
              )}
              {playState.status === "error" && (
                <p className="text-[11px] text-rose-300">{playState.message}</p>
              )}
            </form>

            {/* One click to log what is still missing from the full length (US-11) */}
            <form action={doneFormAction} className="space-y-1">
              <input type="hidden" name="entryId" value={entryId} />
              <input type="hidden" name="chapterId" value={chapter.id} />
              <input type="hidden" name="mediaItemId" value={mediaItemId} />
              <input type="hidden" name="minutes" value={remainingMinutes} />
              <button
                type="submit"
                disabled={!hasRuntime || isCompleted || donePending}
                aria-label={`${isCompleted ? "Completed" : "Mark completed"}: ${chapterName}`}
                className="rounded-lg border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-200 hover:bg-emerald-400/20 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isCompleted
                  ? "\u2713 Completed"
                  : donePending
                    ? "Saving…"
                    : `\u2713 Mark completed${hasRuntime ? ` (${remainingMinutes} min)` : ""}`}
              </button>
              {!hasRuntime && (
                <p className="text-[11px] text-slate-400">
                  This chapter has no known length, so log the time by hand.
                </p>
              )}
              {doneState.status === "saved" && (
                <p className="text-[11px] text-emerald-300">{doneState.message}</p>
              )}
              {doneState.status === "error" && (
                <p className="text-[11px] text-rose-300">{doneState.message}</p>
              )}
            </form>
          </div>
        </div>
      ) : (
        <p className="border-t border-white/10 pt-3 text-xs text-slate-400">
          Add this title to your library to rate chapters, log playtime, and record branching choices.
        </p>
      )}

      {/* Branching Narrative Decisions (US-12) */}
      {chapter.decision_points.length > 0 && (
        <div className="space-y-3 border-t border-white/10 pt-4">
          <span className="block text-xs font-semibold uppercase tracking-wider text-purple-300">
            Narrative Decision Points
          </span>
          {chapter.decision_points.map((dp) => {
            const chosen = decisionsByPoint.get(dp.id);
            return (
              <div
                key={dp.id}
                className="rounded-xl border border-purple-500/20 bg-purple-950/20 p-3.5"
              >
                <p className="text-xs font-medium text-slate-100">{dp.prompt}</p>
                {entryId ? (
                  <form action={decFormAction} className="mt-2.5 flex flex-wrap gap-2">
                    <input type="hidden" name="entryId" value={entryId} />
                    <input type="hidden" name="chapterId" value={chapter.id} />
                    <input type="hidden" name="mediaItemId" value={mediaItemId} />
                    <input type="hidden" name="decisionPointId" value={dp.id} />
                    {dp.options.map((option) => (
                      <button
                        key={option.id}
                        type="submit"
                        name="choice"
                        value={option.label}
                        disabled={decPending}
                        className={`rounded-lg border px-3 py-1.5 text-left text-xs transition-all ${
                          chosen === option.label
                            ? "border-purple-400 bg-purple-500/30 font-semibold text-white"
                            : "border-white/15 bg-white/5 text-slate-300 hover:bg-white/15"
                        }`}
                      >
                        <span className="font-bold text-purple-300">{option.label}:</span>{" "}
                        {option.text ?? option.label}
                      </button>
                    ))}
                  </form>
                ) : (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {dp.options.map((option) => (
                      <span
                        key={option.id}
                        className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-400"
                      >
                        {option.label}: {option.text ?? option.label}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
          {decState.status === "saved" && (
            <p className="text-[11px] text-emerald-300">{decState.message}</p>
          )}
          {decState.status === "error" && (
            <p className="text-[11px] text-rose-300">{decState.message}</p>
          )}
        </div>
      )}
    </div>
  );
}