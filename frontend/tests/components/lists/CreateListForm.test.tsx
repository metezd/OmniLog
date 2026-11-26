import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import CreateListForm from "@/components/lists/CreateListForm";
import { createListAction } from "@/lib/actions/lists";

vi.mock("@/lib/actions/lists", () => ({
  createListAction: vi.fn(),
}));

const mockedCreate = vi.mocked(createListAction);

describe("CreateListForm", () => {
  it("renders input and submit button and submits new list name", async () => {
    mockedCreate.mockResolvedValueOnce({ status: "saved", message: 'Created "Favorites".' });

    render(<CreateListForm />);

    const input = screen.getByPlaceholderText(/New list name/i);
    await userEvent.setup().type(input, "Favorites");
    await userEvent.click(screen.getByRole("button", { name: "+ Create List" }));

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalled();
    });
  });

  it("displays error message when list creation fails (e.g. 409 conflict)", async () => {
    mockedCreate.mockResolvedValueOnce({ status: "error", message: "List name already exists." });

    render(<CreateListForm />);

    await userEvent.setup().type(screen.getByPlaceholderText(/New list name/i), "Favorites");
    await userEvent.click(screen.getByRole("button", { name: "+ Create List" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("List name already exists.");
    });
  });
});
