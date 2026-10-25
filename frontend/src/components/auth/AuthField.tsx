import { useId, type ReactNode } from "react";

interface AuthFieldProps {
  name: string;
  label: string;
  type?: "text" | "email" | "password";
  placeholder?: string;
  autoComplete?: string;
  /** The text that the user typed before. The password is never given back. */
  defaultValue?: string;
  /** The message of the backend for this field. */
  error?: string;
  /** Something next to the label, for example a link. */
  labelAside?: ReactNode;
}

const INPUT_CLASS =
  "w-full rounded-xl bg-black/40 border border-white/10 px-3.5 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-horizon-cyan focus:outline-none focus:ring-1 focus:ring-horizon-cyan transition-all aria-[invalid=true]:border-rose-500/60";

/** A labelled input for the login and registration forms. It shows the message of the backend. */
export default function AuthField({
  name,
  label,
  type = "text",
  placeholder,
  autoComplete,
  defaultValue,
  error,
  labelAside,
}: AuthFieldProps) {
  const id = useId();
  const errorId = `${id}-error`;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label htmlFor={id} className="text-xs font-medium text-slate-300">
          {label}
        </label>
        {labelAside}
      </div>
      <input
        id={id}
        name={name}
        type={type}
        placeholder={placeholder}
        autoComplete={autoComplete}
        defaultValue={defaultValue}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={INPUT_CLASS}
      />
      {error && (
        <p id={errorId} role="alert" className="text-[11px] text-rose-300">
          {error}
        </p>
      )}
    </div>
  );
}
