import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import AuthBanner from "@/components/auth/AuthBanner";

describe("AuthBanner", () => {
  it("announces an error at once", () => {
    render(<AuthBanner variant="error">Invalid credentials</AuthBanner>);

    expect(screen.getByRole("alert")).toHaveTextContent("Invalid credentials");
  });

  it("announces a success note politely, without interrupting", () => {
    render(<AuthBanner variant="success">Your account was created.</AuthBanner>);

    expect(screen.getByRole("status")).toHaveTextContent("Your account was created.");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("announces an info note politely too", () => {
    render(<AuthBanner variant="info">Your session has ended.</AuthBanner>);

    expect(screen.getByRole("status")).toHaveTextContent("Your session has ended.");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
