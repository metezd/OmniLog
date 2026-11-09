"use client";

import { useActionState } from "react";

import AuthBanner from "@/components/auth/AuthBanner";
import AuthField from "@/components/auth/AuthField";
import { loginAction } from "@/lib/actions/auth";

interface LoginFormProps {
  /** True when the user comes from a registration whose automatic login failed. */
  registered?: boolean;
}

export default function LoginForm({ registered = false }: LoginFormProps) {
  const [state, formAction, pending] = useActionState(loginAction, undefined);

  return (
    // noValidate: the backend is the only judge of the data, and its messages are shown here
    <form action={formAction} noValidate className="space-y-4">
      {registered && !state && <AuthBanner variant="success">Your account was created. Please sign in.</AuthBanner>}
      {state?.message && <AuthBanner variant="error">{state.message}</AuthBanner>}

      <AuthField
        name="username"
        label="Username or Email"
        placeholder="Enter your username or email..."
        autoComplete="username"
        defaultValue={state?.values?.username}
        error={state?.fieldErrors?.username}
      />

      <AuthField
        name="password"
        type="password"
        label="Password"
        placeholder="••••••••"
        autoComplete="current-password"
        error={state?.fieldErrors?.password}
        labelAside={
          <a href="#" className="text-[11px] text-horizon-cyan hover:underline">
            Forgot?
          </a>
        }
      />

      <button
        type="submit"
        disabled={pending}
        className="w-full py-2.5 rounded-xl bg-horizon-crimson/30 hover:bg-horizon-crimson/50 border border-horizon-crimson/60 text-white font-medium text-xs transition-all shadow-[0_0_20px_rgba(229,29,36,0.3)] active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {pending ? "Signing in..." : "Sign In"}
      </button>
    </form>
  );
}
