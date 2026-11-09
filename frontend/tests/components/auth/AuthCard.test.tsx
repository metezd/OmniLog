import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import AuthCard from "@/components/auth/AuthCard";

describe("AuthCard", () => {
  it("shows the title, the description and the content", () => {
    render(
      <AuthCard title="Sign in" description="Welcome back">
        <button>Go</button>
      </AuthCard>,
    );

    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByText("Welcome back")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Go" })).toBeInTheDocument();
  });

  it("shows the footer only when it is given", () => {
    const { rerender } = render(
      <AuthCard title="T" description="D">
        content
      </AuthCard>,
    );
    expect(screen.queryByText("Need an account?")).not.toBeInTheDocument();

    rerender(
      <AuthCard title="T" description="D" footer={<span>Need an account?</span>}>
        content
      </AuthCard>,
    );
    expect(screen.getByText("Need an account?")).toBeInTheDocument();
  });
});
