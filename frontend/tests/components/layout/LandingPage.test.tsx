import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "@/app/page";
import { getLibrary } from "@/lib/server/library";
import { getCurrentUser } from "@/lib/server/user";
import type { CurrentUser, LibraryEntry } from "@/types/api";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: vi.fn() }),
}));
vi.mock("@/lib/server/user", () => ({ getCurrentUser: vi.fn() }));
vi.mock("@/lib/server/library", () => ({ getLibrary: vi.fn() }));

const mockedUser = vi.mocked(getCurrentUser);
const mockedLibrary = vi.mocked(getLibrary);

const USER: CurrentUser = {
  id: 7,
  email: "ali@example.com",
  username: "ali",
  created_at: "2026-10-01T10:00:00Z",
};

function makeEntry(
  id: number,
  mediaItemId: number,
  title: string,
  mediaType: "GAME" | "SERIES" = "GAME",
  rating: number | null = 9,
): LibraryEntry {
  return {
    id,
    user_id: USER.id,
    media_item_id: mediaItemId,
    status: "IN_PROGRESS",
    rating,
    playtime_minutes: 0,
    updated_at: null,
    media_item: {
      id: mediaItemId,
      title,
      media_type: mediaType,
      poster_url: null,
      release_date: "2025",
      external_api_id: mediaItemId,
      genres: [],
    },
  };
}

describe("Landing page S-01 (Home /)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows the OmniLog explanation, main features, and Register / Log in buttons for visitors", async () => {
    mockedUser.mockResolvedValue(null);

    render(await Home());

    expect(
      screen.getByRole("heading", { name: /Every story, choice & chapter/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/cross-media tracking and narrative journaling platform/i),
    ).toBeInTheDocument();

    // Main feature cards
    expect(
      screen.getByRole("heading", { name: "Unified Cross-Media Library" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Episodic & Decision Logging" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "AI Recommendations & Spoiler Shield" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Activity Diary, Lists & Analytics" }),
    ).toBeInTheDocument();

    // Visitor CTAs
    expect(screen.getByRole("link", { name: "Register" })).toHaveAttribute(
      "href",
      "/register",
    );
    expect(screen.getByRole("link", { name: "Log in" })).toHaveAttribute(
      "href",
      "/login",
    );

    // No developer PaletteTool or hard-coded mock dashboard cards
    expect(
      screen.queryByText(/Cinematic Horizon Design System Tokens/i),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("Cyberpunk 2077")).not.toBeInTheDocument();
    expect(mockedLibrary).not.toHaveBeenCalled();
  });

  it("shows real library data, library navigation, and catalog search for a logged-in user", async () => {
    mockedUser.mockResolvedValue(USER);
    mockedLibrary.mockResolvedValue([
      makeEntry(1, 10, "Life is Strange", "GAME", 9),
      makeEntry(2, 20, "Dark", "SERIES", 10),
    ]);

    render(await Home());

    expect(screen.getByText("@ali")).toBeInTheDocument();
    expect(
      screen.getByText("2 titles in your personal library"),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open Library" })).toHaveAttribute(
      "href",
      "/library",
    );

    // Real titles from the user's library
    expect(screen.getByRole("link", { name: /Life is Strange/i })).toHaveAttribute(
      "href",
      "/title/10",
    );
    expect(screen.getByRole("link", { name: /Dark/i })).toHaveAttribute(
      "href",
      "/title/20",
    );

    // Visitor buttons are not shown to a logged-in user
    expect(screen.queryByRole("link", { name: "Register" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Log in" })).not.toBeInTheDocument();
  });

  it("navigates to /search with query and media filter when a logged-in user searches", async () => {
    mockedUser.mockResolvedValue(USER);
    mockedLibrary.mockResolvedValue([]);

    render(await Home());

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Video Games" }));
    await user.type(screen.getByRole("textbox", { name: "Search catalog" }), "Hades");
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(pushMock).toHaveBeenCalledWith("/search?q=Hades&type=GAME");
  });
});
