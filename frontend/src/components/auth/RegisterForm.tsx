"use client";

import { useActionState } from "react";

import AuthBanner from "@/components/auth/AuthBanner";
import AuthField from "@/components/auth/AuthField";
import { registerAction } from "@/lib/actions/auth";

export default function RegisterForm() {
  const [state, formAction, pending] = useActionState(registerAction, undefined);

  return (
    // noValidate: the backend is the only judge of the data, and its messages are shown here
    <form action={formAction} noValidate className="space-y-4">
      {state?.message && <AuthBanner variant="error">{state.message}</AuthBanner>}

      <AuthField
        name="username"
        label="Username"
        placeholder="johndoe"
        autoComplete="username"
        defaultValue={state?.values?.username}
        error={state?.fieldErrors?.username}
      />

      <AuthField
        name="email"
        type="email"
        label="Email address"
        placeholder="name@example.com"
        autoComplete="email"
        defaultValue={state?.values?.email}
        error={state?.fieldErrors?.email}
      />

      <AuthField
        name="password"
        type="password"
        label="Password"
        placeholder="••••••••"
        autoComplete="new-password"
        error={state?.fieldErrors?.password}
      />

      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-xl bg-horizon-crimson/20 border border-horizon-crimson/40 py-2.5 text-sm font-medium text-rose-200 hover:bg-horizon-crimson/30 hover:border-horizon-crimson hover:text-white transition-all shadow-[0_0_15px_rgba(229,29,36,0.25)] active:scale-95 mt-2 disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {pending ? "Creating account..." : "Create Account"}
      </button>
    </form>
  );
}
