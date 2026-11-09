import "server-only";

import type { ChapterProgress, ChapterRating, Decision, PlaytimeLog } from "@/types/api";
import { authedFetch } from "./authed";

// Episodic logging for one chapter or episode of a library entry (US-10, US-11, US-12).
// `entryId` is the id of the library entry, not of the title.

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
  });
}

/** Adds one entry. The total of the chapter is the sum of all entries. */
export function logPlaytime(entryId: number, chapterId: number, minutes: number): Promise<PlaytimeLog> {
  return authedFetch<PlaytimeLog>(`${chapterPath(entryId, chapterId)}/playtime`, {
    method: "POST",
    body: { minutes },
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
  });
}
