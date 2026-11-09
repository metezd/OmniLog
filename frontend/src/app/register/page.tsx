import type { Metadata } from "next";
import Link from "next/link";

import AuthCard from "@/components/auth/AuthCard";
import RegisterForm from "@/components/auth/RegisterForm";

export const metadata: Metadata = {
  title: "Create Account | OmniLog",
};

export default function RegisterPage() {
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