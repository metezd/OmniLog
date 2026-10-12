import Link from "next/link";

const FOOTER_LINKS = [
  { href: "/library", label: "Library" },
  { href: "/search", label: "Search" },
  { href: "/dashboard", label: "Dashboard" },
] as const;

export default function Footer() {
  return (
    <footer className="border-t border-zinc-200 dark:border-zinc-800">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-zinc-600 sm:flex-row sm:items-center sm:justify-between sm:px-6 dark:text-zinc-400">
        <p>
          <span className="font-medium text-zinc-900 dark:text-zinc-50">
            OmniLog
          </span>{" "}
          &mdash; track series and games, chapter by chapter.
        </p>

        <ul className="flex items-center gap-4">
          {FOOTER_LINKS.map(({ href, label }) => (
            <li key={href}>
              <Link
                href={href}
                className="transition-colors hover:text-zinc-900 dark:hover:text-zinc-50"
              >
                {label}
              </Link>
            </li>
          ))}
          <li>
            <a
              href="https://github.com/metezd/OmniLog"
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-zinc-900 dark:hover:text-zinc-50"
            >
              GitHub
            </a>
          </li>
        </ul>
      </div>
    </footer>
  );
}