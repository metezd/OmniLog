import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import DeleteListButton from "@/components/lists/DeleteListButton";
import { deleteListAction } from "@/lib/actions/lists";

vi.mock("@/lib/actions/lists", () => ({
  deleteListAction: vi.fn(),
}));

describe("DeleteListButton", () => {
  it("asks for confirmation before deleting a list and submits upon confirmation", async () => {
    render(<DeleteListButton listId={1} listName="Favorites" />);

    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();

    await userEvent.setup().click(screen.getByRole("button", { name: "Delete" }));

    expect(screen.getByText('Delete "Favorites"?')).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Yes" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "No" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "No" }));
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
  });
});
