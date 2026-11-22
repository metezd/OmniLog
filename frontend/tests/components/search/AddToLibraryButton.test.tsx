import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import AddToLibraryButton from "@/components/search/AddToLibraryButton";
import { addToLibraryAction } from "@/lib/actions/library";

vi.mock("@/lib/actions/library", () => ({
  addToLibraryAction: vi.fn(),
}));

const mockedAction = vi.mocked(addToLibraryAction);

describe("AddToLibraryButton", () => {
  it("submits mediaItemId and transitions to Added to library state", async () => {
    mockedAction.mockResolvedValueOnce({ status: "added" });

    render(<AddToLibraryButton mediaItemId={15} />);

    await userEvent.setup().click(screen.getByRole("button", { name: "+ Add to Library" }));

    await waitFor(() => {
      expect(screen.getByText(/Added to library/)).toBeInTheDocument();
    });
  });

  it("displays an error alert when the action fails", async () => {
    mockedAction.mockResolvedValueOnce({ status: "error", message: "Could not add title." });

    render(<AddToLibraryButton mediaItemId={15} />);

    await userEvent.setup().click(screen.getByRole("button", { name: "+ Add to Library" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Could not add title.");
    });
  });
});
