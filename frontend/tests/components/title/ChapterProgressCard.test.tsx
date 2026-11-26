import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import ChapterProgressCard from "@/components/title/ChapterProgressCard";
import { logPlaytimeAction, rateChapterAction, recordDecisionAction } from "@/lib/actions/chapters";
import type { Chapter, ChapterProgress } from "@/types/api";

vi.mock("@/lib/actions/chapters", () => ({
  rateChapterAction: vi.fn(),
  logPlaytimeAction: vi.fn(),
  recordDecisionAction: vi.fn(),
}));

const mockedRate = vi.mocked(rateChapterAction);
const mockedPlay = vi.mocked(logPlaytimeAction);
const mockedDecision = vi.mocked(recordDecisionAction);

function makeChapter(overrides: Partial<Chapter> = {}): Chapter {
  return {
    id: 101,
    number: 1,
    kind: "CHAPTER",
    title: "Chrysalis",
    release_date: "2015-01-30",
    runtime_minutes: 120,
    decision_points: [
      {
        id: 501,
        position: 1,
        prompt: "Report Nathan to the Principal?",
        options: [
          { id: 1, label: "A", text: "Report Nathan" },
          { id: 2, label: "B", text: "Hide the truth" },
        ],
      },
    ],
    ...overrides,
  };
}

function makeProgress(overrides: Partial<ChapterProgress> = {}): ChapterProgress {
  return {
    library_entry_id: 10,
    chapter_id: 101,
    rating: 4,
    playtime_minutes: 95,
    updated_at: null,
    choice: "A",
    decided_at: null,
    decisions: [{ decision_point_id: 501, choice: "A", decided_at: "2026-10-01T10:00:00Z" }],
    ...overrides,
  };
}

describe("ChapterProgressCard", () => {
  it("shows read-only prompt and options when the title is not in the user's library", () => {
    render(<ChapterProgressCard chapter={makeChapter()} mediaItemId={42} />);

    expect(screen.getByRole("heading", { name: "Chrysalis" })).toBeInTheDocument();
    expect(screen.getByText(/Add this title to your library to rate chapters/)).toBeInTheDocument();
    expect(screen.getByText("Report Nathan to the Principal?")).toBeInTheDocument();
    expect(screen.getByText("A: Report Nathan")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "5 ★" })).not.toBeInTheDocument();
  });

  it("displays current rating, running total playtime and allows rating, logging time and choosing an option", async () => {
    mockedRate.mockResolvedValueOnce({ status: "saved", message: "Rated 5/5 ★" });
    mockedPlay.mockResolvedValueOnce({ status: "saved", message: "+30m logged" });
    mockedDecision.mockResolvedValueOnce({ status: "saved", message: 'Choice "B" saved' });

    const user = userEvent.setup();
    render(
      <ChapterProgressCard
        chapter={makeChapter()}
        entryId={10}
        mediaItemId={42}
        progress={makeProgress()}
      />,
    );

    expect(screen.getByText("★ 4/5")).toBeInTheDocument();
    expect(screen.getByText("95 min logged")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "5 ★" }));
    await waitFor(() => expect(screen.getByText("Rated 5/5 ★")).toBeInTheDocument());

    await user.type(screen.getByPlaceholderText("e.g. 45"), "30");
    await user.click(screen.getByRole("button", { name: "+ Log Time" }));
    await waitFor(() => expect(screen.getByText("+30m logged")).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: /B:\s*Hide the truth/ }));
    await waitFor(() => expect(screen.getByText('Choice "B" saved')).toBeInTheDocument());
  });

  it("labels the playtime field, so a screen reader names it (Sonar S6853)", () => {
    render(<ChapterProgressCard chapter={makeChapter()} entryId={10} mediaItemId={42} progress={makeProgress()} />);

    expect(screen.getByLabelText("Log Playtime / Watch Time (minutes)")).toHaveAttribute("name", "minutes");
  });
});
