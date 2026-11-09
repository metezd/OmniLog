import { LoaderCircle } from "lucide-react";

interface LoadingStateProps {
  label?: string;
}

/** Shown while a page loads (S-15). The label is read aloud by screen readers. */
export default function LoadingState({ label = "Loading..." }: LoadingStateProps) {
  return (
    <div role="status" className="flex flex-col items-center justify-center gap-3 py-16 text-slate-400">
      <LoaderCircle className="h-7 w-7 animate-spin text-cyan-400" aria-hidden="true" />
      <span className="text-xs">{label}</span>
    </div>
  );
}
