"use client";

import { useState } from "react";

import AddFriendModal from "@/components/social/AddFriendModal";
import FriendActivityFeed from "@/components/social/FriendActivityFeed";

export default function FriendsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  // Bumped whenever the friend list changes so the feed reloads.
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="relative z-10 mx-auto w-full max-w-4xl px-4 py-8 sm:px-8">
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