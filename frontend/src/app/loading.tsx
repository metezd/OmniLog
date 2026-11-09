import LoadingState from "@/components/states/LoadingState";

// Shown by Next.js while a page of any route is loading.
export default function Loading() {
  return (
    <div className="relative z-10 mx-auto w-full max-w-4xl px-4 py-8 sm:px-8">
      <LoadingState />
    </div>
  );
}
