import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AccountForms from "@/components/account/AccountForms";
import { changePasswordAction, deleteAccountAction } from "@/lib/actions/account";

vi.mock("@/lib/actions/account", () => ({
  changePasswordAction: vi.fn(),
  deleteAccountAction: vi.fn(),
  logoutAllDevicesAction: vi.fn(),
}));

const changeMock = vi.mocked(changePasswordAction);
const deleteMock = vi.mocked(deleteAccountAction);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("AccountForms (#426)", () => {
  it("sends the three password fields and shows the saved message", async () => {
    changeMock.mockResolvedValue({ status: "saved", message: "Your password was changed." });
    const user = userEvent.setup();
    render(<AccountForms />);

    await user.type(screen.getByLabelText("Current password"), "Old-Pass-2026!");
    await user.type(screen.getByLabelText("New password"), "New-Pass-2026!");
    await user.type(screen.getByLabelText("New password again"), "New-Pass-2026!");
    await user.click(screen.getByRole("button", { name: "Change password" }));

    await waitFor(() => expect(changeMock).toHaveBeenCalledTimes(1));
    const [, formData] = changeMock.mock.calls[0];
    expect(Object.fromEntries(formData as FormData)).toEqual({
      current_password: "Old-Pass-2026!",
      new_password: "New-Pass-2026!",
      confirm_password: "New-Pass-2026!",
    });
    expect(await screen.findByText("Your password was changed.")).toBeInTheDocument();
  });

  it("shows the message of a field and of the whole form", async () => {
    changeMock.mockResolvedValue({ status: "error", fieldErrors: { current_password: "The password is not correct." } });
    deleteMock.mockResolvedValue({ status: "error", message: "The server cannot be reached." });
    const user = userEvent.setup();
    render(<AccountForms />);

    await user.click(screen.getByRole("button", { name: "Change password" }));
    await user.click(screen.getByRole("button", { name: "Delete my account" }));

    expect(await screen.findByText("The password is not correct.")).toBeInTheDocument();
    expect(await screen.findByText("The server cannot be reached.")).toBeInTheDocument();
  });

  it("sends the password and the confirmation when the account is deleted", async () => {
    deleteMock.mockResolvedValue({ status: "error", fieldErrors: { confirm: "Type DELETE to confirm." } });
    const user = userEvent.setup();
    render(<AccountForms />);

    await user.type(screen.getByLabelText("Password"), "Pass-2026!");
    await user.type(screen.getByLabelText("Type DELETE to confirm"), "delete");
    await user.click(screen.getByRole("button", { name: "Delete my account" }));

    await waitFor(() => expect(deleteMock).toHaveBeenCalledTimes(1));
    const [, formData] = deleteMock.mock.calls[0];
    expect(Object.fromEntries(formData as FormData)).toEqual({ password: "Pass-2026!", confirm: "delete" });
    expect(await screen.findAllByText("Type DELETE to confirm.")).not.toHaveLength(0);
  });

  it("has a form for logging out on all devices", () => {
    render(<AccountForms />);

    expect(screen.getByRole("button", { name: "Log out everywhere" })).toBeInTheDocument();
  });
});
