import type { Metadata } from "next";
import Link from "next/link";
import { after, connection } from "next/server";

import AuthCard from "@/components/auth/AuthCard";
import RegisterForm from "@/components/auth/RegisterForm";
import { warmUpBackend } from "@/lib/server/warmup";

export const metadata: Metadata = {
  title: "Create Account | OmniLog",
};

export default async function RegisterPage() {
  // Rendered for each request, so the ping runs when a user opens the page and not at build time.
  // It wakes a sleeping backend while the user types, after this page is sent (#250).
  await connection();
  after(() => {
    warmUpBackend();
  });

  return (
    <AuthCard
      title="Create an account"
      description="Start tracking your games and media in cinematic glass."
      footer={
        <>
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-medium text-horizon-cyan underline-offset-4 hover:underline hover:text-cyan-300 transition-colors"
          >
            Sign in
          </Link>
        </>
      }
    >
      <RegisterForm />
    </AuthCard>
  );
}