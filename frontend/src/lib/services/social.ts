import type { ActivityComment, Friend, FriendActivity } from "@/types/social";

// Mock social service. Data lives in memory and resets on page reload.
// Replace each function body with an Axios call (see src/lib/api.ts) once the
// backend exposes friend and activity endpoints.

const CURRENT_USER_AVATAR =
  "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150";

const delay = (ms = 120) =>
  new Promise<void>((resolve) => setTimeout(resolve, ms));

export interface SendRequestResult {
  ok: boolean;
  message: string;
}

let friends: Friend[] = [
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

// Users that can be found by username when adding a friend.
const directory: Friend[] = [
  {
    id: "u-3",
    username: "mert_d",
    displayName: "Mert Demir",
    avatarUrl: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150",
    status: "online",
    activityText: "Watching Severance S1",
  },
  {
    id: "u-4",
    username: "selin_a",
    displayName: "Selin Aksoy",
    avatarUrl: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
    status: "offline",
    activityText: "Finished Elden Ring DLC",
  },
];

// Newest first. Only activity from accepted friends is returned to the feed.
let activities: FriendActivity[] = [
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
    commentText:
      "Bölümün sonundaki sahne inanılmazdı! Görsel efektler ve müzik uyumu diziyi bambaşka bir seviyeye taşıyor.",
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
    commentText:
      "Dogtown hikayesi ana oyundan bile daha sürükleyiciydi. Reed ve Songbird karakter yazımları harika.",
    likesCount: 24,
    hasLiked: true,
    timestamp: "5 hours ago",
    comments: [],
  },
  {
    id: "act-3",
    friendId: "u-3",
    friendName: "Mert Demir",
    friendUsername: "mert_d",
    friendAvatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150",
    mediaTitle: "Severance",
    mediaType: "tv",
    mediaImage: "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600",
    actionType: "rated",
    rating: 9.5,
    commentText: "The season 1 finale still gives me chills.",
    likesCount: 7,
    hasLiked: false,
    timestamp: "1 day ago",
    comments: [],
  },
  {
    id: "act-4",
    friendId: "u-4",
    friendName: "Selin Aksoy",
    friendUsername: "selin_a",
    friendAvatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
    mediaTitle: "Elden Ring: Shadow of the Erdtree",
    mediaType: "game",
    mediaImage: "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=600",
    actionType: "reviewed",
    rating: 9.7,
    commentText: "Realm of Shadow is brutal but beautiful.",
    likesCount: 15,
    hasLiked: false,
    timestamp: "2 days ago",
    comments: [],
  },
];

const normalizeUsername = (raw: string) =>
  raw.trim().replace(/^@/, "").toLowerCase();

export async function getFriends(): Promise<Friend[]> {
  await delay();
  return friends.map((f) => ({ ...f }));
}

// The mock accepts requests instantly. With the real API a request starts as
// pending (isPending: true) until the other user accepts it.
export async function sendFriendRequest(
  rawUsername: string,
): Promise<SendRequestResult> {
  await delay();
  const username = normalizeUsername(rawUsername);

  if (!username) {
    return { ok: false, message: "Enter a username." };
  }
  if (friends.some((f) => f.username.toLowerCase() === username)) {
    return { ok: false, message: `@${username} is already in your friends.` };
  }
  const user = directory.find((u) => u.username.toLowerCase() === username);
  if (!user) {
    return { ok: false, message: `No user found with @${username}.` };
  }

  friends = [...friends, { ...user, isPending: false }];
  return { ok: true, message: `@${user.username} added to your friends.` };
}

export async function removeFriend(friendId: string): Promise<void> {
  friends = friends.filter((f) => f.id !== friendId);
}

export async function getActivities(): Promise<FriendActivity[]> {
  await delay();
  const visibleUsernames = new Set(
    friends.filter((f) => !f.isPending).map((f) => f.username.toLowerCase()),
  );
  return activities
    .filter((a) => visibleUsernames.has(a.friendUsername.toLowerCase()))
    .map((a) => ({ ...a, comments: [...a.comments] }));
}

export async function toggleLike(activityId: string): Promise<void> {
  activities = activities.map((a) =>
    a.id === activityId
      ? {
          ...a,
          hasLiked: !a.hasLiked,
          likesCount: a.hasLiked ? a.likesCount - 1 : a.likesCount + 1,
        }
      : a,
  );
}

export async function addComment(
  activityId: string,
  text: string,
): Promise<void> {
  const trimmed = text.trim();
  if (!trimmed) return;

  const comment: ActivityComment = {
    id: `c-${Date.now()}`,
    authorName: "You",
    authorAvatar: CURRENT_USER_AVATAR,
    text: trimmed,
    timestamp: "Just now",
  };

  activities = activities.map((a) =>
    a.id === activityId ? { ...a, comments: [...a.comments, comment] } : a,
  );
}   