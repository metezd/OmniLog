export interface Friend {
  id: string;
  username: string;
  displayName: string;
  avatarUrl: string;
  status: "online" | "offline" | "in_game";
  activityText?: string;
  isPending?: boolean;
}

export interface ActivityComment {
  id: string;
  authorName: string;
  authorAvatar: string;
  text: string;
  timestamp: string;
}

export interface FriendActivity {
  id: string;
  friendId: string;
  friendName: string;
  friendUsername: string;
  friendAvatar: string;
  mediaTitle: string;
  mediaType: "game" | "movie" | "tv";
  mediaImage: string;
  actionType: "rated" | "reviewed" | "completed" | "watched_episode";
  episodeDetails?: string;
  rating?: number;
  commentText?: string;
  likesCount: number;
  hasLiked?: boolean;
  comments: ActivityComment[];
  timestamp: string;
}