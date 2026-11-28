"use client";

import { useActionState } from "react";

import AuthBanner from "@/components/auth/AuthBanner";
import AuthField from "@/components/auth/AuthField";
import {
  type AccountFormState,
  changePasswordAction,
  deleteAccountAction,
  logoutAllDevicesAction,
} from "@/lib/actions/account";

const IDLE: AccountFormState = { status: "idle" };
const BUTTON =
  "rounded-xl border px-4 py-2 text-sm font-medium transition-all active:scale-95 disabled:cursor-not-allowed disabled:opacity-60";

function errorsOf(state: AccountFormState): Record<string, string> {
  return state.status === "error" ? (state.fieldErrors ?? {}) : {};
}

/** Change the password, log out on all devices, delete the account (#426). */
export default function AccountForms() {
  const [passwordState, passwordAction, passwordPending] = useActionState(changePasswordAction, IDLE);
  const [deleteState, deleteAction, deletePending] = useActionState(deleteAccountAction, IDLE);
  const passwordErrors = errorsOf(passwordState);
  const deleteErrors = errorsOf(deleteState);

  return (
    <div className="space-y-6">
      <section aria-labelledby="change-password" className="liquid-glass space-y-4 rounded-2xl border border-white/10 p-6">
        <h2 id="change-password" className="text-sm font-semibold text-white">
          Change password
        </h2>
        <form action={passwordAction} noValidate className="space-y-3">
          {passwordState.status === "saved" && <AuthBanner variant="info">{passwordState.message}</AuthBanner>}
          {passwordState.status === "error" && passwordState.message && (
            <AuthBanner variant="error">{passwordState.message}</AuthBanner>
          )}
          <AuthField
            name="current_password"
            type="password"
            label="Current password"
            autoComplete="current-password"
            error={passwordErrors.current_password}
          />
          <AuthField
            name="new_password"
            type="password"
            label="New password"
            autoComplete="new-password"
            error={passwordErrors.new_password}
          />
          <AuthField
            name="confirm_password"
            type="password"
            label="New password again"
            autoComplete="new-password"
            error={passwordErrors.confirm_password}
          />
          <p className="text-[11px] text-slate-400">
            Your other devices are logged out when the password changes.
          </p>
          <button
            type="submit"
            disabled={passwordPending}
            className={`${BUTTON} border-white/15 bg-white/10 text-slate-200 hover:bg-white/20`}
          >
            {passwordPending ? "Saving..." : "Change password"}
          </button>
        </form>
      </section>

      <section aria-labelledby="all-devices" className="liquid-glass space-y-3 rounded-2xl border border-white/10 p-6">
        <h2 id="all-devices" className="text-sm font-semibold text-white">
          Log out on all devices
        </h2>
        <p className="text-xs text-slate-400">
          Ends every session of your account, on this device too. Use it after you lost a device or used a shared computer.
        </p>
        <form action={logoutAllDevicesAction}>
          <button type="submit" className={`${BUTTON} border-white/15 bg-white/10 text-slate-200 hover:bg-white/20`}>
            Log out everywhere
          </button>
        </form>
      </section>

      <section aria-labelledby="delete-account" className="liquid-glass space-y-4 rounded-2xl border border-rose-500/30 p-6">
        <h2 id="delete-account" className="text-sm font-semibold text-rose-200">
          Delete account
        </h2>
        <p className="text-xs text-slate-400">
          Deletes your account with your library, lists, diary, chapter progress and reviews. This cannot be undone.
        </p>
        <form action={deleteAction} noValidate className="space-y-3">
          {deleteState.status === "error" && deleteState.message && (
            <AuthBanner variant="error">{deleteState.message}</AuthBanner>
          )}
          <AuthField name="password" type="password" label="Password" autoComplete="current-password" error={deleteErrors.password} />
          <AuthField name="confirm" label="Type DELETE to confirm" autoComplete="off" error={deleteErrors.confirm} />
          <button
            type="submit"
            disabled={deletePending}
            className={`${BUTTON} border-rose-400/40 bg-rose-500/20 text-rose-100 hover:bg-rose-500/30`}
          >
            {deletePending ? "Deleting..." : "Delete my account"}
          </button>
        </form>
      </section>
    </div>
  );
}
