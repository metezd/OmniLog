import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TitlePlaytimeCard from "@/components/title/TitlePlaytimeCard";
import { logTitlePlaytimeAction } from "@/lib/actions/library";
import type { LibraryEntry } from "@/types/api";

vi.mock("@/lib/actions/library", () => ({
  logTitlePlaytimeAction: vi.fn(),
}));

const mockedLog = vi.mocked(logTitlePlaytimeAction);

function makeEntry(overrides: Partial<LibraryEntry> = {}): LibraryEntry {
  return {
    id: 10,
    user_id: 1,
    media_item_id: 91,
    status: "IN_PROGRESS",
    rating: 7,
    playtime_minutes: 0,
    updated_at: null,
    media_item: {
      id: 91,
      title: "Stardew Valley",
      media_type: "GAME",
      poster_url: null,
      release_date: "2016-02-26",
      external_api_id: 17000,
      genres: [],
    },
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("TitlePlaytimeCard (#413)", () => {
  it("shows 0h 0m for a title without playtime", () => {
    render(<TitlePlaytimeCard entry={makeEntry()} />);

    expect(screen.getByRole("heading", { name: "Playtime Logging" })).toBeInTheDocument();
    expect(screen.getByTestId("title-playtime-total")).toHaveTextContent("0h 0m logged");
    expect(screen.queryByText(/logged on chapters/)).not.toBeInTheDocument();
  });

  it("adds the chapter minutes to the total of the title", () => {
    render(<TitlePlaytimeCard entry={makeEntry({ playtime_minutes: 120 })} chapterMinutes={45} />);

    expect(screen.getByTestId("title-playtime-total")).toHaveTextContent("2h 45m logged");
    expect(screen.getByText("Includes 0h 45m logged on chapters.")).toBeInTheDocument();
  });

  it("sends the entry, hours and minutes and shows the saved message", async () => {
    mockedLog.mockResolvedValueOnce({ status: "saved", message: "+1h 15m logged" });
    const user = userEvent.setup();
    render(<TitlePlaytimeCard entry={makeEntry()} />);

    await user.type(screen.getByLabelText("Hours"), "1");
    await user.type(screen.getByLabelText("Minutes"), "15");
    await user.click(screen.getByRole("button", { name: "+ Log Time" }));

    await waitFor(() => expect(screen.getByText("+1h 15m logged")).toBeInTheDocument());
    const formData = mockedLog.mock.calls[0][1] as FormData;
    expect(formData.get("entryId")).toBe("10");
    expect(formData.get("mediaItemId")).toBe("91");
    expect(formData.get("hours")).toBe("1");
    expect(formData.get("minutes")).toBe("15");
  });

  it("shows an error from the action", async () => {
    mockedLog.mockResolvedValueOnce({ status: "error", message: "Playtime must be at least 1 minute." });
    render(<TitlePlaytimeCard entry={makeEntry()} label="Watch Time" />);

    expect(screen.getByRole("heading", { name: "Watch Time Logging" })).toBeInTheDocument();
    await userEvent.setup().click(screen.getByRole("button", { name: "+ Log Time" }));

    await waitFor(() =>
      expect(screen.getByText("Playtime must be at least 1 minute.")).toBeInTheDocument(),
    );
  });
});
