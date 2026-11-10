"use client";

import { useActionState, useState } from "react";

import { type ReviewActionState, submitReviewAction } from "@/lib/actions/library";
import type { Review } from "@/types/api";

interface ReviewSectionProps {
  entryId: number;
  mediaItemId: number;
  initialReview: Review | null;
}

export default function ReviewSection({
  entryId,
  mediaItemId,
  initialReview,
}: ReviewSectionProps) {
  const initialState: ReviewActionState = { status: "idle", review: initialReview };
  const [state, formAction, pending] = useActionState(submitReviewAction, initialState);
  const currentReview = state.status === "saved" ? state.review : initialReview;
  const [revealSpoiler, setRevealSpoiler] = useState(false);

  return (
    <div className="liquid-glass space-y-4 rounded-2xl border border-white/10 p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-base font-bold text-white">
            Your Journal Review &amp; AI Spoiler Moderation
          </h2>
          <p className="text-xs text-slate-400">
            Reviews are automatically scanned by OmniLog&apos;s NLP pipeline to flag plot spoilers
          </p>
        </div>

        {currentReview && (
          <div className="flex items-center gap-2">
            {currentReview.contains_spoiler ? (
              <span className="rounded-full border border-rose-500/40 bg-rose-500/20 px-3 py-1 text-xs font-semibold text-rose-200">
                ⚠ Spoiler Flagged ({Math.round(currentReview.spoiler_score * 100)}% confidence)
              </span>
            ) : (
              <span className="rounded-full border border-emerald-500/40 bg-emerald-500/20 px-3 py-1 text-xs font-semibold text-emerald-200">
                ✓ Spoiler-Free ({currentReview.spoiler_model_version})
              </span>
            )}
          </div>
        )}
      </div>

      {currentReview && (
        <div className="space-y-2 rounded-xl border border-white/10 bg-black/30 p-4">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-400">Published Review</span>
            {currentReview.contains_spoiler && (
              <button
                type="button"
                onClick={() => setRevealSpoiler((prev) => !prev)}
                className="rounded-lg border border-amber-400/30 bg-amber-400/10 px-2.5 py-0.5 text-[11px] font-medium text-amber-200 hover:bg-amber-400/20"
              >
                {revealSpoiler ? "Hide Spoiler" : "Reveal Spoiler"}
              </button>
            )}
          </div>
          <p
            className={`text-sm text-slate-200 transition-all ${
              currentReview.contains_spoiler && !revealSpoiler ? "select-none blur-sm" : ""
            }`}
          >
            {currentReview.text}
          </p>
        </div>
      )}

      <form action={formAction} className="space-y-3">
        <input type="hidden" name="entryId" value={entryId} />
        <input type="hidden" name="mediaItemId" value={mediaItemId} />
        <textarea
          name="text"
          rows={3}
          defaultValue={currentReview?.text ?? ""}
          placeholder="Write your thoughts on this title, chapter twists, or ending..."
          required
          className="w-full rounded-xl border border-white/15 bg-slate-900/80 p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
        />
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-slate-400">
            Model: NLP Spoiler Classifier (US-14)
          </span>
          <button
            type="submit"
            disabled={pending}
            className="rounded-xl border border-horizon-cyan/40 bg-horizon-cyan/20 px-4 py-2 text-xs font-semibold text-cyan-200 transition-all hover:bg-horizon-cyan/30 disabled:opacity-50"
          >
            {pending ? "Analyzing & Saving…" : currentReview ? "Update Review" : "Post Review"}
          </button>
        </div>
      </form>

      {state.status === "error" && (
        <p role="alert" className="text-xs text-rose-300">
          {state.message}
        </p>
      )}
    </div>
  );
}
