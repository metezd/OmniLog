import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import LibraryPage from "@/app/library/page";
import { BackendError } from "@/lib/server/backend";
import { getLibrary } from "@/lib/server/library";
import type { LibraryEntry } from "@/types/api";

vi.mock("@/lib/server/library", () => ({ getLibrary: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));

const library = vi.mocked(getLibrary);

function entry(id: number, title: string): LibraryEntry {
  return {
    id,
    user_id: 7,
    media_item_id: id,
    status: "COMPLETED",
    rating: 9,
    updated_at: null,
    media_item: { id, title, media_type: "SERIES", poster_url: null, release_date: null, external_api_id: null, genres: [] },
  };
}

// The page is an async Server Component, so the test calls it and renders what it returns.
async function renderPage() {
  render(await LibraryPage());
}

describe("Library page", () => {
  it("shows one card for each title", async () => {
    library.mockResolvedValue([entry(1, "Severance"), entry(2, "Arcane")]);

    await renderPage();

    expect(screen.getByRole("heading", { name: "Library" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Severance" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Arcane" })).toBeInTheDocument();
  });

  it("shows the empty state for a new user", async () => {
    library.mockResolvedValue([]);

    await renderPage();

    expect(screen.getByRole("status")).toHaveTextContent("Your library is empty");
  });

  it("shows the unavailable state, with a retry button, when the backend does not answer", async () => {
    library.mockRejectedValue(new BackendError(0, "The server cannot be reached"));

    await renderPage();

    expect(screen.getByRole("alert")).toHaveTextContent("Service unavailable");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("lets a redirect through instead of showing it as an error", async () => {
    library.mockRejectedValue(new Error("NEXT_REDIRECT /session-expired"));

    await expect(LibraryPage()).rejects.toThrow("NEXT_REDIRECT /session-expired");
  });
});
