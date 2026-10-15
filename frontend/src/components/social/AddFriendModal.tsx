"use client";

import React, { useState } from "react";
import { Friend } from "../../types/social";

const INITIAL_FRIENDS: Friend[] = [
  {
    id: "u-1",
    username: "aylin_y",
    displayName: "Aylin Yılmaz",
    avatarUrl: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
    status: "online",
    activityText: "Watching Severance S1",
  },
  {
    id: "u-2",
    username: "canerk",
    displayName: "Caner K.",
    avatarUrl: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
    status: "in_game",
    activityText: "Playing Elden Ring",
  },
];

interface AddFriendModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AddFriendModal({ isOpen, onClose }: AddFriendModalProps) {
  const [searchUsername, setSearchUsername] = useState("");
  const [friendsList] = useState<Friend[]>(INITIAL_FRIENDS);
  const [sentMessage, setSentMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSendRequest = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchUsername.trim()) return;

    setSentMessage(`Friend request sent to @${searchUsername}`);
    setSearchUsername("");
    setTimeout(() => setSentMessage(null), 3000);
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
              className="px-4 py-2 bg-horizon-crimson/20 border border-horizon-crimson/40 text-rose-200 hover:bg-horizon-crimson/30 rounded-xl text-xs font-medium transition-all"
            >
              Add Friend
            </button>
          </div>
          {sentMessage && (
            <p className="text-xs text-emerald-400 font-medium">✓ {sentMessage}</p>
          )}
        </form>

        <div className="space-y-3 pt-2">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Your Friends ({friendsList.length})
          </h4>

          <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
            {friendsList.map((f) => (
              <div
                key={f.id}
                className="flex items-center justify-between p-2.5 rounded-xl bg-white/5 border border-white/5"
              >
                <div className="flex items-center gap-3">
                  <div className="relative">
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
                  <div>
                    <p className="text-xs font-bold text-white">{f.displayName}</p>
                    <p className="text-[10px] text-slate-400">@{f.username}</p>
                  </div>
                </div>
                <span className="text-[10px] text-slate-400 bg-white/5 px-2 py-1 rounded-md border border-white/10">
                  {f.activityText}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}