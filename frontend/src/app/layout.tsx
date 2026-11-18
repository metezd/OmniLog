import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import GlobalAsciiBackground from "@/components/layout/background/GlobalAsciiBackground";
import { SearchProvider } from "@/context/SearchContext";
import { getCurrentUser } from "@/lib/server/user";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "OmniLog | Media & Game Tracker",
  description: "Track movies, TV shows, and video games with a liquid glass aesthetic.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const user = await getCurrentUser();

  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen flex flex-col relative overflow-x-hidden bg-[#05070d]`}
      >
        <SearchProvider>
          {/* Navigation */}
          <header className="relative z-50">
            <Navbar user={user} />
          </header>

          {/* Global Persistent ASCII Creature Canvas (zIndex: 20) + Top Pill Switcher (zIndex: 40) */}
          <GlobalAsciiBackground />

          {/* Main Content (z-30 so interactive cards sit cleanly above the z-20 canvas) */}
          <main className="relative z-30 flex-1 bg-transparent">{children}</main>

          {/* Footer */}
          <footer className="relative z-30 bg-transparent">
            <Footer />
          </footer>
        </SearchProvider>
      </body>
    </html>
  );
}
