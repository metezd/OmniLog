import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AccountPage from "@/app/account/page";
import LoginPage from "@/app/login/page";
import { getCurrentUser } from "@/lib/server/user";

vi.mock("@/lib/server/user", () => ({ getCurrentUser: vi.fn() }));
vi.mock("@/lib/server/warmup", () => ({ warmUpBackend: vi.fn() }));
vi.mock("next/server", () => ({ after: vi.fn(), connection: vi.fn(async () => undefined) }));
vi.mock("next/navigation", async () => await import("../../mocks/next-navigation"));
vi.mock("@/lib/actions/account", () => ({
  changePasswordAction: vi.fn(),
  deleteAccountAction: vi.fn(),
  logoutAllDevicesAction: vi.fn(),
}));
vi.mock("@/lib/actions/auth", () => ({ loginAction: vi.fn() }));

const userMock = vi.mocked(getCurrentUser);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("AccountPage (#426)", () => {
  it("shows who is logged in and the three sections", async () => {
    userMock.mockResolvedValue({ id: 1, username: "sam", email: "sam@example.com", created_at: "2026-11-27T10:00:00Z" });

    render(await AccountPage());

    expect(screen.getByText("Signed in as @sam (sam@example.com)")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Change password" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Log out on all devices" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Delete account" })).toBeInTheDocument();
  });

  it("sends a visitor without a login to the login page", async () => {
    userMock.mockResolvedValue(null);

    await expect(AccountPage()).rejects.toMatchObject({ url: "/login" });
  });
});

describe("LoginPage notices after the account page (#426)", () => {
  it.each([
    [{ deleted: "1" }, "Your account and all its data were deleted."],
    [{ loggedOut: "all" }, "You were logged out on all devices."],
  ])("shows a notice for %o", async (params, text) => {
    render(await LoginPage({ searchParams: Promise.resolve(params) }));

    expect(screen.getByText(text)).toBeInTheDocument();
  });

  it("shows no notice without a parameter", async () => {
    render(await LoginPage({ searchParams: Promise.resolve({}) }));

    expect(screen.queryByText(/were deleted|all devices/)).not.toBeInTheDocument();
  });
});
