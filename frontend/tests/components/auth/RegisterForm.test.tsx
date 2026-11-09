import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import RegisterForm from "@/components/auth/RegisterForm";
import { registerAction, type AuthFormState } from "@/lib/actions/auth";
import { fillField, setupUser, type FillMode } from "../../helpers/forms";

vi.mock("@/lib/actions/auth", () => ({ loginAction: vi.fn(), registerAction: vi.fn() }));

const register = vi.mocked(registerAction);

// The values are pasted, because most tests only look at what the form sends. One test types.
async function fillAndSubmit(
  values: { username?: string; email?: string; password?: string },
  mode: FillMode = "paste",
) {
  const user = setupUser();
  if (values.username) await fillField(user, "Username", values.username, mode);
  if (values.email) await fillField(user, "Email address", values.email, mode);
  if (values.password) await fillField(user, "Password", values.password, mode);
  await user.click(screen.getByRole("button", { name: /create account/i }));
}

describe("RegisterForm", () => {
  it("shows the three fields with the right input types and the button", () => {
    render(<RegisterForm />);

    expect(screen.getByLabelText("Username")).toHaveAttribute("type", "text");
    expect(screen.getByLabelText("Email address")).toHaveAttribute("type", "email");
    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "password");
    expect(screen.getByRole("button", { name: "Create Account" })).toBeEnabled();
  });

  it("sends the three values to the action, under the names that the backend uses", async () => {
    register.mockResolvedValue(undefined);
    render(<RegisterForm />);

    await fillAndSubmit({ username: "ali", email: "ali@example.com", password: "StrongPass123!" }, "type");

    await waitFor(() => expect(register).toHaveBeenCalledTimes(1));
    expect(Object.fromEntries(register.mock.calls[0][1] as FormData)).toEqual({
      username: "ali",
      email: "ali@example.com",
      password: "StrongPass123!",
    });
  });

  it("lets the backend judge an email that the browser would call wrong", async () => {
    register.mockResolvedValue({
      values: { username: "ali", email: "not-an-email" },
      fieldErrors: { email: "value is not a valid email address" },
    });
    render(<RegisterForm />);

    await fillAndSubmit({ username: "ali", email: "not-an-email", password: "StrongPass123!" });

    expect(await screen.findByText("value is not a valid email address")).toBeInTheDocument();
    expect(register).toHaveBeenCalledTimes(1);
  });

  it("shows the message of each rejected field next to it and keeps the username and the email", async () => {
    register.mockResolvedValue({
      values: { username: "a@b", email: "a@b.com" },
      fieldErrors: { username: "must not contain @", password: "String should have at least 8 characters" },
    });
    render(<RegisterForm />);

    await fillAndSubmit({ username: "a@b", email: "a@b.com", password: "x" });

    await waitFor(() => expect(screen.getByLabelText("Username")).toHaveAccessibleDescription("must not contain @"));
    expect(screen.getByLabelText("Password")).toHaveAccessibleDescription("String should have at least 8 characters");
    expect(screen.getByLabelText("Email address")).not.toHaveAttribute("aria-invalid");
    expect(screen.getByLabelText("Username")).toHaveValue("a@b");
    expect(screen.getByLabelText("Email address")).toHaveValue("a@b.com");
    expect(screen.getByLabelText("Password")).toHaveValue("");
  });

  it("shows one message for the whole form when the account exists", async () => {
    register.mockResolvedValue({
      values: { username: "ali", email: "ali@example.com" },
      message: "Username or email is already registered",
    } satisfies AuthFormState);
    render(<RegisterForm />);

    await fillAndSubmit({ username: "ali", email: "ali@example.com", password: "StrongPass123!" });

    expect(await screen.findByRole("alert")).toHaveTextContent("Username or email is already registered");
  });

  it("disables the button and says so while the action works", async () => {
    let finish: (state: AuthFormState) => void = () => {};
    register.mockImplementation(() => new Promise<AuthFormState>((resolve) => (finish = resolve)));
    render(<RegisterForm />);

    await fillAndSubmit({ username: "ali", email: "ali@example.com", password: "StrongPass123!" });

    expect(await screen.findByRole("button", { name: "Creating account..." })).toBeDisabled();

    finish({ message: "Username or email is already registered" });
    expect(await screen.findByRole("button", { name: "Create Account" })).toBeEnabled();
  });
});
