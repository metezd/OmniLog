"use client";

import { useEffect } from "react";

import ErrorState from "@/components/states/ErrorState";
import RetryButton from "@/components/states/RetryButton";

// The last safety net for an error that a page did not handle itself. Pages that call the backend
// catch BackendError and show their own state (see lib/server/error-state.ts), because an error
// from a Server Component loses its details on the way here.
export default function GlobalRouteError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="relative z-10 mx-auto w-full max-w-4xl px-4 py-16 sm:px-8">
      <ErrorState
        kind="error"
        message="An unexpected error happened. Please try again."
        action={<RetryButton onRetry={retry} />}
      />
    </div>
  );
}
