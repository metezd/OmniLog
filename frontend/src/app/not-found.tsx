import ErrorState from "@/components/states/ErrorState";

export default function NotFound() {
  return (
    <div className="relative z-10 mx-auto w-full max-w-4xl px-4 py-16 sm:px-8">
      <ErrorState kind="not_found" title="Page not found" message="This page does not exist or was moved." />
    </div>
  );
}
