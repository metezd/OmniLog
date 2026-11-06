import type { CatalogItem, MediaKind } from "@/types/media";

// Mock catalog service. Replace each function body with an Axios call
// (see src/lib/api.ts) once the backend catalog endpoints are wired up:
//   searchCatalog -> GET /catalog/search?q=...&kind=...
//   library calls -> /library endpoints

const delay = (ms = 250) =>
  new Promise<void>((resolve) => setTimeout(resolve, ms));

const CATALOG: CatalogItem[] = [
  {
    id: "tv-arcane",
    title: "Arcane",
    kind: "tv",
    source: "TMDB",
    year: 2021,
    rating: 9.4,
    summary:
      "Two sisters from the rival cities of Piltover and Zaun are pulled apart by war and by the invention of a dangerous new technology.",
    genres: ["Animation", "Sci-Fi", "Drama"],
    length: "2 seasons • 18 episodes",
    imageUrl:
      "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600",
  },
  {
    id: "tv-severance",
    title: "Severance",
    kind: "tv",
    source: "TMDB",
    year: 2022,
    rating: 8.7,
    summary:
      "Employees at Lumon Industries have their work and personal memories surgically separated, until one of them starts asking questions.",
    genres: ["Thriller", "Sci-Fi", "Mystery"],
    length: "2 seasons • 19 episodes",
    imageUrl:
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600",
  },
  {
    id: "tv-breaking-bad",
    title: "Breaking Bad",
    kind: "tv",
    source: "TMDB",
    year: 2008,
    rating: 9.5,
    summary:
      "A high school chemistry teacher diagnosed with cancer turns to manufacturing drugs to secure his family's future.",
    genres: ["Crime", "Drama", "Thriller"],
    length: "5 seasons • 62 episodes",
    imageUrl: null,
  },
  {
    id: "tv-last-of-us",
    title: "The Last of Us",
    kind: "tv",
    source: "TMDB",
    year: 2023,
    rating: 8.6,
    summary:
      "Twenty years after civilization collapsed, a hardened survivor escorts a teenage girl across a ruined United States.",
    genres: ["Drama", "Horror", "Adventure"],
    length: "2 seasons • 16 episodes",
    imageUrl: null,
  },
  {
    id: "game-cyberpunk",
    title: "Cyberpunk 2077",
    kind: "game",
    source: "IGDB",
    year: 2020,
    rating: 8.6,
    summary:
      "An open-world action RPG set in Night City, where a mercenary chases a one-of-a-kind implant that holds the key to immortality.",
    genres: ["RPG", "Action", "Open World"],
    length: "~25h main story • Phantom Liberty DLC",
    imageUrl:
      "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=600",
  },
  {
    id: "game-elden-ring",
    title: "Elden Ring",
    kind: "game",
    source: "IGDB",
    year: 2022,
    rating: 9.5,
    summary:
      "Rise, Tarnished, and venture into the Lands Between to claim the Elden Ring in a vast world built with George R. R. Martin.",
    genres: ["RPG", "Action", "Souls-like"],
    length: "~60h main story • Shadow of the Erdtree DLC",
    imageUrl:
      "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=600",
  },
  {
    id: "game-baldurs-gate-3",
    title: "Baldur's Gate 3",
    kind: "game",
    source: "IGDB",
    year: 2023,
    rating: 9.6,
    summary:
      "Gather your party and return to the Forgotten Realms in a tale of fellowship, betrayal and the lure of absolute power.",
    genres: ["RPG", "Turn-Based", "Fantasy"],
    length: "3 acts • ~75h main story",
    imageUrl: null,
  },
  {
    id: "game-witcher-3",
    title: "The Witcher 3: Wild Hunt",
    kind: "game",
    source: "IGDB",
    year: 2015,
    rating: 9.3,
    summary:
      "A monster hunter searches for his adopted daughter while a spectral army known as the Wild Hunt closes in.",
    genres: ["RPG", "Open World", "Fantasy"],
    length: "~50h main story • 2 expansions",
    imageUrl: null,
  },
  {
    id: "game-disco-elysium",
    title: "Disco Elysium",
    kind: "game",
    source: "IGDB",
    year: 2019,
    rating: 9.1,
    summary:
      "A detective with a shattered memory solves a murder in a decaying city, where every skill is a voice in your head.",
    genres: ["RPG", "Narrative", "Detective"],
    length: "~25h main story",
    imageUrl: null,
  },
  {
    id: "game-hades",
    title: "Hades",
    kind: "game",
    source: "IGDB",
    year: 2020,
    rating: 9.0,
    summary:
      "Battle out of the Underworld as the immortal son of Hades, growing stronger with every escape attempt.",
    genres: ["Roguelike", "Action", "Mythology"],
    length: "~22h to first escape",
    imageUrl: null,
  },
];

export interface SearchOptions {
  query: string;
  kind?: MediaKind | "all";
}

export async function searchCatalog({
  query,
  kind = "all",
}: SearchOptions): Promise<CatalogItem[]> {
  await delay();
  const q = query.trim().toLowerCase();

  return CATALOG.filter((item) => {
    if (kind !== "all" && item.kind !== kind) return false;
    if (!q) return true;
    return (
      item.title.toLowerCase().includes(q) ||
      item.genres.some((g) => g.toLowerCase().includes(q))
    );
  })
    .sort((a, b) => b.rating - a.rating)
    .map((item) => ({ ...item, genres: [...item.genres] }));
}

// In-memory library. Resets on page reload.
let libraryIds = new Set<string>();

export async function getLibraryIds(): Promise<string[]> {
  return Array.from(libraryIds);
}

export async function addToLibrary(id: string): Promise<void> {
  libraryIds = new Set(libraryIds).add(id);
}

export async function removeFromLibrary(id: string): Promise<void> {
  const next = new Set(libraryIds);
  next.delete(id);
  libraryIds = next;
}