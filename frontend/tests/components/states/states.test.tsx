import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import EmptyState from "@/components/states/EmptyState";
import ErrorState from "@/components/states/ErrorState";
import LoadingState from "@/components/states/LoadingState";
import RetryButton from "@/components/states/RetryButton";

const { refresh } = vi.hoisted(() => ({ refresh: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));

describe("ErrorState", () => {
  it("announces an unavailable service as an alert with a retry button", () => {
    render(<ErrorState kind="unavailable" message="The data service is not available right now." />);

    expect(screen.getByRole("alert")).toHaveTextContent("Service unavailable");
    expect(screen.getByRole("alert")).toHaveTextContent("The data service is not available right now.");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("offers a link back to the library for a missing page, and no retry", () => {
    render(<ErrorState kind="not_found" />);

    expect(screen.getByRole("alert")).toHaveTextContent("Not found");
    expect(screen.getByRole("link", { name: "Go to library" })).toHaveAttribute("href", "/library");
    expect(screen.queryByRole("button", { name: "Try again" })).not.toBeInTheDocument();
  });

  it("shows a generic title for any other error", () => {
    render(<ErrorState kind="error" />);

    expect(screen.getByRole("alert")).toHaveTextContent("Something went wrong");
  });

  it("lets the caller change the title and the action", () => {
    render(<ErrorState kind="not_found" title="Page not found" action={<span>Custom action</span>} />);

    expect(screen.getByRole("alert")).toHaveTextContent("Page not found");
    expect(screen.getByText("Custom action")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Go to library" })).not.toBeInTheDocument();
  });
});

describe("RetryButton", () => {
  it("loads the page again from the server by default", async () => {
    render(<RetryButton />);

    await userEvent.setup().click(screen.getByRole("button", { name: "Try again" }));

    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("calls the function that it was given instead, for an error boundary", async () => {
    const onRetry = vi.fn();
    render(<RetryButton onRetry={onRetry} />);

    await userEvent.setup().click(screen.getByRole("button", { name: "Try again" }));

    expect(onRetry).toHaveBeenCalledTimes(1);
    expect(refresh).not.toHaveBeenCalled();
  });
});

describe("EmptyState", () => {
  it("shows the title and the message politely, as a status", () => {
    render(<EmptyState title="Your library is empty" message="Titles that you add will show up here." />);

    expect(screen.getByRole("status")).toHaveTextContent("Your library is empty");
    expect(screen.getByRole("status")).toHaveTextContent("Titles that you add will show up here.");
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("shows the link when there is one", () => {
    render(<EmptyState title="Nothing here" action={{ href: "/search", label: "Find a title" }} />);

    expect(screen.getByRole("link", { name: "Find a title" })).toHaveAttribute("href", "/search");
  });
});

describe("LoadingState", () => {
  it("shows the default label, and a given one", () => {
    const { rerender } = render(<LoadingState />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading...");

    rerender(<LoadingState label="Loading your library..." />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading your library...");
  });
});
