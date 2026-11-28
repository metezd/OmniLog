import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ReviewSection from "@/components/title/ReviewSection";
import { deleteReviewAction, submitReviewAction, type ReviewActionState } from "@/lib/actions/library";
import type { Review } from "@/types/api";

vi.mock("@/lib/actions/library", () => ({
  submitReviewAction: vi.fn(),
  deleteReviewAction: vi.fn(),
}));
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));

const mockedSubmit = vi.mocked(submitReviewAction);
const mockedDelete = vi.mocked(deleteReviewAction);

function makeReview(overrides: Partial<Review> = {}): Review {
  return {
    id: 1,
    library_entry_id: 10,
    text: "Memorable narrative and atmosphere.",
    contains_spoiler: false,
    spoiler_score: 0.08,
    spoiler_model_version: "omnilog-nlp-spoiler-v1",
    created_at: "2026-11-20T12:00:00Z",
    updated_at: null,
    ...overrides,
  };
}

describe("ReviewSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("displays the review text box and Save button when no review exists yet", () => {
    render(<ReviewSection entryId={10} mediaItemId={42} initialReview={null} />);

    expect(screen.getByLabelText("Review text")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: "Edit Review" })).not.toBeInTheDocument();
  });

  it("submits the review with entryId and text and displays the saved review", async () => {
    const saved = makeReview({ text: "Loved the opening chapter." });
    mockedSubmit.mockResolvedValueOnce({ status: "saved", review: saved });

    const user = userEvent.setup();
    render(<ReviewSection entryId={10} mediaItemId={42} initialReview={null} />);

    await user.type(screen.getByLabelText("Review text"), "Loved the opening chapter.");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(mockedSubmit).toHaveBeenCalledTimes(1);
      expect(screen.getByText("Loved the opening chapter.")).toBeInTheDocument();
    });

    const [, formData] = mockedSubmit.mock.calls[0];
    expect(Object.fromEntries(formData as FormData)).toEqual({
      entryId: "10",
      mediaItemId: "42",
      text: "Loved the opening chapter.",
    });
    expect(screen.getByText(/Review saved\./)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Edit Review" })).toBeInTheDocument();
  });

  it("shows a spoiler warning and blurs text only when contains_spoiler is true", async () => {
    const spoilerReview = makeReview({
      text: "The villain was the narrator all along.",
      contains_spoiler: true,
      spoiler_score: 0.92,
    });

    const user = userEvent.setup();
    render(<ReviewSection entryId={10} mediaItemId={42} initialReview={spoilerReview} />);

    expect(screen.getByText(/Spoiler Warning/i)).toBeInTheDocument();
    expect(screen.getByText(/92% confidence/)).toBeInTheDocument();

    const reviewText = screen.getByText("The villain was the narrator all along.");
    expect(reviewText).toHaveClass("blur-sm");

    await user.click(screen.getByRole("button", { name: "Reveal Spoiler" }));
    expect(reviewText).not.toHaveClass("blur-sm");
    expect(screen.getByRole("button", { name: "Hide Spoiler" })).toBeInTheDocument();
  });

  it("does not show a spoiler warning when contains_spoiler is false", () => {
    render(
      <ReviewSection
        entryId={10}
        mediaItemId={42}
        initialReview={makeReview({ contains_spoiler: false })}
      />,
    );

    expect(screen.queryByText(/Spoiler Warning/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Spoiler-Free/)).toBeInTheDocument();
    expect(screen.getByText("Memorable narrative and atmosphere.")).not.toHaveClass("blur-sm");
  });

  it("does not show a spoiler warning or claim spoiler-free when contains_spoiler is null", () => {
    render(
      <ReviewSection
        entryId={10}
        mediaItemId={42}
        initialReview={makeReview({
          contains_spoiler: null,
          spoiler_score: null,
          spoiler_model_version: null,
        })}
      />,
    );

    expect(screen.queryByText(/Spoiler Warning/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Spoiler-Free/i)).not.toBeInTheDocument();
    expect(screen.getByText("Spoiler check not completed")).toBeInTheDocument();
    expect(screen.getByText("Memorable narrative and atmosphere.")).not.toHaveClass("blur-sm");
  });

  it("communicates saved status without a spoiler warning when AI check returned null on save", async () => {
    mockedSubmit.mockResolvedValueOnce({
      status: "saved",
      review: makeReview({
        text: "Saved without AI check.",
        contains_spoiler: null,
        spoiler_score: null,
        spoiler_model_version: null,
      }),
    });

    const user = userEvent.setup();
    render(<ReviewSection entryId={10} mediaItemId={42} initialReview={null} />);

    await user.type(screen.getByLabelText("Review text"), "Saved without AI check.");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(screen.getByText("Saved without AI check.")).toBeInTheDocument();
    });
    expect(screen.getByText(/Review saved\. Spoiler check could not be completed yet\./)).toBeInTheDocument();
    expect(screen.queryByText(/Spoiler Warning/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Spoiler-Free/i)).not.toBeInTheDocument();
  });

  it("prevents empty or whitespace-only submissions client-side and shows a validation message", async () => {
    const user = userEvent.setup();
    render(<ReviewSection entryId={10} mediaItemId={42} initialReview={null} />);

    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Review text cannot be empty.");
    expect(mockedSubmit).not.toHaveBeenCalled();

    await user.type(screen.getByLabelText("Review text"), "   ");
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Review text cannot be empty.");
    expect(mockedSubmit).not.toHaveBeenCalled();
  });

  it("displays a 422 validation error from the backend while keeping the user's draft", async () => {
    mockedSubmit.mockResolvedValueOnce({
      status: "error",
      code: "validation",
      message: "Review text cannot be blank",
    });

    const user = userEvent.setup();
    render(<ReviewSection entryId={10} mediaItemId={42} initialReview={null} />);

    await user.type(screen.getByLabelText("Review text"), "Draft text");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Review text cannot be blank");
    });
    expect(screen.getByLabelText("Review text")).toHaveValue("Draft text");
  });

  it("shows a not_found ErrorState when the backend returns 404", async () => {
    mockedSubmit.mockResolvedValueOnce({
      status: "error",
      code: "not_found",
      message: "This title or library entry could not be found.",
    });

    const user = userEvent.setup();
    render(<ReviewSection entryId={999} mediaItemId={42} initialReview={null} />);

    await user.type(screen.getByLabelText("Review text"), "A review");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Not found");
      expect(screen.getByRole("alert")).toHaveTextContent(
        "This title or library entry could not be found.",
      );
    });
    expect(screen.getByRole("link", { name: "Go to library" })).toHaveAttribute("href", "/library");
  });

  it("handles a 503 response accurately without losing the user's draft", async () => {
    mockedSubmit.mockResolvedValueOnce({
      status: "error",
      code: "unavailable",
      message:
        "The AI moderation service is unavailable right now. Your review was not saved. Please try again.",
    });

    const user = userEvent.setup();
    render(<ReviewSection entryId={10} mediaItemId={42} initialReview={null} />);

    await user.type(screen.getByLabelText("Review text"), "My unsaved review");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "The AI moderation service is unavailable right now. Your review was not saved. Please try again.",
      );
    });
    expect(screen.getByLabelText("Review text")).toHaveValue("My unsaved review");
    expect(screen.queryByText(/Review saved/i)).not.toBeInTheDocument();
  });

  it("supports editing and cancelling/saving an existing review (#150)", async () => {
    const initial = makeReview({ text: "First version." });
    const updated = makeReview({ text: "Second revised version.", updated_at: "2026-11-21T10:00:00Z" });
    mockedSubmit.mockResolvedValueOnce({ status: "saved", review: updated });

    const user = userEvent.setup();
    render(<ReviewSection entryId={10} mediaItemId={42} initialReview={initial} />);

    // Saved review is shown in view mode first
    expect(screen.getByText("First version.")).toBeInTheDocument();
    expect(screen.queryByLabelText("Review text")).not.toBeInTheDocument();

    // Enter edit mode and cancel without saving
    await user.click(screen.getByRole("button", { name: "Edit Review" }));
    const textarea = screen.getByLabelText("Review text");
    expect(textarea).toHaveValue("First version.");
    await user.clear(textarea);
    await user.type(textarea, "Abandoned edit");
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(screen.getByText("First version.")).toBeInTheDocument();
    expect(mockedSubmit).not.toHaveBeenCalled();

    // Enter edit mode again and save updated review
    await user.click(screen.getByRole("button", { name: "Edit Review" }));
    const editArea = screen.getByLabelText("Review text");
    await user.clear(editArea);
    await user.type(editArea, "Second revised version.");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(screen.getByText("Second revised version.")).toBeInTheDocument();
    });
    expect(screen.queryByLabelText("Review text")).not.toBeInTheDocument();
    expect(screen.getByText(/Review saved\./)).toBeInTheDocument();
  });

  it("disables Save while submission is pending", async () => {
    let finish: (state: ReviewActionState) => void = () => {};
    mockedSubmit.mockImplementation(
      () => new Promise<ReviewActionState>((resolve) => (finish = resolve)),
    );

    const user = userEvent.setup();
    render(<ReviewSection entryId={10} mediaItemId={42} initialReview={null} />);

    await user.type(screen.getByLabelText("Review text"), "Pending test");
    await user.click(screen.getByRole("button", { name: "Save" }));

    const pendingButton = await screen.findByRole("button", { name: "Saving…" });
    expect(pendingButton).toBeDisabled();

    finish({ status: "saved", review: makeReview({ text: "Pending test" }) });
    await waitFor(() => {
      expect(screen.getByText("Pending test")).toBeInTheDocument();
    });
  });
});

describe("ReviewSection: delete the review (#427)", () => {
  it("asks for a confirmation, deletes the review and shows the empty form again", async () => {
    mockedDelete.mockResolvedValueOnce({ status: "idle", review: null });
    const user = userEvent.setup();
    render(<ReviewSection entryId={10} mediaItemId={42} initialReview={makeReview()} />);

    await user.click(screen.getByRole("button", { name: "Delete Review" }));
    await user.click(screen.getByRole("button", { name: "Confirm delete" }));

    await waitFor(() => expect(mockedDelete).toHaveBeenCalledTimes(1));
    const [, formData] = mockedDelete.mock.calls[0];
    expect(Object.fromEntries(formData as FormData)).toEqual({ entryId: "10", mediaItemId: "42", intent: "delete" });
    expect(await screen.findByLabelText("Review text")).toHaveValue("");
    expect(screen.queryByText("Memorable narrative and atmosphere.")).not.toBeInTheDocument();
  });

  it("keeps the review when the user does not confirm", async () => {
    const user = userEvent.setup();
    render(<ReviewSection entryId={10} mediaItemId={42} initialReview={makeReview()} />);

    await user.click(screen.getByRole("button", { name: "Delete Review" }));
    await user.click(screen.getByRole("button", { name: "Keep it" }));

    expect(mockedDelete).not.toHaveBeenCalled();
    expect(screen.getByText("Memorable narrative and atmosphere.")).toBeInTheDocument();
  });
});

