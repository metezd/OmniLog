"use client";

import { useEffect, useState } from "react";

import {
  getFriends,
  removeFriend,
  sendFriendRequest,
} from "@/lib/services/social";
import type { Friend } from "@/types/social";

interface AddFriendModalProps {
  isOpen: boolean;
  onClose: () => void;
  // Called after the friend list changed (friend added or removed).
  onChange?: () => void;
}

export default function AddFriendModal({
  isOpen,
  onClose,
  onChange,
}: AddFriendModalProps) {
  const [searchUsername, setSearchUsername] = useState("");
  const [friendsList, setFriendsList] = useState<Friend[]>([]);
  const [feedback, setFeedback] = useState<{ ok: boolean; message: string } | null>(null);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    getFriends().then((data) => {
      if (!cancelled) setFriendsList(data);
    });
    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSendRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchUsername.trim() || isSending) return;

    setIsSending(true);
    const result = await sendFriendRequest(searchUsername);
    setFeedback(result);
    setIsSending(false);
    setTimeout(() => setFeedback(null), 3000);

    if (result.ok) {
      setSearchUsername("");
      setFriendsList(await getFriends());
      onChange?.();
    }
  };

  const handleRemove = async (friendId: string) => {
    await removeFriend(friendId);
    setFriendsList(await getFriends());
    onChange?.();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4">
      <div className="liquid-glass w-full max-w-md rounded-2xl p-6 border border-white/15 space-y-5 relative">
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white text-sm"
        >
          ✕
        </button>

        <div>
          <h3 className="text-lg font-bold text-white">Friend Directory</h3>
          <p className="text-xs text-slate-400">
            Search users by @username to share ratings & comments
          </p>
        </div>

        <form onSubmit={handleSendRequest} className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={searchUsername}
              onChange={(e) => setSearchUsername(e.target.value)}
              placeholder="Enter @username..."
              className="flex-1 rounded-xl bg-black/50 border border-white/10 px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-horizon-cyan"
            />
            <button
              type="submit"
              disabled={isSending}
              className="px-4 py-2 bg-horizon-crimson/20 border border-horizon-crimson/40 text-rose-200 hover:bg-horizon-crimson/30 rounded-xl text-xs font-medium transition-all disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isSending ? "Adding..." : "Add Friend"}
            </button>
          </div>
          {feedback && (
            <p
              role="status"
              className={`text-xs font-medium ${
                feedback.ok ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {feedback.ok ? "✓ " : ""}
              {feedback.message}
            </p>
          )}
        </form>

        <div className="space-y-3 pt-2">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Your Friends ({friendsList.length})
          </h4>

          <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
            {friendsList.length === 0 && (
              <p className="text-xs text-slate-500">
                No friends yet. Try adding mert_d or selin_a.
              </p>
            )}
            {friendsList.map((f) => (
              <div
                key={f.id}
                className="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-white/5 border border-white/5"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="relative shrink-0">
                    <img
                      src={f.avatarUrl}
                      alt={f.displayName}
                      className="w-8 h-8 rounded-full object-cover"
                    />
                    <span
                      className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-black ${
                        f.status === "online"
                          ? "bg-emerald-400"
                          : f.status === "in_game"
                          ? "bg-purple-400"
                          : "bg-slate-500"
                      }`}
                    />
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-white truncate">
                      {f.displayName}
                    </p>
                    <p className="text-[10px] text-slate-400">@{f.username}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[10px] text-slate-400 bg-white/5 px-2 py-1 rounded-md border border-white/10">
                    {f.isPending ? "Pending" : f.activityText}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleRemove(f.id)}
                    className="text-[10px] text-slate-500 hover:text-rose-400 transition-colors"
                    title={`Remove ${f.displayName}`}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}