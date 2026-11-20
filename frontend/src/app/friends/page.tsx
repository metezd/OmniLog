"use client";

import { useState } from "react";

import AddFriendModal from "@/components/social/AddFriendModal";
import FriendActivityFeed from "@/components/social/FriendActivityFeed";

export default function FriendsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  // Bumped whenever the friend list changes so the feed reloads.
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="relative z-10 mx-auto w-full max-w-4xl space-y-4 px-4 py-8 sm:px-8">
      <div
        role="status"
        className="liquid-glass flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-amber-400/30 bg-amber-500/10 px-4 py-2.5 text-xs text-amber-100"
      >
        <span>
          <strong className="font-semibold text-amber-200">Demo Preview:</strong>{" "}
          The social friend feed uses in-memory sample data and resets on reload.
        </span>
        <span className="rounded-full border border-amber-400/40 bg-amber-500/20 px-2.5 py-0.5 font-mono text-[10px] tracking-wider text-amber-200 uppercase">
          UI Demo
        </span>
      </div>

      <FriendActivityFeed
        onOpenAddFriend={() => setIsModalOpen(true)}
        refreshKey={refreshKey}
      />
      <AddFriendModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onChange={() => setRefreshKey((key) => key + 1)}
      />
    </div>
  );
}