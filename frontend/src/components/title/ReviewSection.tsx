"use client";

import { useActionState, useState, type FormEvent } from "react";

import ErrorState from "@/components/states/ErrorState";
import { deleteReviewAction, type ReviewActionState, submitReviewAction } from "@/lib/actions/library";
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
  const [isEditing, setIsEditing] = useState(false);
  const [draftText, setDraftText] = useState(initialReview?.text ?? "");
  const [clientError, setClientError] = useState<string | null>(null);
  const [showActionError, setShowActionError] = useState(true);
  const [revealSpoiler, setRevealSpoiler] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const [state, formAction, pending] = useActionState(
    async (prev: ReviewActionState, formData: FormData): Promise<ReviewActionState> => {
      if (formData.get("intent") === "delete") {
        // Removing the review (#427): the section shows the empty form again
        const removed = await deleteReviewAction(prev, formData);
        setConfirmDelete(false);
        if (removed.status === "idle") {
          setIsEditing(false);
          setDraftText("");
        }
        return removed;
      }
      const result = await submitReviewAction(prev, formData);
      if (result.status === "saved") {
        setIsEditing(false);
        setRevealSpoiler(false);
        setDraftText(result.review.text);
      }
      return result;
    },
    initialState,
  );

  // `review: null` in the state means that the review was removed, so it does not fall back
  const currentReview =
    state.status === "saved" ? state.review : state.review !== undefined ? state.review : initialReview;
  const showForm = !currentReview || isEditing;
  const activeError =
    clientError !== null
      ? { code: "validation" as const, message: clientError }
      : state.status === "error" && showActionError
        ? { code: state.code, message: state.message }
        : null;

  function handleStartEdit() {
    setDraftText(currentReview?.text ?? "");
    setClientError(null);
    setShowActionError(false);
    setIsEditing(true);
  }

  function handleCancelEdit() {
    setDraftText(currentReview?.text ?? "");
    setClientError(null);
    setShowActionError(false);
    setIsEditing(false);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    setShowActionError(true);
    if (!draftText.trim()) {
      event.preventDefault();
      setClientError("Review text cannot be empty.");
      return;
    }
    setClientError(null);
  }

  if (activeError?.code === "not_found") {
    return (
      <div className="liquid-glass rounded-2xl border border-white/10 p-6">
        <ErrorState kind="not_found" message={activeError.message} />
      </div>
    );
  }

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
            {currentReview.contains_spoiler === true && (
              <span
                role="status"
                className="rounded-full border border-rose-500/40 bg-rose-500/20 px-3 py-1 text-xs font-semibold text-rose-200"
              >
                ⚠ Spoiler Warning
                {currentReview.spoiler_score !== null
                  ? ` (${Math.round(currentReview.spoiler_score * 100)}% confidence)`
                  : ""}
              </span>
            )}
            {currentReview.contains_spoiler === false && (
              <span className="rounded-full border border-emerald-500/40 bg-emerald-500/20 px-3 py-1 text-xs font-semibold text-emerald-200">
                ✓ Spoiler-Free
                {currentReview.spoiler_model_version ? ` (${currentReview.spoiler_model_version})` : ""}
              </span>
            )}
            {currentReview.contains_spoiler === null && (
              <span className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs font-medium text-slate-300">
                Spoiler check not completed
              </span>
            )}
          </div>
        )}
      </div>

      {currentReview && !isEditing && (
        <div className="space-y-3 rounded-xl border border-white/10 bg-black/30 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-[11px] font-medium text-slate-400">Saved Review</span>
            <div className="flex items-center gap-2">
              {currentReview.contains_spoiler === true && (
                <button
                  type="button"
                  onClick={() => setRevealSpoiler((prev) => !prev)}
                  className="rounded-lg border border-amber-400/30 bg-amber-400/10 px-2.5 py-1 text-[11px] font-medium text-amber-200 hover:bg-amber-400/20"
                >
                  {revealSpoiler ? "Hide Spoiler" : "Reveal Spoiler"}
                </button>
              )}
              <button
                type="button"
                onClick={handleStartEdit}
                className="rounded-lg border border-white/15 bg-white/5 px-2.5 py-1 text-[11px] font-medium text-slate-200 transition-all hover:bg-white/15"
              >
                Edit Review
              </button>
              {confirmDelete ? (
                <form action={formAction} className="flex items-center gap-2">
                  <input type="hidden" name="entryId" value={entryId} />
                  <input type="hidden" name="mediaItemId" value={mediaItemId} />
                  <input type="hidden" name="intent" value="delete" />
                  <button
                    type="submit"
                    disabled={pending}
                    className="rounded-lg border border-rose-400/40 bg-rose-400/20 px-2.5 py-1 text-[11px] font-semibold text-rose-100 hover:bg-rose-400/30 disabled:opacity-50"
                  >
                    {pending ? "Deleting…" : "Confirm delete"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmDelete(false)}
                    className="rounded-lg border border-white/15 bg-white/5 px-2.5 py-1 text-[11px] font-medium text-slate-200 hover:bg-white/15"
                  >
                    Keep it
                  </button>
                </form>
              ) : (
                <button
                  type="button"
                  onClick={() => setConfirmDelete(true)}
                  className="rounded-lg border border-rose-400/30 bg-rose-400/10 px-2.5 py-1 text-[11px] font-medium text-rose-200 hover:bg-rose-400/20"
                >
                  Delete Review
                </button>
              )}
            </div>
          </div>

          <p
            className={`whitespace-pre-wrap text-sm text-slate-200 transition-all ${
              currentReview.contains_spoiler === true && !revealSpoiler ? "select-none blur-sm" : ""
            }`}
          >
            {currentReview.text}
          </p>
        </div>
      )}

      {showForm && (
        <form action={formAction} onSubmit={handleSubmit} noValidate className="space-y-3">
          <input type="hidden" name="entryId" value={entryId} />
          <input type="hidden" name="mediaItemId" value={mediaItemId} />
          <label htmlFor={`review-text-${entryId}`} className="sr-only">
            Review text
          </label>
          <textarea
            id={`review-text-${entryId}`}
            name="text"
            rows={3}
            maxLength={5000}
            value={draftText}
            onChange={(event) => {
              setDraftText(event.target.value);
              if (clientError) setClientError(null);
            }}
            placeholder="Write your thoughts on this title, chapter twists, or ending..."
            className="w-full rounded-xl border border-white/15 bg-slate-900/80 p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-[11px] text-slate-400">
              Model: NLP Spoiler Classifier (US-14)
            </span>
            <div className="flex items-center gap-2">
              {currentReview && (
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  disabled={pending}
                  className="rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200 transition-all hover:bg-white/15 disabled:opacity-50"
                >
                  Cancel
                </button>
              )}
              <button
                type="submit"
                disabled={pending}
                className="rounded-xl border border-horizon-cyan/40 bg-horizon-cyan/20 px-4 py-2 text-xs font-semibold text-cyan-200 transition-all hover:bg-horizon-cyan/30 disabled:opacity-50"
              >
                {pending ? "Saving…" : "Save"}
              </button>
            </div>
          </div>
        </form>
      )}

      {state.status === "saved" && !isEditing && !activeError && (
        <p className="text-xs text-emerald-300">
          ✓{" "}
          {state.review.contains_spoiler === null
            ? "Review saved. Spoiler check could not be completed yet."
            : "Review saved."}
        </p>
      )}

      {activeError && (
        <p role="alert" className="text-xs text-rose-300">
          {activeError.message}
        </p>
      )}
    </div>
  );
}
