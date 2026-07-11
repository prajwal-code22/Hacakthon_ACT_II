// app/layout.tsx — Root layout

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Router — Intelligent LLM Routing",
  description:
    "An intelligent AI router that automatically selects the most efficient model " +
    "(Local LLM or Cloud LLM) for every user request based on prompt complexity, " +
    "intent, and reasoning requirements.",
  keywords: ["AI", "LLM", "routing", "Gemma", "Fireworks", "local AI", "cloud AI"],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="antialiased min-h-screen">{children}</body>
    </html>
  );
}
