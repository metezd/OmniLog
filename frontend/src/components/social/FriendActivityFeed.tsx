"use client";

import { useEffect, useState } from "react";

import { addComment, getActivities, toggleLike } from "@/lib/services/social";
import type { FriendActivity } from "@/types/social";

interface FriendActivityFeedProps {
  onOpenAddFriend: () => void;
  // Change this value to reload the feed, for example after the friend list changed.
  refreshKey?: number;
}

export default function FriendActivityFeed({
  onOpenAddFriend,
  refreshKey = 0,
}: FriendActivityFeedProps) {
  const [activities, setActivities] = useState<FriendActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeCommentBox, setActiveCommentBox] = useState<string | null>(null);
  const [newCommentInput, setNewCommentInput] = useState("");

  useEffect(() => {
    let cancelled = false;
    getActivities().then((data) => {
      if (cancelled) return;
      setActivities(data);
      setIsLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const reload = async () => setActivities(await getActivities());

  const handleLike = async (id: string) => {
    await toggleLike(id);
    await reload();
  };

  const handleAddComment = async (activityId: string) => {
    if (!newCommentInput.trim()) return;
    await addComment(activityId, newCommentInput);
    setNewCommentInput("");
    await reload();
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

      {isLoading && (
        <p className="text-xs text-slate-400">Loading activity...</p>
      )}

      {!isLoading && activities.length === 0 && (
        <div className="liquid-glass rounded-2xl border border-white/10 p-8 text-center text-sm text-slate-400">
          No activity yet. Add friends to see what they are watching, playing
          and rating.
        </div>
      )}

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
                      {item.actionType === "reviewed" && "📝 Reviewed"}
                    </span>
                    <span>•</span>
                    <span>{item.timestamp}</span>
                  </p>
                </div>
              </div>

              {item.rating !== undefined && (
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
                  <div
                    key={c.id}
                    className="flex items-start gap-2 text-xs bg-white/5 p-2.5 rounded-xl"
                  >
                    <img
                      src={c.authorAvatar}
                      alt={c.authorName}
                      className="w-5 h-5 rounded-full object-cover"
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200">
                          {c.authorName}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          {c.timestamp}
                        </span>
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
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleAddComment(item.id);
                  }}
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