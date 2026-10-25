import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import AuthField from "@/components/auth/AuthField";

describe("AuthField", () => {
  it("connects the label to the input", () => {
    render(<AuthField name="username" label="Username" />);

    const input = screen.getByLabelText("Username");
    expect(input).toHaveAttribute("name", "username");
    expect(input).toHaveAttribute("type", "text");
  });

  it("passes the type, the placeholder, the autocomplete hint and the earlier text to the input", () => {
    render(
      <AuthField
        name="email"
        type="email"
        label="Email"
        placeholder="name@example.com"
        autoComplete="email"
        defaultValue="ali@example.com"
      />,
    );

    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("type", "email");
    expect(input).toHaveAttribute("placeholder", "name@example.com");
    expect(input).toHaveAttribute("autocomplete", "email");
    expect(input).toHaveValue("ali@example.com");
  });

  it("shows no error and does not mark the input as invalid when there is no error", () => {
    render(<AuthField name="username" label="Username" />);

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Username")).not.toHaveAttribute("aria-invalid");
    expect(screen.getByLabelText("Username")).not.toHaveAttribute("aria-describedby");
  });

  it("shows the message, announces it and ties it to the input", () => {
    render(<AuthField name="password" label="Password" error="String should have at least 8 characters" />);

    const input = screen.getByLabelText("Password");
    const message = screen.getByRole("alert");
    expect(message).toHaveTextContent("String should have at least 8 characters");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("String should have at least 8 characters");
  });

  it("shows the extra element next to the label", () => {
    render(<AuthField name="password" label="Password" labelAside={<a href="#">Forgot?</a>} />);

    expect(screen.getByRole("link", { name: "Forgot?" })).toBeInTheDocument();
  });

  it("gives two fields on one page different ids", () => {
    render(
      <>
        <AuthField name="a" label="First" />
        <AuthField name="b" label="Second" />
      </>,
    );

    expect(screen.getByLabelText("First").id).not.toBe(screen.getByLabelText("Second").id);
  });
});
