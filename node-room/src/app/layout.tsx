import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Hybrid Dialogue",
  description: "A shared conversation room with Claude as a quiet facilitator.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
