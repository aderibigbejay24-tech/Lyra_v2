import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Lyra Lead Guardian — Fornest Automotive Demo",
  description:
    "Interactive prototype of the Lyra Lead Guardian pipeline for Fornest Automotive. Click through 12 scenes to experience the full lead → approval → booking flow.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={inter.className}>{children}</body>
    </html>
  );
}
