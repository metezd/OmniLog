import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Footer from "@/components/layout/Footer";

describe("Footer", () => {
  it("links to real application routes and never links to the removed /dashboard route", () => {
    render(<Footer />);

    expect(screen.getByRole("link", { name: "Library" })).toHaveAttribute("href", "/library");
    expect(screen.getByRole("link", { name: "Search" })).toHaveAttribute("href", "/search");
    expect(screen.getByRole("link", { name: "Lists" })).toHaveAttribute("href", "/lists");
    expect(screen.getByRole("link", { name: "Diary" })).toHaveAttribute("href", "/diary");
    expect(screen.getByRole("link", { name: "Stats" })).toHaveAttribute("href", "/stats");
    expect(screen.queryByRole("link", { name: "Dashboard" })).not.toBeInTheDocument();
  });
});
