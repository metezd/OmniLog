import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import LibraryControls from "@/components/title/LibraryControls";
import { removeLibraryEntryAction, updateLibraryEntryAction } from "@/lib/actions/library";
import type { LibraryEntry } from "@/types/api";

vi.mock("@/lib/actions/library", () => ({
  updateLibraryEntryAction: vi.fn(),
  removeLibraryEntryAction: vi.fn(),
}));

const mockedUpdate = vi.mocked(updateLibraryEntryAction);
const mockedRemove = vi.mocked(removeLibraryEntryAction);

function makeEntry(overrides: Partial<LibraryEntry> = {}): LibraryEntry {
  return {
    id: 10,
    user_id: 1,
    media_item_id: 42,
    status: "IN_PROGRESS",
    rating: 8,
    updated_at: null,
    media_item: {
      id: 42,
      title: "Life is Strange",
      media_type: "GAME",
      poster_url: null,
      release_date: "2015-01-30",
      external_api_id: 100,
      genres: ["Adventure"],
    },
    ...overrides,
  };
}

describe("LibraryControls", () => {
  it("renders current watch status and rating and submits updated values", async () => {
    mockedUpdate.mockResolvedValueOnce({ status: "saved", message: "Library entry updated." });

    render(<LibraryControls entry={makeEntry()} />);

    expect(screen.getByLabelText(/Status/i)).toHaveValue("IN_PROGRESS");
    expect(screen.getByLabelText(/Overall Rating/i)).toHaveValue("8");

    await userEvent.setup().click(screen.getByRole("button", { name: "Save Changes" }));

    await waitFor(() => {
      expect(screen.getByText(/Library entry updated\./)).toBeInTheDocument();
    });
  });

  it("shows an error alert when updating the library entry fails", async () => {
    mockedUpdate.mockResolvedValueOnce({ status: "error", message: "Could not update entry." });

    render(<LibraryControls entry={makeEntry({ rating: null })} />);

    await userEvent.setup().click(screen.getByRole("button", { name: "Save Changes" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Could not update entry.");
    });
  });

  it("calls removeLibraryEntryAction when Remove from Library is clicked", async () => {
    mockedRemove.mockResolvedValueOnce(undefined);

    render(<LibraryControls entry={makeEntry()} />);

    await userEvent.setup().click(screen.getByRole("button", { name: "Remove from Library" }));

    await waitFor(() => {
      expect(mockedRemove).toHaveBeenCalledTimes(1);
    });
  });
});
