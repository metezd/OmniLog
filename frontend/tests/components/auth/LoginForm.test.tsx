import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import LoginForm from "@/components/auth/LoginForm";
import { loginAction, type AuthFormState } from "@/lib/actions/auth";
import { fillField, setupUser, type FillMode } from "../../helpers/forms";

// The real action talks to the backend. A form test only needs to control its answer.
vi.mock("@/lib/actions/auth", () => ({ loginAction: vi.fn(), registerAction: vi.fn() }));

const login = vi.mocked(loginAction);

// The values are pasted, because most tests only look at what the form sends. One test types.
async function fillAndSubmit(username: string, password: string, mode: FillMode = "paste") {
  const user = setupUser();
  if (username) await fillField(user, "Username or Email", username, mode);
  if (password) await fillField(user, "Password", password, mode);
  await user.click(screen.getByRole("button", { name: /sign in/i }));
}

describe("LoginForm", () => {
  it("shows the two fields, the Forgot? link and the button", () => {
    render(<LoginForm />);

    expect(screen.getByLabelText("Username or Email")).toHaveAttribute("name", "username");
    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "password");
    expect(screen.getByRole("link", { name: "Forgot?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign In" })).toBeEnabled();
  });

  it("sends what the user typed to the action, under the names that the backend uses", async () => {
    login.mockResolvedValue(undefined);
    render(<LoginForm />);

    await fillAndSubmit("ali@example.com", "StrongPass123!", "type");

    await waitFor(() => expect(login).toHaveBeenCalledTimes(1));
    const [, formData] = login.mock.calls[0];
    expect(Object.fromEntries(formData as FormData)).toEqual({
      username: "ali@example.com",
      password: "StrongPass123!",
    });
  });

  it("does not stop an empty form in the browser, because the backend judges the data", async () => {
    login.mockResolvedValue({ values: { username: "" }, fieldErrors: { username: "String should have at least 1 character" } });
    render(<LoginForm />);

    await fillAndSubmit("", "");

    expect(await screen.findByText("String should have at least 1 character")).toBeInTheDocument();
    expect(login).toHaveBeenCalledTimes(1);
  });

  it("shows the message of the whole form and keeps the username, but not the password", async () => {
    login.mockResolvedValue({ values: { username: "ali" }, message: "Invalid credentials" } satisfies AuthFormState);
    render(<LoginForm />);

    await fillAndSubmit("ali", "wrong-password");

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid credentials");
    expect(screen.getByLabelText("Username or Email")).toHaveValue("ali");
    expect(screen.getByLabelText("Password")).toHaveValue("");
  });

  it("shows the message of a field next to that field", async () => {
    login.mockResolvedValue({ values: { username: "ali" }, fieldErrors: { password: "Field required" } });
    render(<LoginForm />);

    await fillAndSubmit("ali", "");

    const password = await screen.findByLabelText("Password");
    await waitFor(() => expect(password).toHaveAccessibleDescription("Field required"));
    expect(screen.getByLabelText("Username or Email")).not.toHaveAttribute("aria-invalid");
  });

  it("disables the button and says so while the action works", async () => {
    let finish: (state: AuthFormState) => void = () => {};
    login.mockImplementation(() => new Promise<AuthFormState>((resolve) => (finish = resolve)));
    render(<LoginForm />);

    await fillAndSubmit("ali", "StrongPass123!");

    const waiting = await screen.findByRole("button", { name: "Signing in..." });
    expect(waiting).toBeDisabled();

    finish({ values: { username: "ali" }, message: "Invalid credentials" });
    expect(await screen.findByRole("button", { name: "Sign In" })).toBeEnabled();
  });

  it("tells a user who comes from a registration to sign in", () => {
    render(<LoginForm registered />);

    expect(screen.getByRole("status")).toHaveTextContent("Your account was created. Please sign in.");
  });

  it("does not show that note otherwise", () => {
    render(<LoginForm />);

    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("replaces the note with the error after a failed attempt", async () => {
    login.mockResolvedValue({ values: { username: "ali" }, message: "Invalid credentials" });
    render(<LoginForm registered />);

    await fillAndSubmit("ali", "wrong");

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid credentials");
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
