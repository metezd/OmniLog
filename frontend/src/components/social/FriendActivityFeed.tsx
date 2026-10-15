"use client";

import React, { useState } from "react";
import { FriendActivity } from "../../types/social";

const MOCK_ACTIVITIES: FriendActivity[] = [
  {
    id: "act-1",
    friendId: "u-101",
    friendName: "Aylin Yılmaz",
    friendUsername: "aylin_y",
    friendAvatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
    mediaTitle: "Arcane: Season 2",
    mediaType: "tv",
    mediaImage: "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600",
    actionType: "watched_episode",
    episodeDetails: "Season 2 • Episode 6: 'The Beast Within'",
    rating: 9.8,
    commentText: "Bölümün sonundaki sahne inanılmazdı! Görsel efektler ve müzik uyumu diziyi bambaşka bir seviyeye taşıyor.",
    likesCount: 12,
    hasLiked: false,
    timestamp: "2 hours ago",
    comments: [
      {
        id: "c-1",
        authorName: "Mert",
        authorAvatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150",
        text: "Kesinlikle katılıyorum, 2. sezonun en iyi bölümüydü!",
        timestamp: "1 hour ago",
      },
    ],
  },
  {
    id: "act-2",
    friendId: "u-102",
    friendName: "Caner K.",
    friendUsername: "canerk",
    friendAvatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
    mediaTitle: "Cyberpunk 2077",
    mediaType: "game",
    mediaImage: "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=600",
    actionType: "completed",
    episodeDetails: "Phantom Liberty Expansion • All Endings Unlocked",
    rating: 9.5,
    commentText: "Dogtown hikayesi ana oyundan bile daha sürükleyiciydi. Reed ve Songbird karakter yazımları harika.",
    likesCount: 24,
    hasLiked: true,
    timestamp: "5 hours ago",
    comments: [],
  },
];

interface FriendActivityFeedProps {
  onOpenAddFriend: () => void;
}

export default function FriendActivityFeed({ onOpenAddFriend }: FriendActivityFeedProps) {
  const [activities, setActivities] = useState<FriendActivity[]>(MOCK_ACTIVITIES);
  const [activeCommentBox, setActiveCommentBox] = useState<string | null>(null);
  const [newCommentInput, setNewCommentInput] = useState<string>("");

  const handleLike = (id: string) => {
    setActivities((prev) =>
      prev.map((item) =>
        item.id === id
          ? {
              ...item,
              hasLiked: !item.hasLiked,
              likesCount: item.hasLiked ? item.likesCount - 1 : item.likesCount + 1,
            }
          : item
      )
    );
  };

  const handleAddComment = (activityId: string) => {
    if (!newCommentInput.trim()) return;

    setActivities((prev) =>
      prev.map((item) =>
        item.id === activityId
          ? {
              ...item,
              comments: [
                ...item.comments,
                {
                  id: `c-${Date.now()}`,
                  authorName: "You",
                  authorAvatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
                  text: newCommentInput,
                  timestamp: "Just now",
                },
              ],
            }
          : item
      )
    );
    setNewCommentInput("");
  };

  return (
    <section className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>Social Activity & Friend Reviews</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-horizon-cyan/20 border border-horizon-cyan/40 text-cyan-300">
              Live Feed
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            See what your friends are watching, playing, and rating
          </p>
        </div>

        <button
          type="button"
          onClick={onOpenAddFriend}
          className="rounded-xl bg-white/10 hover:bg-white/15 border border-white/15 px-3.5 py-2 text-xs font-medium text-slate-200 hover:text-white transition-all flex items-center gap-2 active:scale-95"
        >
          <span>👥 Manage Friends</span>
        </button>
      </div>

      <div className="space-y-6">
        {activities.map((item) => (
          <div
            key={item.id}
            className="liquid-glass rounded-2xl p-5 border border-white/10 hover:border-white/20 transition-all space-y-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <img
                  src={item.friendAvatar}
                  alt={item.friendName}
                  className="w-10 h-10 rounded-full border border-white/20 object-cover"
                />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white">
                      {item.friendName}
                    </span>
                    <span className="text-xs text-slate-400">
                      @{item.friendUsername}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                    <span className="text-horizon-cyan font-medium">
                      {item.actionType === "watched_episode" && "📺 Watched an Episode"}
                      {item.actionType === "completed" && "🏆 Completed"}
                      {item.actionType === "rated" && "⭐ Rated"}
                    </span>
                    <span>•</span>
                    <span>{item.timestamp}</span>
                  </p>
                </div>
              </div>

              {item.rating && (
                <div className="flex items-center gap-1 bg-amber-500/10 border border-amber-500/30 px-2.5 py-1 rounded-xl text-amber-300 font-bold text-xs">
                  <span>★</span>
                  <span>{item.rating} / 10</span>
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-4 bg-black/40 rounded-xl p-3 border border-white/5">
              <img
                src={item.mediaImage}
                alt={item.mediaTitle}
                className="w-full sm:w-28 h-20 rounded-lg object-cover border border-white/10"
              />
              <div className="flex-1 space-y-1">
                <h4 className="font-bold text-white text-sm">{item.mediaTitle}</h4>
                {item.episodeDetails && (
                  <p className="text-xs text-slate-300 font-medium bg-white/5 inline-block px-2 py-0.5 rounded border border-white/10">
                    {item.episodeDetails}
                  </p>
                )}
                {item.commentText && (
                  <p className="text-xs text-slate-300 pt-1 italic">
                    &ldquo;{item.commentText}&rdquo;
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-400 pt-1">
              <button
                type="button"
                onClick={() => handleLike(item.id)}
                className={`flex items-center gap-1.5 transition-colors ${
                  item.hasLiked ? "text-rose-400 font-semibold" : "hover:text-white"
                }`}
              >
                <span>{item.hasLiked ? "❤️" : "🤍"}</span>
                <span>{item.likesCount} Likes</span>
              </button>

              <button
                type="button"
                onClick={() =>
                  setActiveCommentBox(activeCommentBox === item.id ? null : item.id)
                }
                className="hover:text-white transition-colors flex items-center gap-1.5"
              >
                <span>💬</span>
                <span>{item.comments.length} Comments</span>
              </button>
            </div>

            {item.comments.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-white/5">
                {item.comments.map((c) => (
                  <div key={c.id} className="flex items-start gap-2 text-xs bg-white/5 p-2.5 rounded-xl">
                    <img
                      src={c.authorAvatar}
                      alt={c.authorName}
                      className="w-5 h-5 rounded-full object-cover"
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200">{c.authorName}</span>
                        <span className="text-[10px] text-slate-500">{c.timestamp}</span>
                      </div>
                      <p className="text-slate-300 mt-0.5">{c.text}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeCommentBox === item.id && (
              <div className="flex gap-2 pt-2">
                <input
                  type="text"
                  value={newCommentInput}
                  onChange={(e) => setNewCommentInput(e.target.value)}
                  placeholder="Write a reply or thought..."
                  className="flex-1 rounded-xl bg-black/50 border border-white/10 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-horizon-cyan"
                />
                <button
                  type="button"
                  onClick={() => handleAddComment(item.id)}
                  className="px-3 py-1.5 bg-horizon-cyan/20 border border-horizon-cyan/40 text-cyan-200 text-xs rounded-xl hover:bg-horizon-cyan/30 transition-all font-medium"
                >
                  Send
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}