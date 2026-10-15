import type { Metadata } from "next";
import Link from "next/link";

import AuthCard from "@/components/auth/AuthCard";
import LoginForm from "@/components/auth/LoginForm";

export const metadata: Metadata = {
  title: "Sign In | OmniLog",
};

export default function LoginPage() {
  return (
    <AuthCard
      title="Welcome back"
      description="Log in to your OmniLog library."
      footer={
        <>
          No account yet?{" "}
          <Link
            href="/register"
            className="font-medium text-horizon-cyan underline-offset-4 hover:underline hover:text-cyan-300 transition-colors"
          >
            Sign up
          </Link>
        </>
      }
    >
      <LoginForm />
    </AuthCard>
  );
}