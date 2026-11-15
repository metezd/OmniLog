import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import Navbar from "@/components/layout/Navbar";
import { SearchProvider } from "@/context/SearchContext";
import { logoutAction } from "@/lib/actions/auth";
import type { CurrentUser } from "@/types/api";

vi.mock("@/lib/actions/auth", () => ({ logoutAction: vi.fn() }));

const USER: CurrentUser = { id: 7, email: "ali@example.com", username: "ali", created_at: "2026-10-01T10:00:00Z" };

function renderNavbar(user: CurrentUser | null) {
  return render(
    <SearchProvider>
      <Navbar user={user} />
    </SearchProvider>,
  );
}

describe("Navbar for a visitor", () => {
  it("shows Sign In and Get Started, and nothing of an account", () => {
    renderNavbar(null);

    expect(screen.getByRole("link", { name: "Sign In" })).toHaveAttribute("href", "/login");
    expect(screen.getByRole("link", { name: "Get Started" })).toHaveAttribute("href", "/register");
    expect(screen.queryByRole("button", { name: "Log out" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Library" })).not.toBeInTheDocument();
  });

  it("includes a search form that submits to /search with query parameter q", () => {
    renderNavbar(null);

    const input = screen.getByPlaceholderText("Search games, series or titles...");
    expect(input).toHaveAttribute("name", "q");
    expect(input.closest("form")).toHaveAttribute("action", "/search");
  });
});

describe("Navbar for a logged-in user", () => {
  it("shows the username, Library and Search links instead of Sign In", () => {
    renderNavbar(USER);

    expect(screen.getByText("@ali")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Library" })).toHaveAttribute("href", "/library");
    expect(screen.getByRole("link", { name: "Search" })).toHaveAttribute("href", "/search");
    expect(screen.queryByRole("link", { name: "Sign In" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Get Started" })).not.toBeInTheDocument();
  });

  it("calls the logout action from the Log out button", async () => {
    renderNavbar(USER);

    await userEvent.setup().click(screen.getByRole("button", { name: "Log out" }));

    await waitFor(() => expect(logoutAction).toHaveBeenCalledTimes(1));
  });
});
