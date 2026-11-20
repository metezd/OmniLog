import AtmosphericHero from "@/components/layout/dashboard/AtmosphericHero";
import { getLibrary } from "@/lib/server/library";
import { getCurrentUser } from "@/lib/server/user";
import type { LibraryEntry } from "@/types/api";

export default async function Home() {
  const user = await getCurrentUser();
  let entries: LibraryEntry[] = [];

  if (user) {
    try {
      entries = await getLibrary();
    } catch (error) {
      const digest = (error as { digest?: unknown } | null)?.digest;
      if (typeof digest === "string" && digest.startsWith("NEXT_REDIRECT")) {
        throw error;
      }
      entries = [];
    }
  }

  return (
    <div className="relative min-h-[calc(100vh-4rem)] w-full bg-transparent">
      <AtmosphericHero user={user} entries={entries} />
    </div>
  );
}
