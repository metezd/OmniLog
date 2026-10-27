// The answers of the FastAPI backend, as they arrive (snake_case). They follow backend/app/schemas.
// Dates are ISO 8601 strings.

export type MediaType = "GAME" | "SERIES" | "MOVIE";
export type WatchStatus = "PLAN_TO_WATCH" | "IN_PROGRESS" | "COMPLETED" | "DROPPED";
export type ChapterKind = "EPISODE" | "CHAPTER";

export interface CurrentUser {
  id: number;
  email: string;
  username: string;
  created_at: string;
}

// ---- Catalog and library
export interface MediaItem {
  id: number;
  title: string;
  media_type: MediaType;
  poster_url: string | null;
  release_date: string | null;
  external_api_id: number | null;
  genres: string[]; // sorted by name. Empty until the title details were opened once.
}

export interface DecisionOption {
  id: number;
  label: string; // such as "A". recordDecision() takes this value as `choice`.
  text: string | null;
}

export interface DecisionPoint {
  id: number;
  position: number;
  prompt: string;
  options: DecisionOption[]; // sorted by label
}

export interface Chapter {
  id: number;
  number: number;
  kind: ChapterKind;
  title: string | null;
  release_date: string | null;
  runtime_minutes: number | null;
  decision_points: DecisionPoint[]; // empty for a chapter without a decision
}

export interface Season {
  id: number;
  season_number: number; // 0 is used for specials
  title: string | null;
  air_date: string | null;
  episodes: Chapter[];
}

export interface MediaDetail extends MediaItem {
  description: string | null;
  seasons: Season[];
  chapters: Chapter[];
}

export interface LibraryEntry {
  id: number;
  user_id: number;
  media_item_id: number;
  status: WatchStatus;
  rating: number | null; // 1 to 10
  updated_at: string | null;
  media_item: MediaItem;
}

// ---- Episodic logging
export interface ChapterRating {
  library_entry_id: number;
  chapter_id: number;
  rating: number; // 1 to 5
  updated_at: string;
}

export interface PlaytimeLog {
  id: number;
  chapter_id: number;
  minutes: number;
  logged_at: string;
  playtime_minutes: number; // total of all entries of the chapter
}

export interface DecisionItem {
  decision_point_id: number;
  choice: string;
  decided_at: string;
}

export interface Decision extends DecisionItem {
  library_entry_id: number;
  chapter_id: number;
}

export interface ChapterProgress {
  library_entry_id: number;
  chapter_id: number;
  rating: number | null;
  playtime_minutes: number;
  updated_at: string | null;
  choice: string | null;
  decided_at: string | null;
  decisions: DecisionItem[];
}

// ---- Journal
export interface CustomListItem {
  id: number;
  list_id: number;
  media_item_id: number;
  added_at: string;
}

export interface CustomList {
  id: number;
  name: string;
  created_at: string;
  items: CustomListItem[];
}

export interface DiaryEntry {
  id: number;
  action: string;
  media_item_id: number | null; // empty for events that are not about a title
  details: string | null;
  created_at: string;
}
