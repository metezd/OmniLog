import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DiaryPage from "@/app/diary/page";
import { getDiary } from "@/lib/server/journal";
import { getLibrary } from "@/lib/server/library";
import type { DiaryEntry } from "@/types/api";

vi.mock("@/lib/server/journal", () => ({ getDiary: vi.fn() }));
vi.mock("@/lib/server/library", () => ({ getLibrary: vi.fn() }));

const diaryMock = vi.mocked(getDiary);
const libraryMock = vi.mocked(getLibrary);

function events(count: number, firstId = 1): DiaryEntry[] {
  return Array.from({ length: count }, (_, i) => ({
    id: firstId + i,
    user_id: 1,
    media_item_id: null,
    action: "LIST_CREATED",
    details: `Created list ${firstId + i}`,
    created_at: "2026-11-27T10:00:00Z",
  }));
}

async function renderPage(page?: string) {
  render(await DiaryPage({ searchParams: Promise.resolve(page ? { page } : {}) }));
}

describe("DiaryPage paging (#418)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    libraryMock.mockResolvedValue([]);
  });

  it("asks for one event more than a page, shows 100 and links to the older page", async () => {
    diaryMock.mockResolvedValue(events(101));

    await renderPage();

    expect(diaryMock).toHaveBeenCalledWith({ limit: 101, offset: 0 });
    expect(screen.getAllByText(/^Created list/)).toHaveLength(100);
    expect(screen.getByRole("link", { name: "Older events" })).toHaveAttribute("href", "/diary?page=2");
    expect(screen.queryByRole("link", { name: "Newer events" })).not.toBeInTheDocument();
  });

  it("reads the second page with an offset and links back", async () => {
    diaryMock.mockResolvedValue(events(30, 101));

    await renderPage("2");

    expect(diaryMock).toHaveBeenCalledWith({ limit: 101, offset: 100 });
    expect(screen.getByRole("link", { name: "Newer events" })).toHaveAttribute("href", "/diary");
    expect(screen.queryByRole("link", { name: "Older events" })).not.toBeInTheDocument();
  });

  it("shows no pager when everything fits on one page", async () => {
    diaryMock.mockResolvedValue(events(3));

    await renderPage();

    expect(screen.queryByRole("navigation", { name: "Diary pages" })).not.toBeInTheDocument();
  });

  it.each(["0", "-2", "abc", "1.5"])("reads the first page for a wrong page number %s", async (page) => {
    diaryMock.mockResolvedValue(events(1));

    await renderPage(page);

    expect(diaryMock).toHaveBeenCalledWith({ limit: 101, offset: 0 });
  });
});
