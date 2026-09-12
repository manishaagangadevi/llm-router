import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Router — one prompt, the right model",
  description: "A predictive multi-LLM router with compression, caching, and cost-aware routing.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-bg-0 text-text-primary">{children}</body>
    </html>
  );
}
