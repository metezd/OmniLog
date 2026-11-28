import type { Metadata } from "next";
import { redirect } from "next/navigation";

import AccountForms from "@/components/account/AccountForms";
import { LOGIN_PATH } from "@/lib/auth/routes";
import { getCurrentUser } from "@/lib/server/user";

export const metadata: Metadata = {
  title: "Account | OmniLog",
};

export default async function AccountPage() {
  const user = await getCurrentUser();
  if (!user) redirect(LOGIN_PATH);

  return (
    <div className="relative z-10 mx-auto w-full max-w-2xl space-y-6 px-4 py-8 sm:px-8">
      <div className="border-b border-white/10 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-white">Account</h1>
        <p className="text-xs text-slate-400">
          Signed in as @{user.username} ({user.email})
        </p>
      </div>
      <AccountForms />
    </div>
  );
}
