import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
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
  // Read on every request, so the navigation shows the right links after a login or a logout
  const user = await getCurrentUser();

  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen flex flex-col relative overflow-x-hidden`}
      >
        <SearchProvider>
          {/* Horizon Ambient Light Glow */}
          <div
            aria-hidden="true"
            className="pointer-events-none fixed -top-32 left-1/2 -translate-x-1/2 w-[1100px] h-[340px] bg-horizon-glow opacity-25 blur-[130px] rounded-full z-0"
          />

          {/* Navigation */}
          <header className="relative z-50">
            <Navbar user={user} />
          </header>

          {/* Main Content */}
          <main className="relative z-10 flex-1">{children}</main>

          {/* Footer */}
          <footer className="relative z-10">
            <Footer />
          </footer>
        </SearchProvider>
      </body>
    </html>
  );
}