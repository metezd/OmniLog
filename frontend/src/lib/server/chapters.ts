import "server-only";

import type { ChapterProgress, ChapterRating, Decision, PlaytimeLog } from "@/types/api";
import { authedFetch } from "./authed";

// Episodic logging for one chapter or episode of a library entry (US-10, US-11, US-12).
// `entryId` is the id of the library entry, not of the title.

/**
 * Longest wait for a change (#411). The backend on Render sleeps when nobody uses it, and its first
 * answer after that took about 30 seconds. With the usual 10 seconds the change was often saved
 * after the page had already shown an error, and a second click saved it twice.
 */
export const CHAPTER_WRITE_TIMEOUT_MS = 60_000;

function chapterPath(entryId: number, chapterId: number): string {
  return `/library/${entryId}/chapters/${chapterId}`;
}

export function getChapterProgress(entryId: number, chapterId: number): Promise<ChapterProgress> {
  return authedFetch<ChapterProgress>(chapterPath(entryId, chapterId));
}

/** A rating from 1 to 5. A new rating replaces the old one. */
export function rateChapter(entryId: number, chapterId: number, rating: number): Promise<ChapterRating> {
  return authedFetch<ChapterRating>(`${chapterPath(entryId, chapterId)}/rating`, {
    method: "PUT",
    body: { rating },
    timeoutMs: CHAPTER_WRITE_TIMEOUT_MS,
  });
}

/** Adds one entry. The total of the chapter is the sum of all entries. */
export function logPlaytime(entryId: number, chapterId: number, minutes: number): Promise<PlaytimeLog> {
  return authedFetch<PlaytimeLog>(`${chapterPath(entryId, chapterId)}/playtime`, {
    method: "POST",
    body: { minutes },
    timeoutMs: CHAPTER_WRITE_TIMEOUT_MS,
  });
}

/** `choice` is the label of an option, such as "A". The decision point is only needed when the chapter has several. */
export function recordDecision(
  entryId: number,
  chapterId: number,
  choice: string,
  decisionPointId?: number,
): Promise<Decision> {
  return authedFetch<Decision>(`${chapterPath(entryId, chapterId)}/decision`, {
    method: "PUT",
    body: { choice, decision_point_id: decisionPointId },
    timeoutMs: CHAPTER_WRITE_TIMEOUT_MS,
  });
}

// ---------------------------------------------------------------- remove what was logged (#427)

/** Removes the rating of a chapter. The playtime and the choices stay. 404 when there is none. */
export function removeChapterRating(entryId: number, chapterId: number): Promise<void> {
  return authedFetch<void>(`${chapterPath(entryId, chapterId)}/rating`, {
    method: "DELETE",
    timeoutMs: CHAPTER_WRITE_TIMEOUT_MS,
  });
}

/** Removes the newest playtime entry of a chapter and answers the new progress. */
export function removeLastChapterPlaytime(entryId: number, chapterId: number): Promise<ChapterProgress> {
  return authedFetch<ChapterProgress>(`${chapterPath(entryId, chapterId)}/playtime/last`, {
    method: "DELETE",
    timeoutMs: CHAPTER_WRITE_TIMEOUT_MS,
  });
}

/** Removes the choice at a decision point. A chapter with several points needs the point id. */
export function removeDecision(entryId: number, chapterId: number, decisionPointId?: number): Promise<void> {
  const query = decisionPointId === undefined ? "" : `?decision_point_id=${decisionPointId}`;
  return authedFetch<void>(`${chapterPath(entryId, chapterId)}/decision${query}`, {
    method: "DELETE",
    timeoutMs: CHAPTER_WRITE_TIMEOUT_MS,
  });
}

