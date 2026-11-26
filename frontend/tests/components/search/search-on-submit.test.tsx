import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import Navbar from "@/components/layout/Navbar";
import AtmosphericHero from "@/components/layout/dashboard/AtmosphericHero";
import { SearchProvider } from "@/context/SearchContext";
import type { CurrentUser } from "@/types/api";

// #250 asked for a 350 to 400 ms debounce on the search inputs, so that typing does not send a
// request for every key. The search boxes of OmniLog send nothing while the user types: a search
// starts only when the form is sent (Enter or the Search button). These tests keep it that way, so
// a debounce is not needed. A live search added later must come with its own debounce.

const USER: CurrentUser = { id: 7, email: "ali@example.com", username: "ali", created_at: "2026-10-01T10:00:00Z" };

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: vi.fn() }),
}));
vi.mock("@/lib/actions/auth", () => ({ logoutAction: vi.fn() }));

let fetchSpy: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  pushMock.mockReset();
  fetchSpy = vi.spyOn(globalThis, "fetch");
});

afterEach(() => {
  fetchSpy.mockRestore();
});

describe("the search box of the navigation bar", () => {
  it("sends no request while the user types", async () => {
    const user = userEvent.setup();
    render(
      <SearchProvider>
        <Navbar user={null} />
      </SearchProvider>,
    );

    await user.type(screen.getByPlaceholderText("Search games, series or titles..."), "the witcher 3");

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(pushMock).not.toHaveBeenCalled();
  });
});

describe("the search box of the home page", () => {
  it("sends no request while the user types, and one navigation on Enter", async () => {
    const user = userEvent.setup();
    // The search box of the home page is shown to a logged-in user
    render(<AtmosphericHero user={USER} entries={[]} />);
    const input = screen.getByLabelText("Search catalog");

    await user.type(input, "hades");

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(pushMock).not.toHaveBeenCalled();

    await user.type(input, "{Enter}");

    expect(pushMock).toHaveBeenCalledTimes(1);
    expect(pushMock).toHaveBeenCalledWith("/search?q=hades");
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
