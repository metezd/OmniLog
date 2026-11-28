import { vi } from "vitest";

// Stand-ins for the Server Actions that the title page passes to its client components. A page
// test that renders the whole title page needs all of them, but calls none. Use it like this:
//
//   vi.mock("@/lib/actions/library", async () => (await import("../../mocks/server-actions")).libraryActions);
//   vi.mock("@/lib/actions/chapters", async () => (await import("../../mocks/server-actions")).chapterActions);

export const libraryActions = {
  addToLibraryAction: vi.fn(),
  updateLibraryEntryAction: vi.fn(),
  removeLibraryEntryAction: vi.fn(),
  logTitlePlaytimeAction: vi.fn(),
  submitReviewAction: vi.fn(),
};

export const chapterActions = {
  rateChapterAction: vi.fn(),
  logPlaytimeAction: vi.fn(),
  recordDecisionAction: vi.fn(),
};
