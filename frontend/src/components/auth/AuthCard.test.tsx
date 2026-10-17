import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import AuthCard from "./AuthCard";

describe("AuthCard", () => {
  it("renders title, description, and children", () => {
    render(
      <AuthCard
        title="Welcome back"
        description="Sign in to continue"
      >
        <button type="button">Sign in</button>
      </AuthCard>,
    );

    expect(
      screen.getByRole("heading", { name: "Welcome back" }),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Sign in to continue"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Sign in" }),
    ).toBeInTheDocument();
  });

  it("renders the optional footer", () => {
    render(
      <AuthCard
        title="Create account"
        description="Register a new account"
        footer={<a href="/login">Already have an account?</a>}
      >
        <form aria-label="Registration form" />
      </AuthCard>,
    );

    expect(
      screen.getByRole("link", {
        name: "Already have an account?",
      }),
    ).toHaveAttribute("href", "/login");
  });

  it("does not render a footer when it is not provided", () => {
    render(
      <AuthCard
        title="Login"
        description="Enter your credentials"
      >
        <form aria-label="Login form" />
      </AuthCard>,
    );

    expect(
      screen.queryByRole("link"),
    ).not.toBeInTheDocument();
  });
});