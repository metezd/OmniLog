// Links of the main navigation for a logged-in user (docs/analysis/ui/screen-list.md, section 4).
// A screen adds its link here when its page exists, so the navigation never points to a 404.
export const USER_NAV_LINKS = [
  { href: "/library", label: "Library" },
  { href: "/search", label: "Search" },
  { href: "/friends", label: "Friends" },
] as const;