import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "OmniLog",
  description: "Track series and games, chapter by chapter.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-[#05010a] text-white min-h-screen selection:bg-purple-500 selection:text-white`}>
        <Navbar />
        <main className="w-full min-h-screen">{children}</main>
      </body>
    </html>
  );
}